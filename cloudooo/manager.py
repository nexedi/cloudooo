##############################################################################
#
# Copyright (c) 2009-2010 Nexedi SA and Contributors. All Rights Reserved.
#                    Gabriel M. Monnerat <gabriel@tiolive.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is free software: you can Use, Study, Modify and Redistribute
# it under the terms of the GNU General Public License version 3, or (at your
# option) any later version, as published by the Free Software Foundation.
#
# You can also Link and Combine this program with other software covered by
# the terms of any of the Free Software licenses or any of the Open Source
# Initiative approved licenses and Convey the resulting work. Corresponding
# source of such a combination shall include the source code for all other
# software used.
#
# This program is distributed WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See COPYING file for full licensing terms.
# See https://www.nexedi.com/licensing for rationale and options.
#
##############################################################################

import mimetypes
import xmlrpc
from mimetypes import guess_type, guess_extension
from binascii import a2b_base64
from base64 import encodebytes
from zope.interface import implementer
from .interfaces.manager import IManager, IERP5Compatibility
from cloudooo.util import logger, parseContentType
from cloudooo.interfaces.granulate import ITableGranulator
from cloudooo.interfaces.granulate import IImageGranulator
from cloudooo.interfaces.granulate import ITextGranulator
from fnmatch import fnmatch

#XXX Must be removed
from cloudooo.handler.ooo.granulator import OOGranulator
from cloudooo.handler.ooo.mimemapper import mimemapper
from cloudooo.handler.wkhtmltopdf.handler import Handler as WkhtmltopdfHandler

class HandlerNotFound(Exception):
  pass

def getHandlerClass(source_format, destination_format, mimetype_registry,
                    handler_dict):
  """Select handler according to source_format and destination_format
  """
  source_mimetype = mimetypes.types_map.get('.%s' % source_format, "*")
  destination_mimetype = mimetypes.types_map.get('.%s' % destination_format, "*")
  for pattern in mimetype_registry:
    registry_list = pattern.split()
    if fnmatch(source_mimetype, registry_list[0]) and \
        (fnmatch(destination_mimetype, registry_list[1]) or destination_format is None):
      return handler_dict[registry_list[2]]
  raise HandlerNotFound('No Handler found for %r=>%r' % (source_format,
                                                         destination_format))

def BBB_guess_type(url):
  base = url.split("/")[-1].lstrip(".")
  # if base.endswith(".ms.docx"): return ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "Microsoft Word 2007-2013 XML")
  split = base.split(".")
  ext = '' if len(split) == 1 else split[-1]
  return {
    "docy": ("application/x-asc-text", None),
    "xlsy": ("application/x-asc-spreadsheet", None),
    "ppty": ("application/x-asc-presentation", None),
  }.get(ext, None) or guess_type(url)

def BBB_guess_extension(mimetype, title=None):
  return {
    # title : extension
    "Flat XML ODF Text Document": ".fodt",
    "MET - OS/2 Metafile": ".met",
    "Microsoft Excel 2007-2013 XML": ".ms.xlsx",
    "Excel 2007–365": ".ms.xlsx",
    "Microsoft PowerPoint 2007-2013 XML": ".ms.pptx",
    "Microsoft PowerPoint 2007-2013 XML AutoPlay": ".ms.ppsx",
    "Microsoft Word 2007-2013 XML": ".ms.docx",
    "Word 2007": ".ms.docx",
  }.get(title, None) or {
    # mediatype : extension
    "application/msword": ".doc",
    "application/postscript": ".eps",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.ms-excel.sheet.macroenabled.12": ".xlsm",
    "application/vnd.ms-powerpoint": ".ppt",
    "text/html": ".html",
    "text/plain": ".txt",
    "image/jpeg": ".jpg",
  }.get(parseContentType(mimetype).get_content_type(), None) or guess_extension(mimetype)

@implementer(IManager, IERP5Compatibility, ITableGranulator, IImageGranulator,
             ITextGranulator)
class Manager(object):
  """Manipulates requisitons of client and temporary files in file system."""

  def __init__(self, path_tmp_dir, **kw):
    """Need pass the path where the temporary document will be created."""
    self._path_tmp_dir = path_tmp_dir
    self.kw = kw
    self.mimetype_registry = kw.pop("mimetype_registry")
    self.handler_dict = kw.pop("handler_dict")

  def _check_file_type(self, file):
    if isinstance(file, xmlrpc.client.Binary):
      raise TypeError('`file` must be provided as a string with the file content encoded as base64')

  def convertFile(self, file:str, source_format:str, destination_format:str, zip=False,
                  refresh=False, conversion_kw={}) -> str:
    """Returns the converted file in the given format.
    Keywords arguments:
      file -- File as string in base64
      source_format -- Format of original file as string
      destination_format -- Target format as string
      zip -- Boolean Attribute. If true, returns the file in the form of a
      zip archive
      refresh -- Obsolete and ignored
    """
    self._check_file_type(file)

    kw = self.kw.copy()
    kw.update(zip=zip)
    # XXX Force the use of wkhtmltopdf handler if converting from html to pdf
    #     with conversion parameters.
    #     This is a hack that quickly enables the use of wkhtmltopdf without
    #     conflicting with other "html to pdf" conversion method
    #     (i.e. using the ooo handler) that does not use such a parameter.
    #     This hack should be removed after defining and implementing a way to
    #     use the conversion_kw in a possible interoperable way between all
    #     "html to pdf" handlers.
    if (conversion_kw and
        source_format in ("html", "text/html") and
        destination_format in ("pdf", "application/pdf")):
      handler_class = WkhtmltopdfHandler
    else:
      handler_class = getHandlerClass(source_format,
                                    destination_format,
                                    self.mimetype_registry,
                                    self.handler_dict)
    handler = handler_class(self._path_tmp_dir,
                            a2b_base64(file),
                            source_format,
                            **kw)
    decode_data = handler.convert(destination_format, **conversion_kw)
    return encodebytes(decode_data).decode()

  def updateFileMetadata(self, file:str, source_format:str, metadata_dict:dict) -> str:
    """Receives the string of document and a dict with metadatas. The metadata
    is added in document.
    e.g
    self.updateFileMetadata(data = encodebytes(data), metadata = \
      {"title":"abc","description":...})
    return encodebytes(document_with_metadata)
    """
    self._check_file_type(file)
    handler_class = getHandlerClass(source_format,
                               None,
                               self.mimetype_registry,
                               self.handler_dict)
    handler = handler_class(self._path_tmp_dir,
                            a2b_base64(file),
                            source_format,
                            **self.kw)
    metadata_dict = {key.capitalize(): value \
                        for key, value in metadata_dict.items()}
    decode_data = handler.setMetadata(metadata_dict)
    return encodebytes(decode_data).decode()

  def getFileMetadataItemList(self, file:str, source_format:str, base_document=False) -> dict[str, str]:
    """Receives the string of document as encodebytes and returns a dict with
    metadatas.
    e.g.
    self.getFileMetadataItemList(data = encodebytes(data).decode())
    return {'Title': 'abc','Description': 'comments', 'Data': None}

    If converted_data is True, the ODF of data is added in dictionary.
    e.g
    self.getFileMetadataItemList(data = encodebytes(data).decode(), True)
    return {'Title': 'abc','Description': 'comments', 'Data': string_ODF}

    Note that all keys of the dictionary have the first word in uppercase.
    """
    self._check_file_type(file)
    handler_class = getHandlerClass(source_format,
                                    None,
                                    self.mimetype_registry,
                                    self.handler_dict)
    handler = handler_class(self._path_tmp_dir,
                            a2b_base64(file),
                            source_format,
                            **self.kw)
    metadata_dict = handler.getMetadata(base_document)
    metadata_dict['Data'] = encodebytes(metadata_dict.get('Data', b'')).decode()
    return metadata_dict

  def getAllowedExtensionList(self, request_dict={}):
    """BBB: extension should not be used, use MIMEType with getAllowedConversionFormatList

    List extension which can be generated from given type
    Type can be given as:
      - content type
      - filename extension
      - document type
    """
    mimetype = request_dict.get('mimetype')
    extension = request_dict.get('extension')
    document_type = request_dict.get('document_type')
    if not mimetype:
      if extension:
        mimetype, _ = BBB_guess_type("a." + extension)
      elif document_type:
        # BBB no other choice than to ask ooo.mimemapper
        return mimemapper.getAllowedExtensionList(document_type=document_type)
    if mimetype:
      allowed_extension_set = set()
      for content_type, title in self.getAllowedConversionFormatList(mimetype):
        ext = BBB_guess_extension(content_type, title)
        if ext:
          allowed_extension_set.add((ext.lstrip('.'), title))
      return list(allowed_extension_set) or [('', '')]
    else:
      return [('', '')]

  def getAllowedConversionFormatList(self, source_mimetype:str) -> list:
    r"""Returns a list content_type and their titles which are supported
    by enabled handlers.

    [('application/vnd.oasis.opendocument.text', 'ODF Text Document'),
     ('application/pdf', 'PDF - Portable Document Format'),
     ...
    ]

    This methods gets handler conversion mimetype availability according
    to Cloudooo's mimetype registry.

    /!\ unlike `self.getAllowedExtensionList`, it may return empty list
        instead of `[('', '')]`.

    /!\ the returned list may have the same mimetype twice with different title.
    """
    handler_dict = {}  # handler_dict["ooo"] = ["text/*", "application/*"]
    for entry in self.mimetype_registry:
      split_entry = entry.split()
      if fnmatch(source_mimetype, split_entry[0]):
        if split_entry[2] in handler_dict:
          handler_dict[split_entry[2]].append(split_entry[1])
        else:
          handler_dict[split_entry[2]] = [split_entry[1]]

    output_mimetype_set = set()
    for handler, mimetype_filter_list in handler_dict.items():
      for output_mimetype in self.handler_dict[handler].getAllowedConversionFormatList(source_mimetype):
        for mimetype_filter in mimetype_filter_list:
          if fnmatch(output_mimetype[0], mimetype_filter):
            output_mimetype_set.add(output_mimetype)
            break

    return list(output_mimetype_set)

  def run_convert(self, filename='', data=None, meta=None, extension=None,
                  orig_format=None):
    """Method to support the old API. Wrapper getFileMetadataItemList but
    returns a dict.
    This is a Backwards compatibility provided for ERP5 Project, in order to
    keep compatibility with OpenOffice.org Daemon.
    """
    if not extension:
      extension = filename.split('.')[-1]
    try:
      response_dict = {}
      metadata_dict = self.getFileMetadataItemList(data, extension,
                                                   base_document=True)
      response_dict['meta'] = metadata_dict
      # XXX - Backward compatibility: Previous API expects 'mime' now we
      # use 'MIMEType'
      response_dict['meta']['mime'] = response_dict['meta']['MIMEType']
      response_dict['data'] = response_dict['meta']['Data']
      response_dict['mime'] = response_dict['meta']['MIMEType']
      del response_dict['meta']['Data']
      return (200, response_dict, "")
    except Exception as e:
      logger.error('Error converting to %s', extension, exc_info=True)
      return (402, {}, e.args[0])

  def run_setmetadata(self, filename='', data=None, meta=None,
                      extension=None, orig_format=None):
    """Wrapper updateFileMetadata but returns a dict.
    This is a Backwards compatibility provided for ERP5 Project, in order to
    keep compatibility with OpenOffice.org Daemon.
    """
    if not extension:
      extension = filename.split('.')[-1]
    response_dict = {}
    try:
      response_dict['data'] = self.updateFileMetadata(data, extension, meta)
      return (200, response_dict, '')
    except Exception as e:
      logger.error('Error setting metadata', exc_info=True)
      return (402, {}, e.args[0])

  def run_getmetadata(self, filename='', data=None, meta=None,
                      extension=None, orig_format=None):
    """Wrapper for getFileMetadataItemList.
    This is a Backwards compatibility provided for ERP5 Project, in order to
    keep compatibility with OpenOffice.org Daemon.
    """
    if not extension:
      extension = filename.split('.')[-1]
    response_dict = {}
    try:
      response_dict['meta'] = self.getFileMetadataItemList(data, extension)
      # XXX - Backward compatibility: Previous API expects 'title' now
      # we use 'Title'"
      response_dict['meta']['title'] = response_dict['meta']['Title']
      return (200, response_dict, '')
    except Exception as e:
      logger.error('Error getting metadata', exc_info=True)
      return (402, {}, e.args[0])

  def run_generate(self, filename='', data=None, meta=None, extension=None,
                   orig_format=''):
    """Wrapper convertFile but returns a dict which includes mimetype.
    This is a Backwards compatibility provided for ERP5 Project, in order
    to keep compatibility with OpenOffice.org Daemon.
    """
    # calculate original extension required by convertFile from
    # given content_type (orig_format)
    original_extension = BBB_guess_extension(orig_format).strip('.')
    # XXX - ugly way to remove "/" and "."
    orig_format = orig_format.split('.')[-1]
    orig_format = orig_format.split('/')[-1]
    if "htm" in extension:
      zip = True
    else:
      zip = False
    try:
      response_dict = {}
      # XXX - use html format instead of xhtml
      if orig_format in ("presentation",
                         "graphics",
                         "spreadsheet",
                         'text') and extension == "xhtml":
        extension = 'html'
      response_dict['data'] = self.convertFile(data,
                                               original_extension,
                                               extension,
                                               zip)
      # FIXME: Fast solution to obtain the html or pdf mimetypes
      if zip:
        response_dict['mime'] = "application/zip"
      elif extension == 'xhtml':
        response_dict['mime'] = "text/html"
      else:
        response_dict['mime'] = mimetypes.types_map.get('.%s' % extension,
            mimetypes.types_map.get('.%s' % extension.split('.')[-1]))
      return (200, response_dict, "")
    except Exception as e:
      logger.error('Error in generate from %s to %s', orig_format, extension, exc_info=True)
      return (402, response_dict, str(e))

  def getAllowedTargetItemList(self, content_type:str):
    """Wrapper getAllowedExtensionList but returns a dict.
    This is a Backwards compatibility provided for ERP5 Project, in order to
    keep compatibility with OpenOffice.org Daemon.
    """
    response_dict = {}
    try:
      mimetype_list = self.getAllowedConversionFormatList(content_type)
      extension_list = []
      for m, t in mimetype_list:
        ext = BBB_guess_extension(m, t)
        if ext:
          extension_list.append((ext.lstrip('.'), t))
      response_dict['response_data'] = extension_list
      return (200, response_dict, '')
    except Exception as e:
      logger.error('Error in getting target item list from %s', content_type, exc_info=True)
      return (402, {}, e.args[0])

  def _getOOGranulator(self, data:str, source_format="odt"):
    """Returns an instance of the handler OOGranulator after convert the
    data to 'odt'
    data is a str with the actual data encoded in base64
    """
    GRANULATABLE_FORMAT_LIST = ("odt",)
    if source_format not in GRANULATABLE_FORMAT_LIST:
      data = self.convertFile(data, source_format,
                    GRANULATABLE_FORMAT_LIST[0], zip=False)
    return OOGranulator(a2b_base64(data), GRANULATABLE_FORMAT_LIST[0])

  def getTableItemList(self, data, source_format="odt"):
    """Returns the list of table IDs in the form of (id, title)."""
    document = self._getOOGranulator(data, source_format)
    return document.getTableItemList()

  def getTable(self, data, id, source_format="odt") -> str:
    """Returns the table into a new 'format' file."""
    document = self._getOOGranulator(data, source_format)
    #the file will be convert; so, the source_format will be always 'odt'
    return encodebytes(document.getTable(id, 'odt')).decode()

  def getColumnItemList(self, data, table_id, source_format):
    """Return the list of columns in the form of (id, title)."""
    document = self._getOOGranulator(data, source_format)
    return document.getColumnItemList(table_id)

  def getLineItemList(self, data, table_id, source_format):
    """Returns the lines of a given table as (key, value) pairs."""
    document = self._getOOGranulator(data, source_format)
    return document.getLineItemList(table_id)

  def getImageItemList(self, data:str, source_format:str):
    """Return the list of images in the form of (id, title)."""
    document = self._getOOGranulator(data, source_format)
    return document.getImageItemList()

  def getImage(self, data:str, image_id:str, source_format:str, format=None,
               resolution=None, **kw) -> str:
    """Return the given image."""
    document = self._getOOGranulator(data, source_format)
    return encodebytes(document.getImage(image_id, format, resolution, **kw)).decode()

  def getParagraphItemList(self, data, source_format):
    """Returns the list of paragraphs in the form of (id, class) where class
       may have special meaning to define TOC/TOI."""
    document = self._getOOGranulator(data, source_format)
    return document.getParagraphItemList()

  def getParagraph(self, data, paragraph_id, source_format):
    """Returns the paragraph in the form of (text, class)."""
    document = self._getOOGranulator(data, source_format)
    return document.getParagraph(paragraph_id)

  def getChapterItemList(self, data, source_format):
    """Returns the list of chapters in the form of (id, level)."""
    document = self._getOOGranulator(data, source_format)
    return document.getChapterItemList()

  def getChapterItem(self, chapter_id, data, source_format):
    """Return the chapter in the form of (title, level)."""
    document = self._getOOGranulator(data, source_format)
    return document.getChapterItem(chapter_id)
