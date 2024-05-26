#!/usr/bin/env python
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

import sys
import csv
import codecs
import helper_util
from unohelper import systemPathToFileUrl
from os.path import dirname, splitext
from tempfile import mktemp
from base64 import b64encode, b64decode
from functools import partial
from getopt import getopt, GetoptError
from html.parser import HTMLParser
import os.path
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
import tempfile
from zipfile import BadZipFile, ZipFile

__doc__ = """

usage: unodocument [options]

Options:
  -h, --help            this help screen

  --test                Test if the Openoffice works correctly

  --hostname=STRING     OpenOffice Instance address

  --port=STRING         OpenOffice Instance port

  --document_url=STRING_URL
                        URL of document to load in OpenOffice

  --office_binary_path=STRING_URL
                        Folder path were is the binary openoffice
  --uno_path=STRING_URL
                        Folter path were is the uno library
  --destination_format=STRING
                        extension to export the document
  --mimemapper=OBJECT_SERIALIZED
                        Mimemapper serialized. The object is passed using
                        json. IF this option is None, the object is
                        created
  --metadata=DICT_SERIALIZED
                        Dictionary with metadata
  --infilter=FILTER_NAME[:FILTER_OPTIONS]
                        Import filter with options
  --script=PYTHON_TEXT
                        Script to execute on the loaded document,
                        in Python langage
"""


MARKER = []
def next(gen, default=MARKER):
  try:
    return gen.__next__()
  except StopIteration:
    if default is MARKER:
      raise
    return default


class UnoDocument:
  """A module to easily work with OpenOffice.org."""

  def __init__(self, service_manager, document_url,
               source_format, destination_format, *args):
    self.service_manager = service_manager
    self.document_url = document_url
    self.source_format = source_format
    self.destination_format = destination_format
    self.filter_list = [(x[1], x[2])
      for x in mimemapper.get("filter_list", ())
      if destination_format == x[0] and x[2]
    ] if mimemapper else ()
    self._load(*args)

  def _createProperty(self, name, value):
    """Create property"""
    from com.sun.star.beans import PropertyValue
    property = PropertyValue()
    property.Name = name
    property.Value = value
    return property

  def _createSpecificProperty(self, filter_name):
    """Creates a property according to the filter"""
    import uno
    from com.sun.star.beans import PropertyValue
    if filter_name == "impress_html_Export":
      property = PropertyValue('FilterData', 0,
                        uno.Any('[]com.sun.star.beans.PropertyValue',
                        (PropertyValue('IsExportNotes', 0, True, 0),
                        PropertyValue('PublishMode', 0, 0, 0),
                        PropertyValue('Width', 0, 640, 0),
                        PropertyValue('Format', 0, 2, 0),),), 0)
    elif filter_name == "impress_pdf_Export":
      property = PropertyValue('FilterData', 0,
                       uno.Any('[]com.sun.star.beans.PropertyValue',
                       (PropertyValue('ExportNotesPages', 0, True, 0),
                       PropertyValue('SelectPdfVersion', 0, 1, 0),),), 0)
    elif "pdf_Export" in filter_name :
      property = PropertyValue('FilterData', 0,
                       uno.Any('[]com.sun.star.beans.PropertyValue',
                       (PropertyValue('SelectPdfVersion', 0, 1, 0),),), 0)
    elif filter_name in ("draw_html_Export", "HTML (StarCalc)"):
      property = PropertyValue('FilterData', 0,
                        uno.Any('[]com.sun.star.beans.PropertyValue',
                                (PropertyValue('Format', 0, 2, 0),),), 0)
    elif filter_name == "Text (encoded)":
      property = PropertyValue('FilterFlags', 0, 'UTF8,LF', 0)
    else:
      return []

    return [property, ]

  def _getPropertyToImport(self, infilter,
      _ods="com.sun.star.sheet.SpreadsheetDocument"):
    """Create the property for import filter, according to the extension of the file."""
    from com.sun.star.document.MacroExecMode import NEVER_EXECUTE
    args = [
      self._createProperty('MacroExecMode', NEVER_EXECUTE),
    ]
    if infilter:
      infilter = infilter.split(':', 1)
      args.append(self._createProperty("FilterName", infilter.pop(0)))
      if infilter:
        args.append(self._createProperty("FilterOptions", *infilter))
      return args
    candidates = (x[0] for x in self.filter_list)
    if self.source_format == 'csv':
      if _ods in candidates:
        # https://wiki.openoffice.org/wiki/Documentation/DevGuide/Spreadsheets/Filter_Options

        # Try to sniff the csv delimiter
        with codecs.open(self.document_url, 'rb', 'utf-8', errors="ignore") as csvfile:
          try:
            dialect = csv.Sniffer().sniff(csvfile.read(1024))
            delimiter = ord(dialect.delimiter)
          except csv.Error:
            delimiter = ord(',')

        args.extend((
          self._createProperty("FilterName", "Text - txt - csv (StarCalc)"),
          self._createProperty("FilterOptions", "%s,34,UTF-8" % delimiter))
        )

    elif self.source_format == 'html':
      if next(candidates, None) == _ods:
        args.extend((
          self._createProperty("FilterName", "calc_HTML_WebQuery"),
          )
        )

    return args

  def _load(self, infilter):
    """Create one document with basic properties
    """
    createInstance = self.service_manager.createInstance
    self.desktop = createInstance("com.sun.star.frame.Desktop")
    uno_url = systemPathToFileUrl(self.document_url)
    self.document_loaded = uno_document = self.desktop.loadComponentFromURL(
        uno_url,
        "_blank",
        0,
        self._getPropertyToImport(infilter))
    if not uno_document:
      raise AttributeError("This document can not be loaded or is empty")
    def isSafeUrl(url):
      parsed_url = urlparse(url)
      if parsed_url.scheme == 'data':
        return True
      elif parsed_url.scheme == '':
        norm_path = os.path.normpath(parsed_url.path)
        if norm_path[0] not in ('/', '.') or \
            os.path.dirname(os.path.normpath(parsed_url.path)) == os.path.dirname(self.document_url):
          return True
      return False
    with tempfile.NamedTemporaryFile() as temp_file:
      uno_document.storeToURL(systemPathToFileUrl(temp_file.name), ())
      try:
        with ZipFile(temp_file.name, 'r') as zip_file:
          content = ET.fromstring(zip_file.read('content.xml'))
          for e in content.findall('.//*[@{http://www.w3.org/1999/xlink}actuate="onLoad"]'):
            href = e.attrib.get('{http://www.w3.org/1999/xlink}href')
            if href:
              if not isSafeUrl(href):
                raise RuntimeError('This document contains unsafe links %s' % href)
      except BadZipFile: # HTML input case
        class CustomHTMLParser(HTMLParser):
          def handle_starttag(self, tag, attrs):
            for attr in attrs:
              if attr[0] == 'src':
                if not isSafeUrl(attr[1]):
                  raise RuntimeError('This document contains unsafe links %s' % attr[1])
        parser = CustomHTMLParser()
        with open(temp_file.name, 'r') as f:
          parser.feed(f.read())
    module_manager = createInstance("com.sun.star.frame.ModuleManager")
    self.document_type = module_manager.identify(uno_document)

  def runScript(self, script):
    exec(script, {
      # Inspired from XSCRIPTCONTEXT API.
      # XXX: Is it possible to get a real XSCRIPTCONTEXT object?
      "ComponentContext": self.service_manager.DefaultContext,
      #"Desktop": self.desktop, # is there any reasonable use?
      "Document": self.document_loaded,
    })

  def convert(self):
    """it converts a document to specific format"""
    for document_type, filter_name in self.filter_list:
      if document_type == self.document_type:
        property_list = [
          self._createProperty("Overwrite", True),
          self._createProperty("FilterName", filter_name),
        ]
        property_list += self._createSpecificProperty(filter_name)
        property_list = tuple(property_list)
        break
    else:
        property_list = ()

    ext = self.destination_format
    if ext in ("html", "htm", "xhtml"):
      ext = "impr.html"
    output_url = mktemp(suffix='.' + ext if ext else '',
                        dir=dirname(self.document_url))
    try:
      self.document_loaded.storeToURL(systemPathToFileUrl(output_url),
         property_list)
    finally:
      self.document_loaded.dispose()
    return output_url

  def getMetadata(self):
    """Extract all metadata of the document"""
    metadata = {}
    document_properties = self.document_loaded.getDocumentProperties()
    user_defined_properties = document_properties.getUserDefinedProperties()
    for container in [document_properties, user_defined_properties]:
      for property_name in dir(container):
        if property_name in ('SupportedServiceNames',):
          continue
        property_value = getattr(container, property_name, '')
        if property_value:
          if isinstance(property_value, str):
            metadata[property_name] = property_value
          elif isinstance(property_value, tuple) and isinstance(property_value[0], str):
            metadata[property_name] = property_value
          else:
            try:
              if property_value.typeName == 'com.sun.star.util.DateTime':
                # It is a local time and we have no timezone information.
                datetime = "%02d/%02d/%04d %02d:%02d:%02d" % (property_value.Day, property_value.Month,
                    property_value.Year, property_value.Hours, property_value.Minutes, property_value.Seconds)
                metadata[property_name] = datetime
            except AttributeError:
              pass

    createInstance = self.service_manager.createInstance
    type_detection = createInstance("com.sun.star.document.TypeDetection")
    uno_file_access = createInstance("com.sun.star.ucb.SimpleFileAccess")
    doc = uno_file_access.openFileRead(systemPathToFileUrl(self.document_url))
    input_stream = self._createProperty("InputStream", doc)
    open_new_view = self._createProperty("OpenNewView", True)
    filter_name = type_detection.queryTypeByDescriptor((input_stream,
                                                        open_new_view), True)[0]
    doc.closeInput()
    metadata['MIMEType'] = mimemapper["mimetype_by_filter_type"].get(filter_name)
    return metadata

  def setMetadata(self, metadata):
    """Returns a document with new metadata.

    Keyword arguments:
    metadata -- expected an dictionary with metadata.
    """
    document_properties = self.document_loaded.getDocumentProperties()
    user_defined_properties = document_properties.getUserDefinedProperties()
    new_properties = []
    for prop, value in metadata.items():
      for container in [document_properties, user_defined_properties]:
        current_value = getattr(container, prop, None)
        if current_value is not None:
          if isinstance(current_value, tuple):
            if isinstance(value, list):
              value = tuple(value)
            elif isinstance(value, str):
              # BBB: old ERP5 code sends Keywords as a string
              # separated by a whitespace.
              value = tuple(value.split(' '))
          if isinstance(value, type(current_value)):
            setattr(container, prop, value)
          break
      else:
        new_properties.append([prop, value])
    for prop, value in new_properties:
      if isinstance(value, str):
        user_defined_properties.addProperty(prop, 0, '')
        user_defined_properties.setPropertyValue(prop, value)
    self.document_loaded.store()
    self.document_loaded.dispose()


def help():
  sys.stderr.write(__doc__)
  sys.exit(1)


def main():
  global mimemapper

  help_msg = "\nUse --help or -h\n"
  try:
    opt_list, _ = getopt(sys.argv[1:], "h", ["help", "test",
      "convert", "getmetadata", "setmetadata",
      "uno_path=", "office_binary_path=",
      "hostname=", "port=", "source_format=",
      "document_url=", "destination_format=",
      "mimemapper=", "metadata=",
      "unomimemapper_bin=", "infilter=", "script="])
  except GetoptError as msg:
    msg = msg.msg + help_msg
    sys.stderr.write(msg)
    sys.exit(2)

  param_list = [tuple[0] for tuple in iter(opt_list)]

  import json

  metadata = mimemapper = script = None
  hostname = port = office_binary_path = uno_path = None
  document_url = destination_format = source_format = infilter = None
  for opt, arg in iter(opt_list):
    if opt in ('-h', '--help'):
      help()
    elif opt == '--hostname':
      hostname = arg
    elif opt == '--port':
      port = arg
    elif opt == '--document_url':
      document_url = arg
    elif opt == '--office_binary_path':
      office_binary_path = arg
    elif opt == '--uno_path':
      uno_path = arg
    elif opt == '--destination_format':
      destination_format = arg
    elif opt == '--source_format':
      source_format = arg
    elif opt == '--metadata':
      arg = b64decode(arg).decode('utf-8')
      metadata = json.loads(arg)
    elif opt == '--mimemapper':
      mimemapper = json.loads(arg)
    elif opt == '--infilter':
      infilter = arg
    elif opt == '--script':
      script = arg

  service_manager = helper_util.getServiceManager(
    hostname, port, uno_path, office_binary_path)
  unodocument = UnoDocument(service_manager, document_url,
    source_format, destination_format, infilter)
  if script:
    unodocument.runScript(script)
  if '--setmetadata' in param_list:
    unodocument.setMetadata(metadata)
    output = document_url
  else:
    output = unodocument.convert() if "--convert" in param_list else None
    if '--getmetadata' in param_list:
      if output:
        # Instanciate new UnoDocument instance with new url
        unodocument = UnoDocument(service_manager, output,
          destination_format or source_format, None, None)
      metadata_dict = unodocument.getMetadata()
      if output:
        metadata_dict['document_url'] = output
      output = b64encode(json.dumps(metadata_dict).encode('utf-8')).decode()

  sys.stdout.write(output)

if "__main__" == __name__:
  main()
