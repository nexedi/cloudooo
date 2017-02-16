##############################################################################
#
# Copyright (c) 2009-2011 Nexedi SA and Contributors. All Rights Reserved.
#                    Gabriel M. Monnerat <gabriel@tiolive.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################
from xml.etree import ElementTree
from subprocess import Popen, PIPE
import os
import json
import io
from mimetypes import guess_type

from zope.interface import implements

from cloudooo.interfaces.handler import IHandler
from cloudooo.file import File
from cloudooo.util import logger, zipTree, unzip, parseContentType
from cloudooo.handler.ooo.handler import Handler as OOoHandler
from cloudooo.handler.ooo.handler import bootstrapHandler

from zipfile import ZipFile

AVS_OFFICESTUDIO_FILE_UNKNOWN = "0"
AVS_OFFICESTUDIO_FILE_DOCUMENT_DOCX = "65"
AVS_OFFICESTUDIO_FILE_PRESENTATION_PPTX = "129"
AVS_OFFICESTUDIO_FILE_PRESENTATION_PPSX = "132"
AVS_OFFICESTUDIO_FILE_SPREADSHEET_XLSX = "257"
AVS_OFFICESTUDIO_FILE_CROSSPLATFORM_PDF = "513"
AVS_OFFICESTUDIO_FILE_TEAMLAB_DOCY = "4097"
AVS_OFFICESTUDIO_FILE_TEAMLAB_XLSY = "4098"
AVS_OFFICESTUDIO_FILE_TEAMLAB_PPTY = "4099"
AVS_OFFICESTUDIO_FILE_CANVAS_WORD = "8193"
AVS_OFFICESTUDIO_FILE_CANVAS_SPREADSHEET = "8194"
AVS_OFFICESTUDIO_FILE_CANVAS_PRESENTATION = "8195"
AVS_OFFICESTUDIO_FILE_OTHER_HTMLZIP = "2051"
AVS_OFFICESTUDIO_FILE_OTHER_ZIP = "2057"

format_code_map = {
  "docy": AVS_OFFICESTUDIO_FILE_CANVAS_WORD,
  "docx": AVS_OFFICESTUDIO_FILE_DOCUMENT_DOCX,
  "xlsy": AVS_OFFICESTUDIO_FILE_CANVAS_SPREADSHEET,
  "xlsx": AVS_OFFICESTUDIO_FILE_SPREADSHEET_XLSX,
  "ppty": AVS_OFFICESTUDIO_FILE_CANVAS_PRESENTATION,
  "pptx": AVS_OFFICESTUDIO_FILE_PRESENTATION_PPTX,
}

yformat_map = {
  'docy': 'docx',
  'xlsy': 'xlsx',
  'ppty': 'pptx',
}

yformat2opendocument_map = {
  'docy': 'odt',
  'xlsy': 'ods',
  'ppty': 'odp',
}

yformat_tuple = (
  "docy", "application/x-asc-text",
  "xlsy", "application/x-asc-spreadsheet",
  "ppty", "application/x-asc-presentation",
)

openxml_tuple = (
  "docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation",
)

supported_formats = yformat_tuple + openxml_tuple

class Handler(object):
  """
  X2T Handler is used to convert Microsoft Office 2007 documents to OnlyOffice
  documents.
  """

  implements(IHandler)

  def __init__(self, base_folder_url, data, source_format, **kw):
    """
    base_folder_url(string)
      The requested url for data base folder
    data(string)
      The opened and readed file into a string
    source_format(string)
      The source format of the inputed file
    """
    self.base_folder_url = base_folder_url
    self._data = data
    self._source_format = source_format
    self._init_kw = kw
    self.environment = kw.get("env", {})

  def convert(self, destination_format=None, **kw):
    """ Convert the inputed file to output as format that were informed """
    source_format = self._source_format
    logger.debug("x2t convert: %s > %s" % (source_format, destination_format))
    data = self._data

    if source_format in yformat_tuple:
      supported_format = yformat_map[source_format]
      data = self._convert(data, source_format, supported_format)
      source_format = supported_format

    if destination_format in yformat_tuple:
      supported_format = yformat_map[destination_format]
      if supported_format != source_format:
        data = OOoHandler(self.base_folder_url, data, source_format, **self._init_kw)\
          .convert(destination_format=supported_format)
      data = self._convert(data, supported_format, destination_format)
    elif destination_format != source_format:
      data = OOoHandler(self.base_folder_url, data, source_format, **self._init_kw)\
        .convert(destination_format=destination_format)
    return data

  def _convert(self, data, source_format, destination_format):
    """ Convert the inputed file to output as format that were informed """
    self.file = File(self.base_folder_url, data, source_format)
    logger.debug("x2t convert: %s > %s" % (source_format, destination_format))

    # init vars and xml configuration file
    in_format = format_code_map[source_format]
    out_format = format_code_map[destination_format]
    root_dir = self.file.directory_name
    input_dir = os.path.join(root_dir, "input")
    output_dir = os.path.join(root_dir, "output")
    final_file_name = os.path.join(root_dir, "document.%s" % destination_format)
    input_file_name = self.file.getUrl()
    output_file_name = final_file_name
    config_file_name = os.path.join(root_dir, "config.xml")
    metadata = None
    output_data = None

    if source_format in yformat_tuple:
      if data.startswith("PK\x03\x04"):
        os.mkdir(input_dir)
        unzip(self.file.getUrl(), input_dir)
        input_file_name = os.path.join(input_dir, "body.txt")
        metadata_file_name = os.path.join(input_dir, "metadata.json")
        if os.path.isfile(metadata_file_name):
          with open(metadata_file_name) as metadata_file:
            metadata = json.loads(metadata_file.read())
    if destination_format in yformat_tuple:
      os.mkdir(output_dir)
      output_file_name = os.path.join(output_dir, "body.txt")

    with open(config_file_name, "w") as config_file:
      config = {
        # 'm_sKey': 'from',
        'm_sFileFrom': input_file_name,
        'm_nFormatFrom': in_format,
        'm_sFileTo': output_file_name,
        'm_nFormatTo': out_format,
        # 'm_bPaid': 'true',
        # 'm_bEmbeddedFonts': 'false',
        # 'm_bFromChanges': 'false',
        # 'm_sFontDir': '/usr/share/fonts',
        # 'm_sThemeDir': '/var/www/onlyoffice/documentserver/FileConverterService/presentationthemes',
      }
      root = ElementTree.Element('root')
      for key, value in config.items():
        ElementTree.SubElement(root, key).text = value
      ElementTree.ElementTree(root).write(config_file, encoding='utf-8', xml_declaration=True, default_namespace=None, method="xml")

    # run convertion binary
    p = Popen(
      ["x2t", config_file.name],
      stdout=PIPE,
      stderr=PIPE,
      close_fds=True,
      env=self.environment,
    )
    stdout, stderr = p.communicate()
    if p.returncode != 0:
      raise RuntimeError("x2t: exit code %d != 0\n+ %s\n> stdout: %s\n> stderr: %s@ x2t xml:\n%s" % (p.returncode, " ".join(["x2t", config_file.name]), stdout, stderr, "  " + open(config_file.name).read().replace("\n", "\n  ")))

    self.file.reload(final_file_name)
    try:
      if source_format in yformat_tuple:
        if (metadata):
          output_data = OOoHandler(self.base_folder_url, self.file.getContent(), source_format, **self._init_kw)\
            .setMetadata(metadata)
        else:
          output_data = self.file.getContent()
      elif destination_format in yformat_tuple:
        dir_name = os.path.dirname(output_file_name)
        metadata_file_name = os.path.join(dir_name, "metadata.json")
        with open(metadata_file_name, 'w') as metadata_file:
          metadata = OOoHandler(self.base_folder_url, data, source_format, **self._init_kw).getMetadata()
          metadata.pop('MIMEType', None)
          metadata.pop('Generator', None)
          metadata.pop('AppVersion', None)
          metadata.pop('ImplementationName', None)
          metadata_file.write(json.dumps(metadata))
        zipTree(
          final_file_name,
          (output_file_name, ""),
          (metadata_file_name, ""),
          (os.path.join(dir_name, "media"), ""),
        )
        output_data = self.file.getContent()
    finally:
      self.file.trash()
    return output_data

  def _getContentType(self):
    mimetype_type = None
    if "/" not in self._source_format:
      mimetype_type = guess_type('a.' + self._source_format)[0]
    if mimetype_type is None:
      mimetype_type = self._source_format
    return mimetype_type

  def getMetadata(self, base_document=False):
    r"""Returns a dictionary with all metadata of document.
    """
    if self._source_format in yformat_tuple and self._data.startswith("PK\x03\x04"):
      with io.BytesIO(self._data) as memfile, ZipFile(memfile) as zipfile:
        try:
          metadata = zipfile.read("metadata.json")
        except KeyError:
          metadata = '{}'
        metadata = json.loads(metadata)
        metadata['MIMEType'] = self._getContentType()
        if base_document:
          opendocument_format = yformat2opendocument_map[self._source_format]
          metadata['MIMEType'] = guess_type('a.' + opendocument_format)[0]
          metadata['Data'] = self.convert(opendocument_format)

        return metadata
    else:
      return OOoHandler(self.base_folder_url, self._data, self._source_format, **self._init_kw).getMetadata(base_document)

  def setMetadata(self, metadata={}):
    r"""Returns document with new metadata.
    Keyword arguments:
    metadata -- expected an dictionary with metadata.
    """
    if self._source_format in yformat_tuple and self._data.startswith("PK\x03\x04"):
      with io.BytesIO(self._data) as memfile, ZipFile(memfile) as zipfile:
        zipfile.write("metadata.json", json.dumps(metadata))
        return memfile.getvalue()
    else:
      return OOoHandler(self.base_folder_url, self._data, self._source_format, **self._init_kw).setMetadata(metadata)

  @staticmethod
  def getAllowedConversionFormatList(source_mimetype):
    """Returns a list content_type and their titles which are supported
    by enabled handlers.

    [('application/x-asc-text', 'OnlyOffice Text Document'),
     ...
    ]
    """
    getFormatList = OOoHandler.getAllowedConversionFormatList
    source_mimetype = parseContentType(source_mimetype).gettype()
    if source_mimetype in ("docy", "application/x-asc-text"):
      return getFormatList("application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    if source_mimetype in ("xlsy", "application/x-asc-spreadsheet"):
      return getFormatList("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if source_mimetype in ("ppty", "application/x-asc-presentation"):
      return getFormatList("application/vnd.openxmlformats-officedocument.presentationml.presentation")

    format_list = getFormatList(source_mimetype)
    format_list_append = format_list.append
    for type, _ in format_list:
      if type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        format_list_append(("application/x-asc-text", "OnlyOffice Text Document"))
        break
      if type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        format_list_append(("application/x-asc-spreadsheet", "OnlyOffice Spreadsheet"))
        break
      if type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
        format_list_append(("application/x-asc-presentation", "OnlyOffice Presentation"))
        break
    return format_list

