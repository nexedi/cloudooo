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

import magic
from os import path
from base64 import encodebytes, decodebytes
from cloudooo.tests.handlerTestCase import HandlerTestCase
from cloudooo.handler.ooo.handler import Handler
from cloudooo.handler.ooo.application.openoffice import openoffice
import os
from lxml import etree
from zipfile import ZipFile

OPENOFFICE = True


class TestHandler(HandlerTestCase):
  """Test OOO Handler and manipulation of OOo Instance"""

  _file_path_list = []

  def _save_document(self, document_output_url, data):
    """Create document in file system"""
    with open(document_output_url, "wb") as f:
      f.write(data)
    self._file_path_list.append(document_output_url)

  def _assert_document_output(self, document, expected_mimetype):
    """Check if the document was created correctly"""
    mime = magic.Magic(mime=True)
    mimetype = mime.from_buffer(document)
    self.assertEqual(mimetype, expected_mimetype)

  def tearDown(self):
    """Cleanup temp files
    """
    while self._file_path_list:
      file_path = self._file_path_list.pop()
      if os.path.exists(file_path):
        os.remove(file_path)
    HandlerTestCase.tearDown(self)

  def testConvertOdtToDoc(self):
    """Test convert ODT to DOC"""
    with open("data/test.odt", "rb") as f:
      data = f.read()
    handler = Handler(self.tmp_url,
                        data,
                        'odt')
    doc_exported = handler.convert("doc")
    self._assert_document_output(doc_exported, "application/msword")

  def testConvertDocToOdt(self):
    """Test convert DOC to ODT"""
    with open("data/test.doc", "rb") as f:
      data = f.read()
    handler = Handler(self.tmp_url,
                        data,
                        'doc')
    doc_exported = handler.convert("odt")
    self._assert_document_output(doc_exported,
                          "application/vnd.oasis.opendocument.text")

  def testGetMetadata(self):
    """Test getMetadata"""
    with open("data/test.odt", "rb") as f:
      data = f.read()
    handler = Handler(self.tmp_url,
                        data,
                        'odt')
    metadata = handler.getMetadata()
    self.assertEqual(metadata.get('MIMEType'),
                      'application/vnd.oasis.opendocument.text')
    handler.document.restoreOriginal()
    metadata = handler.getMetadata(True)
    self.assertNotEqual(metadata.get('Data'), '')

  def testSetMetadata(self):
    """Test setMetadata"""
    with open("data/test.odt", "rb") as f:
      data = f.read()
    handler = Handler(self.tmp_url,
                        data,
                        'odt')
    new_data = handler.setMetadata({"Title": "cloudooo Test -"})
    new_handler = Handler(self.tmp_url,
                            new_data,
                            'odt')
    metadata = new_handler.getMetadata()
    self.assertEqual(metadata.get('Title'), "cloudooo Test -")
    handler = Handler(self.tmp_url,
                        data,
                        'odt')
    new_data = handler.setMetadata({"Title": "Namie's working record"})
    new_handler = Handler(self.tmp_url,
                            new_data,
                            'odt')
    metadata = new_handler.getMetadata()
    self.assertEqual(metadata.get('Title'), "Namie's working record")

  def testConvertWithOpenOfficeStopped(self):
    """Test convert with openoffice stopped"""
    openoffice.stop()
    with open("data/test.doc", "rb") as f:
      data = f.read()
    handler = Handler(self.tmp_url,
                        data,
                        'doc')
    doc_exported = handler.convert("odt")
    self._assert_document_output(doc_exported,
                          "application/vnd.oasis.opendocument.text")

  def testGetMetadataWithOpenOfficeStopped(self):
    """Test getMetadata with openoffice stopped"""
    openoffice.stop()
    with open("data/test.odt", "rb") as f:
      data = f.read()
    handler = Handler(self.tmp_url,
                        data,
                        'odt')
    metadata = handler.getMetadata()
    self.assertEqual(metadata.get('Title'), 'title')
    self.assertEqual(metadata.get('MIMEType'),
              'application/vnd.oasis.opendocument.text')

  def testSetMetadataWithOpenOfficeStopped(self):
    """Test setMetadata with openoffice stopped"""
    openoffice.stop()
    with open("data/test.doc", "rb") as f:
      data = f.read()
    handler = Handler(self.tmp_url,
                        data,
                        'doc')
    new_data = handler.setMetadata({"Title": "cloudooo Test -"})
    new_handler = Handler(self.tmp_url,
                            new_data,
                            'doc')
    metadata = new_handler.getMetadata()
    self.assertEqual(metadata.get('Title'), "cloudooo Test -")

  def testRefreshOdt(self):
    """Test refresh argument"""
    with open("data/test_fields.odt", "rb") as f:
      data = f.read()
    # refresh parameter is now ignored.
    handler = Handler(self.tmp_url,
                        data,
                        'odt',
                        refresh=False)
    doc_exported = handler.convert("odt")
    document_output_url = path.join(self.tmp_url, "testExport.odt")
    self._save_document(document_output_url, doc_exported)
    zip_handler = ZipFile(document_output_url)
    content_tree = etree.fromstring(zip_handler.read('content.xml'))
    self.assertTrue(content_tree.xpath('//text:variable-get[text() = "DISPLAY ME"]',
                                       namespaces=content_tree.nsmap))

  def testGetAllowedConversionFormatList_TextPlain(self):
    """Test allowed conversion format for text/plain with charset parameter"""
    def get(*args, **kw):
      return sorted(Handler.getAllowedConversionFormatList(*args, **kw))
    text_plain_output_list = [
      ('application/epub+zip', 'EPUB Document'),
      ('application/msword', 'Word 97–2003'),
      ('application/pdf', 'PDF - Portable Document Format'),
      ('application/rtf', 'Rich Text'),
      ('application/vnd.ms-word.document.macroEnabled.12', 'Word 2007 VBA'),
      ('application/vnd.oasis.opendocument.text', 'ODF Text Document'),
      ('application/vnd.oasis.opendocument.text-flat-xml', 'Flat XML ODF Text Document'),
      ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'Word 2007'),
      ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'Word 2010–365 Document'),
      ('image/jpeg', 'JPEG - Joint Photographic Experts Group'),
      ('image/png', 'PNG - Portable Network Graphics'),
      ('image/webp', 'WEBP - WebP Image'),
      ('text/html', 'HTML Document (Writer)'),
      ('text/plain', 'Text - Choose Encoding'),
    ]
    self.assertEqual(get("text/plain;ignored=param"), text_plain_output_list)
    self.assertEqual(get("text/plain;charset=UTF-8;ignored=param"), text_plain_output_list)
    self.assertEqual(get("text/plain;charset=US-ASCII;ignored=param"), text_plain_output_list)

  def testGetAllowedConversionFormatList_ApplicationMsword(self):
    """Test allowed conversion format for application/msword"""
    self.assertEqual(
      sorted(Handler.getAllowedConversionFormatList("application/msword;ignored=param")),
      [ ('application/epub+zip', 'EPUB Document'),
        ('application/msword', 'Word 97–2003'),
        ('application/pdf', 'PDF - Portable Document Format'),
        ('application/rtf', 'Rich Text'),
        ('application/vnd.ms-word.document.macroEnabled.12', 'Word 2007 VBA'),
        ('application/vnd.oasis.opendocument.text', 'ODF Text Document'),
        ('application/vnd.oasis.opendocument.text-flat-xml', 'Flat XML ODF Text Document'),
        ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'Word 2007'),
        ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'Word 2010–365 Document'),
        ('image/jpeg', 'JPEG - Joint Photographic Experts Group'),
        ('image/png', 'PNG - Portable Network Graphics'),
        ('image/webp', 'WEBP - WebP Image'),
        ('text/html', 'HTML Document (Writer)'),
        ('text/plain', 'Text - Choose Encoding') ])

  def testGetAllowedConversionFormatList_ApplicationPdf(self):
    """Test allowed conversion format for application/pdf"""
    self.assertEqual(
      sorted(Handler.getAllowedConversionFormatList("application/pdf;ignored=param")),
      [ ('application/pdf', 'PDF - Portable Document Format'),
        ('application/postscript', 'EPS - Encapsulated PostScript'),
        ('application/vnd.oasis.opendocument.graphics', 'ODF Drawing'),
        ('application/vnd.oasis.opendocument.graphics-flat-xml', 'Flat XML ODF Drawing'),
        ('application/x-ms-wmz', 'WMZ - Compressed Windows Metafile'),
        ('image/emf', 'EMF - Enhanced Metafile'),
        ('image/gif', 'GIF - Graphics Interchange Format'),
        ('image/jpeg', 'JPEG - Joint Photographic Experts Group'),
        ('image/png', 'PNG - Portable Network Graphics'),
        ('image/svg+xml', 'SVG - Scalable Vector Graphics'),
        ('image/svg+xml', 'SVGZ - Compressed Scalable Vector Graphics'),
        ('image/tiff', 'TIFF - Tagged Image File Format'),
        ('image/vnd.mozilla.apng', 'APNG - Animated Portable Network Graphics'),
        ('image/webp', 'WEBP - WebP Image'),
        ('image/wmf', 'WMF - Windows Metafile'),
        ('image/x-ms-bmp', 'BMP - Windows Bitmap'),
        ('text/html', 'HTML Document (Draw)') ])

  def testGetAllowedConversionFormatList_TextRtf(self):
    """Test allowed conversion format for text/rtf"""
    self.assertEqual(
      sorted(Handler.getAllowedConversionFormatList("text/rtf;ignored=param")),
      [])

  def testGetAllowedConversionFormatList_ApplicationVndOasisOpendocumentText(self):
    """Test allowed conversion format for application/vnd.oasis.opendocument.text"""
    for content_type in (
      "application/vnd.oasis.opendocument.text;ignored=param",
      "application/vnd.oasis.opendocument.text-flat-xml;ignored=param",
      ):
      self.assertEqual(
        sorted(Handler.getAllowedConversionFormatList(content_type)), [
        ('application/epub+zip', 'EPUB Document'),
        ('application/msword', 'Word 97–2003'),
        ('application/pdf', 'PDF - Portable Document Format'),
        ('application/rtf', 'Rich Text'),
        ('application/vnd.ms-word.document.macroEnabled.12', 'Word 2007 VBA'),
        ('application/vnd.oasis.opendocument.text', 'ODF Text Document'),
        ('application/vnd.oasis.opendocument.text-flat-xml', 'Flat XML ODF Text Document'),
        ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'Word 2007'),
        ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'Word 2010–365 Document'),
        ('image/jpeg', 'JPEG - Joint Photographic Experts Group'),
        ('image/png', 'PNG - Portable Network Graphics'),
        ('image/webp', 'WEBP - WebP Image'),
        ('text/html', 'HTML Document (Writer)'),
        ('text/plain', 'Text - Choose Encoding'),
        ])

  def testGetAllowedConversionFormatList_ApplicationVndOpenxmlformatsOfficedocumentWordprocessingmlDocument(self):
    """Test allowed conversion format for application/vnd.openxmlformats-officedocument.wordprocessingml.document"""
    self.assertEqual(
      sorted(Handler.getAllowedConversionFormatList("application/vnd.openxmlformats-officedocument.wordprocessingml.document;ignored=param")),
      [ ('application/epub+zip', 'EPUB Document'),
        ('application/msword', 'Word 97–2003'),
        ('application/pdf', 'PDF - Portable Document Format'),
        ('application/rtf', 'Rich Text'),
        ('application/vnd.ms-word.document.macroEnabled.12', 'Word 2007 VBA'),
        ('application/vnd.oasis.opendocument.text', 'ODF Text Document'),
        ('application/vnd.oasis.opendocument.text-flat-xml', 'Flat XML ODF Text Document'),
        ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'Word 2007'),
        ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'Word 2010–365 Document'),
        ('image/jpeg', 'JPEG - Joint Photographic Experts Group'),
        ('image/png', 'PNG - Portable Network Graphics'),
        ('image/webp', 'WEBP - WebP Image'),
        ('text/html', 'HTML Document (Writer)'),
        ('text/plain', 'Text - Choose Encoding') ])

  def testGetAllowedConversionFormatList_ImageJpeg(self):
    """Test allowed conversion format for image/jpeg"""
    self.assertEqual(
      sorted(Handler.getAllowedConversionFormatList("image/jpeg;ignored=param")),
      [ ('application/pdf', 'PDF - Portable Document Format'),
        ('application/postscript', 'EPS - Encapsulated PostScript'),
        ('application/vnd.oasis.opendocument.graphics', 'ODF Drawing'),
        ('application/vnd.oasis.opendocument.graphics-flat-xml', 'Flat XML ODF Drawing'),
        ('application/x-ms-wmz', 'WMZ - Compressed Windows Metafile'),
        ('image/emf', 'EMF - Enhanced Metafile'),
        ('image/gif', 'GIF - Graphics Interchange Format'),
        ('image/jpeg', 'JPEG - Joint Photographic Experts Group'),
        ('image/png', 'PNG - Portable Network Graphics'),
        ('image/svg+xml', 'SVG - Scalable Vector Graphics'),
        ('image/svg+xml', 'SVGZ - Compressed Scalable Vector Graphics'),
        ('image/tiff', 'TIFF - Tagged Image File Format'),
        ('image/vnd.mozilla.apng', 'APNG - Animated Portable Network Graphics'),
        ('image/webp', 'WEBP - WebP Image'),
        ('image/wmf', 'WMF - Windows Metafile'),
        ('image/x-ms-bmp', 'BMP - Windows Bitmap'),
        ('text/html', 'HTML Document (Draw)') ])

  def testGetAllowedConversionFormatList_ImagePng(self):
    """Test allowed conversion format for image/png"""
    self.assertEqual(
      sorted(Handler.getAllowedConversionFormatList("image/png;ignored=param")),
      [ ('application/pdf', 'PDF - Portable Document Format'),
        ('application/postscript', 'EPS - Encapsulated PostScript'),
        ('application/vnd.oasis.opendocument.graphics', 'ODF Drawing'),
        ('application/vnd.oasis.opendocument.graphics-flat-xml', 'Flat XML ODF Drawing'),
        ('application/x-ms-wmz', 'WMZ - Compressed Windows Metafile'),
        ('image/emf', 'EMF - Enhanced Metafile'),
        ('image/gif', 'GIF - Graphics Interchange Format'),
        ('image/jpeg', 'JPEG - Joint Photographic Experts Group'),
        ('image/png', 'PNG - Portable Network Graphics'),
        ('image/svg+xml', 'SVG - Scalable Vector Graphics'),
        ('image/svg+xml', 'SVGZ - Compressed Scalable Vector Graphics'),
        ('image/tiff', 'TIFF - Tagged Image File Format'),
        ('image/vnd.mozilla.apng', 'APNG - Animated Portable Network Graphics'),
        ('image/webp', 'WEBP - WebP Image'),
        ('image/wmf', 'WMF - Windows Metafile'),
        ('image/x-ms-bmp', 'BMP - Windows Bitmap'),
        ('text/html', 'HTML Document (Draw)') ])

  def testGetAllowedConversionFormatList_TextHtml(self):
    """Test allowed conversion format for text/html"""
    self.assertEqual(
      sorted(Handler.getAllowedConversionFormatList("text/html;ignored=param")),
      [ ('application/epub+zip', 'EPUB Document'),
        ('application/msword', 'Word 97–2003'),
        ('application/pdf', 'PDF - Portable Document Format'),
        ('application/rtf', 'Rich Text'),
        ('application/vnd.ms-excel', 'Excel 97–2003'),
        ('application/vnd.ms-excel.sheet.macroEnabled.12', 'Excel 2007–365 (macro-enabled)'),
        ('application/vnd.ms-word.document.macroEnabled.12', 'Word 2007 VBA'),
        ('application/vnd.oasis.opendocument.spreadsheet', 'ODF Spreadsheet'),
        ('application/vnd.oasis.opendocument.spreadsheet-flat-xml', 'Flat XML ODF Spreadsheet'),
        ('application/vnd.oasis.opendocument.text', 'ODF Text Document'),
        ('application/vnd.oasis.opendocument.text', 'Text (Writer/Web)'),
        ('application/vnd.oasis.opendocument.text-flat-xml', 'Flat XML ODF Text Document'),
        ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'Excel 2007–365'),
        ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'Office Open XML Spreadsheet'),
        ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'Word 2007'),
        ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'Word 2010–365 Document'),
        ('application/vnd.sun.xml.writer', 'OpenOffice.org 1.0 Text Document (Writer/Web)'),
        ('image/jpeg', 'JPEG - Joint Photographic Experts Group'),
        ('image/png', 'PNG - Portable Network Graphics'),
        ('image/webp', 'WEBP - WebP Image'),
        ('text/csv', 'Text CSV'),
        ('text/html', 'HTML Document'),
        ('text/html', 'HTML Document (Calc)'),
        ('text/html', 'HTML Document (Writer)'),
        ('text/plain', 'Text (Writer/Web)'),
        ('text/plain', 'Text - Choose Encoding'),
        ('text/plain', 'Text - Choose Encoding (Writer/Web)') ])

  def testGetAllowedConversionFormatList_ApplicationPostscript(self):
    """Test allowed conversion format for application/postscript"""
    self.assertEqual(
      sorted(Handler.getAllowedConversionFormatList("application/postscript;ignored=param")),
      [ ('application/pdf', 'PDF - Portable Document Format'),
        ('application/postscript', 'EPS - Encapsulated PostScript'),
        ('application/vnd.oasis.opendocument.graphics', 'ODF Drawing'),
        ('application/vnd.oasis.opendocument.graphics-flat-xml', 'Flat XML ODF Drawing'),
        ('application/x-ms-wmz', 'WMZ - Compressed Windows Metafile'),
        ('image/emf', 'EMF - Enhanced Metafile'),
        ('image/gif', 'GIF - Graphics Interchange Format'),
        ('image/jpeg', 'JPEG - Joint Photographic Experts Group'),
        ('image/png', 'PNG - Portable Network Graphics'),
        ('image/svg+xml', 'SVG - Scalable Vector Graphics'),
        ('image/svg+xml', 'SVGZ - Compressed Scalable Vector Graphics'),
        ('image/tiff', 'TIFF - Tagged Image File Format'),
        ('image/vnd.mozilla.apng', 'APNG - Animated Portable Network Graphics'),
        ('image/webp', 'WEBP - WebP Image'),
        ('image/wmf', 'WMF - Windows Metafile'),
        ('image/x-ms-bmp', 'BMP - Windows Bitmap'),
        ('text/html', 'HTML Document (Draw)') ])

  def testGetAllowedConversionFormatList_ApplicationVndOasisOpendocumentGraphics(self):
    """Test allowed conversion format for application/vnd.oasis.opendocument.graphics"""
    self.assertEqual(
      sorted(Handler.getAllowedConversionFormatList("application/vnd.oasis.opendocument.graphics;ignored=param")),
      [ ('application/pdf', 'PDF - Portable Document Format'),
        ('application/postscript', 'EPS - Encapsulated PostScript'),
        ('application/vnd.oasis.opendocument.graphics', 'ODF Drawing'),
        ('application/vnd.oasis.opendocument.graphics-flat-xml', 'Flat XML ODF Drawing'),
        ('application/x-ms-wmz', 'WMZ - Compressed Windows Metafile'),
        ('image/emf', 'EMF - Enhanced Metafile'),
        ('image/gif', 'GIF - Graphics Interchange Format'),
        ('image/jpeg', 'JPEG - Joint Photographic Experts Group'),
        ('image/png', 'PNG - Portable Network Graphics'),
        ('image/svg+xml', 'SVG - Scalable Vector Graphics'),
        ('image/svg+xml', 'SVGZ - Compressed Scalable Vector Graphics'),
        ('image/tiff', 'TIFF - Tagged Image File Format'),
        ('image/vnd.mozilla.apng', 'APNG - Animated Portable Network Graphics'),
        ('image/webp', 'WEBP - WebP Image'),
        ('image/wmf', 'WMF - Windows Metafile'),
        ('image/x-ms-bmp', 'BMP - Windows Bitmap'),
        ('text/html', 'HTML Document (Draw)') ])

  def testGetAllowedConversionFormatList_ImageGif(self):
    """Test allowed conversion format for image/gif"""
    self.assertEqual(
      sorted(Handler.getAllowedConversionFormatList("image/gif;ignored=param")),
      [ ('application/pdf', 'PDF - Portable Document Format'),
        ('application/postscript', 'EPS - Encapsulated PostScript'),
        ('application/vnd.oasis.opendocument.graphics', 'ODF Drawing'),
        ('application/vnd.oasis.opendocument.graphics-flat-xml', 'Flat XML ODF Drawing'),
        ('application/x-ms-wmz', 'WMZ - Compressed Windows Metafile'),
        ('image/emf', 'EMF - Enhanced Metafile'),
        ('image/gif', 'GIF - Graphics Interchange Format'),
        ('image/jpeg', 'JPEG - Joint Photographic Experts Group'),
        ('image/png', 'PNG - Portable Network Graphics'),
        ('image/svg+xml', 'SVG - Scalable Vector Graphics'),
        ('image/svg+xml', 'SVGZ - Compressed Scalable Vector Graphics'),
        ('image/tiff', 'TIFF - Tagged Image File Format'),
        ('image/vnd.mozilla.apng', 'APNG - Animated Portable Network Graphics'),
        ('image/webp', 'WEBP - WebP Image'),
        ('image/wmf', 'WMF - Windows Metafile'),
        ('image/x-ms-bmp', 'BMP - Windows Bitmap'),
        ('text/html', 'HTML Document (Draw)') ])

  def testGetAllowedConversionFormatList_ImageSvgXml(self):
    """Test allowed conversion format for image/svg+xml"""
    self.assertEqual(
      sorted(Handler.getAllowedConversionFormatList("image/svg+xml;ignored=param")),
      [('application/pdf', 'PDF - Portable Document Format'),
       ('application/postscript', 'EPS - Encapsulated PostScript'),
       ('application/vnd.ms-powerpoint', 'PowerPoint 97–2003'),
       ('application/vnd.ms-powerpoint', 'PowerPoint 97–2003 AutoPlay'),
       ('application/vnd.ms-powerpoint.presentation.macroEnabled.12', 'PowerPoint 2007–365 VBA'),
       ('application/vnd.oasis.opendocument.graphics', 'ODF Drawing'),
       ('application/vnd.oasis.opendocument.graphics-flat-xml', 'Flat XML ODF Drawing'),
       ('application/vnd.oasis.opendocument.presentation', 'ODF Presentation'),
       ('application/vnd.oasis.opendocument.presentation-flat-xml', 'Flat XML ODF Presentation'),
       ('application/vnd.openxmlformats-officedocument.presentationml.presentation', 'Office Open XML Presentation'),
       ('application/vnd.openxmlformats-officedocument.presentationml.presentation', 'PowerPoint 2007–365'),
       ('application/vnd.openxmlformats-officedocument.presentationml.slideshow', 'Office Open XML Presentation AutoPlay'),
       ('application/vnd.openxmlformats-officedocument.presentationml.slideshow', 'PowerPoint 2007–365 AutoPlay'),
       ('application/x-ms-wmz', 'WMZ - Compressed Windows Metafile'),
       ('image/emf', 'EMF - Enhanced Metafile'),
       ('image/gif', 'GIF - Graphics Interchange Format'),
       ('image/jpeg', 'JPEG - Joint Photographic Experts Group'),
       ('image/png', 'PNG - Portable Network Graphics'),
       ('image/svg+xml', 'SVG - Scalable Vector Graphics'),
       ('image/svg+xml', 'SVGZ - Compressed Scalable Vector Graphics'),
       ('image/tiff', 'TIFF - Tagged Image File Format'),
       ('image/vnd.mozilla.apng', 'APNG - Animated Portable Network Graphics'),
       ('image/webp', 'WEBP - WebP Image'),
       ('image/wmf', 'WMF - Windows Metafile'),
       ('image/x-ms-bmp', 'BMP - Windows Bitmap'),
       ('text/html', 'HTML Document (Draw)'),
       ('text/html', 'HTML Document (Impress)') ])

  def testGetAllowedConversionFormatList_ImageTiff(self):
    """Test allowed conversion format for image/tiff"""
    self.assertEqual(
      sorted(Handler.getAllowedConversionFormatList("image/tiff;ignored=param")),
      [ ('application/pdf', 'PDF - Portable Document Format'),
        ('application/postscript', 'EPS - Encapsulated PostScript'),
        ('application/vnd.oasis.opendocument.graphics', 'ODF Drawing'),
        ('application/vnd.oasis.opendocument.graphics-flat-xml', 'Flat XML ODF Drawing'),
        ('application/x-ms-wmz', 'WMZ - Compressed Windows Metafile'),
        ('image/emf', 'EMF - Enhanced Metafile'),
        ('image/gif', 'GIF - Graphics Interchange Format'),
        ('image/jpeg', 'JPEG - Joint Photographic Experts Group'),
        ('image/png', 'PNG - Portable Network Graphics'),
        ('image/svg+xml', 'SVG - Scalable Vector Graphics'),
        ('image/svg+xml', 'SVGZ - Compressed Scalable Vector Graphics'),
        ('image/tiff', 'TIFF - Tagged Image File Format'),
        ('image/vnd.mozilla.apng', 'APNG - Animated Portable Network Graphics'),
        ('image/webp', 'WEBP - WebP Image'),
        ('image/wmf', 'WMF - Windows Metafile'),
        ('image/x-ms-bmp', 'BMP - Windows Bitmap'),
        ('text/html', 'HTML Document (Draw)')])

  def testGetAllowedConversionFormatList_ImageXCmuRaster(self):
    """Test allowed conversion format for image/x-cmu-raster"""
    self.assertEqual(
      sorted(Handler.getAllowedConversionFormatList("image/x-cmu-raster;ignored=param")),
      [ ('application/pdf', 'PDF - Portable Document Format'),
        ('application/postscript', 'EPS - Encapsulated PostScript'),
        ('application/vnd.oasis.opendocument.graphics', 'ODF Drawing'),
        ('application/vnd.oasis.opendocument.graphics-flat-xml', 'Flat XML ODF Drawing'),
        ('application/x-ms-wmz', 'WMZ - Compressed Windows Metafile'),
        ('image/emf', 'EMF - Enhanced Metafile'),
        ('image/gif', 'GIF - Graphics Interchange Format'),
        ('image/jpeg', 'JPEG - Joint Photographic Experts Group'),
        ('image/png', 'PNG - Portable Network Graphics'),
        ('image/svg+xml', 'SVG - Scalable Vector Graphics'),
        ('image/svg+xml', 'SVGZ - Compressed Scalable Vector Graphics'),
        ('image/tiff', 'TIFF - Tagged Image File Format'),
        ('image/vnd.mozilla.apng', 'APNG - Animated Portable Network Graphics'),
        ('image/webp', 'WEBP - WebP Image'),
        ('image/wmf', 'WMF - Windows Metafile'),
        ('image/x-ms-bmp', 'BMP - Windows Bitmap'),
        ('text/html', 'HTML Document (Draw)') ])

  def testGetAllowedConversionFormatList_ImageBmp(self):
    """Test allowed conversion format for image/x-ms-bmp"""
    self.assertEqual(
      sorted(Handler.getAllowedConversionFormatList("image/x-ms-bmp;ignored=param")),
      [ ('application/pdf', 'PDF - Portable Document Format'),
        ('application/postscript', 'EPS - Encapsulated PostScript'),
        ('application/vnd.oasis.opendocument.graphics', 'ODF Drawing'),
        ('application/vnd.oasis.opendocument.graphics-flat-xml', 'Flat XML ODF Drawing'),
        ('application/x-ms-wmz', 'WMZ - Compressed Windows Metafile'),
        ('image/emf', 'EMF - Enhanced Metafile'),
        ('image/gif', 'GIF - Graphics Interchange Format'),
        ('image/jpeg', 'JPEG - Joint Photographic Experts Group'),
        ('image/png', 'PNG - Portable Network Graphics'),
        ('image/svg+xml', 'SVG - Scalable Vector Graphics'),
        ('image/svg+xml', 'SVGZ - Compressed Scalable Vector Graphics'),
        ('image/tiff', 'TIFF - Tagged Image File Format'),
        ('image/vnd.mozilla.apng', 'APNG - Animated Portable Network Graphics'),
        ('image/webp', 'WEBP - WebP Image'),
        ('image/wmf', 'WMF - Windows Metafile'),
        ('image/x-ms-bmp', 'BMP - Windows Bitmap'),
        ('text/html', 'HTML Document (Draw)') ])

  def testGetAllowedConversionFormatList_ImageXPortableBitmap(self):
    """Test allowed conversion format for image/x-portable-bitmap"""
    self.assertEqual(
      sorted(Handler.getAllowedConversionFormatList("image/x-portable-bitmap;ignored=param")),
      [ ('application/pdf', 'PDF - Portable Document Format'),
        ('application/postscript', 'EPS - Encapsulated PostScript'),
        ('application/vnd.oasis.opendocument.graphics', 'ODF Drawing'),
        ('application/vnd.oasis.opendocument.graphics-flat-xml', 'Flat XML ODF Drawing'),
        ('application/x-ms-wmz', 'WMZ - Compressed Windows Metafile'),
        ('image/emf', 'EMF - Enhanced Metafile'),
        ('image/gif', 'GIF - Graphics Interchange Format'),
        ('image/jpeg', 'JPEG - Joint Photographic Experts Group'),
        ('image/png', 'PNG - Portable Network Graphics'),
        ('image/svg+xml', 'SVG - Scalable Vector Graphics'),
        ('image/svg+xml', 'SVGZ - Compressed Scalable Vector Graphics'),
        ('image/tiff', 'TIFF - Tagged Image File Format'),
        ('image/vnd.mozilla.apng', 'APNG - Animated Portable Network Graphics'),
        ('image/webp', 'WEBP - WebP Image'),
        ('image/wmf', 'WMF - Windows Metafile'),
        ('image/x-ms-bmp', 'BMP - Windows Bitmap'),
        ('text/html', 'HTML Document (Draw)') ])

  def testGetAllowedConversionFormatList_ImageXPortableGraymap(self):
    """Test allowed conversion format for image/x-portable-graymap"""
    self.assertEqual(
      sorted(Handler.getAllowedConversionFormatList("image/x-portable-graymap;ignored=param")),
      [ ('application/pdf', 'PDF - Portable Document Format'),
        ('application/postscript', 'EPS - Encapsulated PostScript'),
        ('application/vnd.oasis.opendocument.graphics', 'ODF Drawing'),
        ('application/vnd.oasis.opendocument.graphics-flat-xml', 'Flat XML ODF Drawing'),
        ('application/x-ms-wmz', 'WMZ - Compressed Windows Metafile'),
        ('image/emf', 'EMF - Enhanced Metafile'),
        ('image/gif', 'GIF - Graphics Interchange Format'),
        ('image/jpeg', 'JPEG - Joint Photographic Experts Group'),
        ('image/png', 'PNG - Portable Network Graphics'),
        ('image/svg+xml', 'SVG - Scalable Vector Graphics'),
        ('image/svg+xml', 'SVGZ - Compressed Scalable Vector Graphics'),
        ('image/tiff', 'TIFF - Tagged Image File Format'),
        ('image/vnd.mozilla.apng', 'APNG - Animated Portable Network Graphics'),
        ('image/webp', 'WEBP - WebP Image'),
        ('image/wmf', 'WMF - Windows Metafile'),
        ('image/x-ms-bmp', 'BMP - Windows Bitmap'),
        ('text/html', 'HTML Document (Draw)') ])

  def testGetAllowedConversionFormatList_ImageXPortablePixmap(self):
    """Test allowed conversion format for image/x-portable-pixmap"""
    self.assertEqual(
      sorted(Handler.getAllowedConversionFormatList("image/x-portable-pixmap;ignored=param")),
      [ ('application/pdf', 'PDF - Portable Document Format'),
        ('application/postscript', 'EPS - Encapsulated PostScript'),
        ('application/vnd.oasis.opendocument.graphics', 'ODF Drawing'),
        ('application/vnd.oasis.opendocument.graphics-flat-xml', 'Flat XML ODF Drawing'),
        ('application/x-ms-wmz', 'WMZ - Compressed Windows Metafile'),
        ('image/emf', 'EMF - Enhanced Metafile'),
        ('image/gif', 'GIF - Graphics Interchange Format'),
        ('image/jpeg', 'JPEG - Joint Photographic Experts Group'),
        ('image/png', 'PNG - Portable Network Graphics'),
        ('image/svg+xml', 'SVG - Scalable Vector Graphics'),
        ('image/svg+xml', 'SVGZ - Compressed Scalable Vector Graphics'),
        ('image/tiff', 'TIFF - Tagged Image File Format'),
        ('image/vnd.mozilla.apng', 'APNG - Animated Portable Network Graphics'),
        ('image/webp', 'WEBP - WebP Image'),
        ('image/wmf', 'WMF - Windows Metafile'),
        ('image/x-ms-bmp', 'BMP - Windows Bitmap'),
        ('text/html', 'HTML Document (Draw)') ])

  def testGetAllowedConversionFormatList_ImageXXpixmap(self):
    """Test allowed conversion format for image/x-xpixmap"""
    self.assertEqual(
      sorted(Handler.getAllowedConversionFormatList("image/x-xpixmap;ignored=param")),
      [ ('application/pdf', 'PDF - Portable Document Format'),
        ('application/postscript', 'EPS - Encapsulated PostScript'),
        ('application/vnd.oasis.opendocument.graphics', 'ODF Drawing'),
        ('application/vnd.oasis.opendocument.graphics-flat-xml', 'Flat XML ODF Drawing'),
        ('application/x-ms-wmz', 'WMZ - Compressed Windows Metafile'),
        ('image/emf', 'EMF - Enhanced Metafile'),
        ('image/gif', 'GIF - Graphics Interchange Format'),
        ('image/jpeg', 'JPEG - Joint Photographic Experts Group'),
        ('image/png', 'PNG - Portable Network Graphics'),
        ('image/svg+xml', 'SVG - Scalable Vector Graphics'),
        ('image/svg+xml', 'SVGZ - Compressed Scalable Vector Graphics'),
        ('image/tiff', 'TIFF - Tagged Image File Format'),
        ('image/vnd.mozilla.apng', 'APNG - Animated Portable Network Graphics'),
        ('image/webp', 'WEBP - WebP Image'),
        ('image/wmf', 'WMF - Windows Metafile'),
        ('image/x-ms-bmp', 'BMP - Windows Bitmap'),
        ('text/html', 'HTML Document (Draw)') ])

  def testGetAllowedConversionFormatList_ApplicationVndMsExcel(self):
    """Test allowed conversion format for application/vnd.ms-excel"""
    self.assertEqual(
      sorted(Handler.getAllowedConversionFormatList("application/vnd.ms-excel;ignored=param")),
      [ ('application/pdf', 'PDF - Portable Document Format'),
        ('application/vnd.ms-excel', 'Excel 97–2003'),
        ('application/vnd.ms-excel.sheet.macroEnabled.12', 'Excel 2007–365 (macro-enabled)'),
        ('application/vnd.oasis.opendocument.spreadsheet', 'ODF Spreadsheet'),
        ('application/vnd.oasis.opendocument.spreadsheet-flat-xml', 'Flat XML ODF Spreadsheet'),
        ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'Excel 2007–365'),
        ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'Office Open XML Spreadsheet'),
        ('image/jpeg', 'JPEG - Joint Photographic Experts Group'),
        ('image/png', 'PNG - Portable Network Graphics'),
        ('image/webp', 'WEBP - WebP Image'),
        ('text/csv', 'Text CSV'),
        ('text/html', 'HTML Document (Calc)') ])

  def testGetAllowedConversionFormatList_ApplicationVndMsExcelSheetMacroenabled12(self):
    """Test allowed conversion format for application/vnd.ms-excel.sheet.macroEnabled.12"""
    self.assertEqual(
      sorted(Handler.getAllowedConversionFormatList("application/vnd.ms-excel.sheet.macroEnabled.12;ignored=param")),
      [])

  def testGetAllowedConversionFormatList_ApplicationVndOasisOpendocumentSpreadsheet(self):
    """Test allowed conversion format for application/vnd.oasis.opendocument.spreadsheet"""
    self.assertEqual(
      sorted(Handler.getAllowedConversionFormatList("application/vnd.oasis.opendocument.spreadsheet;ignored=param")),
      [ ('application/pdf', 'PDF - Portable Document Format'),
        ('application/vnd.ms-excel', 'Excel 97–2003'),
        ('application/vnd.ms-excel.sheet.macroEnabled.12', 'Excel 2007–365 (macro-enabled)'),
        ('application/vnd.oasis.opendocument.spreadsheet', 'ODF Spreadsheet'),
        ('application/vnd.oasis.opendocument.spreadsheet-flat-xml', 'Flat XML ODF Spreadsheet'),
        ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'Excel 2007–365'),
        ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'Office Open XML Spreadsheet'),
        ('image/jpeg', 'JPEG - Joint Photographic Experts Group'),
        ('image/png', 'PNG - Portable Network Graphics'),
        ('image/webp', 'WEBP - WebP Image'),
        ('text/csv', 'Text CSV'),
        ('text/html', 'HTML Document (Calc)') ])

  def testGetAllowedConversionFormatList_ApplicationVndOpenXmlFormatsOfficedocumentSpreadsheetmlSheet(self):
    """Test allowed conversion format for application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"""
    self.assertEqual(
      sorted(Handler.getAllowedConversionFormatList("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;ignored=param")),
      [ ('application/pdf', 'PDF - Portable Document Format'),
        ('application/vnd.ms-excel', 'Excel 97–2003'),
        ('application/vnd.ms-excel.sheet.macroEnabled.12', 'Excel 2007–365 (macro-enabled)'),
        ('application/vnd.oasis.opendocument.spreadsheet', 'ODF Spreadsheet'),
        ('application/vnd.oasis.opendocument.spreadsheet-flat-xml', 'Flat XML ODF Spreadsheet'),
        ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'Excel 2007–365'),
        ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'Office Open XML Spreadsheet'),
        ('image/jpeg', 'JPEG - Joint Photographic Experts Group'),
        ('image/png', 'PNG - Portable Network Graphics'),
        ('image/webp', 'WEBP - WebP Image'),
        ('text/csv', 'Text CSV'),
        ('text/html', 'HTML Document (Calc)') ])

  def testGetAllowedConversionFormatList_ApplicationVndSunXmlWriter(self):
    """Test allowed conversion format for application/vnd.sun.xml.writer"""
    self.assertEqual(
      sorted(Handler.getAllowedConversionFormatList("application/vnd.sun.xml.writer;ignored=param")),
      [ ('application/epub+zip', 'EPUB Document'),
        ('application/msword', 'Word 97–2003'),
        ('application/pdf', 'PDF - Portable Document Format'),
        ('application/rtf', 'Rich Text'),
        ('application/vnd.ms-word.document.macroEnabled.12', 'Word 2007 VBA'),
        ('application/vnd.oasis.opendocument.text', 'ODF Text Document'),
        ('application/vnd.oasis.opendocument.text-flat-xml', 'Flat XML ODF Text Document'),
        ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'Word 2007'),
        ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'Word 2010–365 Document'),
        ('image/jpeg', 'JPEG - Joint Photographic Experts Group'),
        ('image/png', 'PNG - Portable Network Graphics'),
        ('image/webp', 'WEBP - WebP Image'),
        ('text/html', 'HTML Document (Writer)'),
        ('text/plain', 'Text - Choose Encoding') ])

  def testGetAllowedConversionFormatList_TextCsv(self):
    """Test allowed conversion format for text/csv"""
    self.assertEqual(
      sorted(Handler.getAllowedConversionFormatList("text/csv;ignored=param")),
      [ ('application/epub+zip', 'EPUB Document'),
        ('application/msword', 'Word 97–2003'),
        ('application/pdf', 'PDF - Portable Document Format'),
        ('application/rtf', 'Rich Text'),
        ('application/vnd.ms-excel', 'Excel 97–2003'),
        ('application/vnd.ms-excel.sheet.macroEnabled.12', 'Excel 2007–365 (macro-enabled)'),
        ('application/vnd.ms-word.document.macroEnabled.12', 'Word 2007 VBA'),
        ('application/vnd.oasis.opendocument.spreadsheet', 'ODF Spreadsheet'),
        ('application/vnd.oasis.opendocument.spreadsheet-flat-xml', 'Flat XML ODF Spreadsheet'),
        ('application/vnd.oasis.opendocument.text', 'ODF Text Document'),
        ('application/vnd.oasis.opendocument.text', 'Text (Writer/Web)'),
        ('application/vnd.oasis.opendocument.text-flat-xml', 'Flat XML ODF Text Document'),
        ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'Excel 2007–365'),
        ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'Office Open XML Spreadsheet'),
        ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'Word 2007'),
        ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'Word 2010–365 Document'),
        ('application/vnd.sun.xml.writer', 'OpenOffice.org 1.0 Text Document (Writer/Web)'),
        ('image/jpeg', 'JPEG - Joint Photographic Experts Group'),
        ('image/png', 'PNG - Portable Network Graphics'),
        ('image/webp', 'WEBP - WebP Image'),
        ('text/csv', 'Text CSV'),
        ('text/html', 'HTML Document'),
        ('text/html', 'HTML Document (Calc)'),
        ('text/html', 'HTML Document (Writer)'),
        ('text/plain', 'Text (Writer/Web)'),
        ('text/plain', 'Text - Choose Encoding'),
        ('text/plain', 'Text - Choose Encoding (Writer/Web)') ])

  def testGetAllowedConversionFormatList_ApplicationVndOasisOpendocumentPresentation(self):
    """Test allowed conversion format for application/vnd.oasis.opendocument.presentation"""
    self.assertEqual(
      sorted(Handler.getAllowedConversionFormatList("application/vnd.oasis.opendocument.presentation;ignored=param")),
      [ ('application/pdf', 'PDF - Portable Document Format'),
        ('application/postscript', 'EPS - Encapsulated PostScript'),
        ('application/vnd.ms-powerpoint', 'PowerPoint 97–2003'),
        ('application/vnd.ms-powerpoint', 'PowerPoint 97–2003 AutoPlay'),
        ('application/vnd.ms-powerpoint.presentation.macroEnabled.12', 'PowerPoint 2007–365 VBA'),
        ('application/vnd.oasis.opendocument.presentation', 'ODF Presentation'),
        ('application/vnd.oasis.opendocument.presentation-flat-xml', 'Flat XML ODF Presentation'),
        ('application/vnd.openxmlformats-officedocument.presentationml.presentation', 'Office Open XML Presentation'),
        ('application/vnd.openxmlformats-officedocument.presentationml.presentation', 'PowerPoint 2007–365'),
        ('application/vnd.openxmlformats-officedocument.presentationml.slideshow', 'Office Open XML Presentation AutoPlay'),
        ('application/vnd.openxmlformats-officedocument.presentationml.slideshow', 'PowerPoint 2007–365 AutoPlay'),
        ('image/emf', 'EMF - Enhanced Metafile'),
        ('image/gif', 'GIF - Graphics Interchange Format'),
        ('image/jpeg', 'JPEG - Joint Photographic Experts Group'),
        ('image/png', 'PNG - Portable Network Graphics'),
        ('image/svg+xml', 'SVG - Scalable Vector Graphics'),
        ('image/tiff', 'TIFF - Tagged Image File Format'),
        ('image/webp', 'WEBP - WebP Image'),
        ('image/wmf', 'WMF - Windows Metafile'),
        ('image/x-ms-bmp', 'BMP - Windows Bitmap'),
        ('text/html', 'HTML Document (Impress)') ])

  def testGetAllowedConversionFormatList_ApplicationVndOpenxmlformatsOfficedocumentPresentationmlPresentation(self):
    """Test allowed conversion format for application/vnd.openxmlformats-officedocument.presentationml.presentation"""
    self.assertEqual(
      sorted(Handler.getAllowedConversionFormatList("application/vnd.openxmlformats-officedocument.presentationml.presentation;ignored=param")),
      [ ('application/pdf', 'PDF - Portable Document Format'),
        ('application/postscript', 'EPS - Encapsulated PostScript'),
        ('application/vnd.ms-powerpoint', 'PowerPoint 97–2003'),
        ('application/vnd.ms-powerpoint', 'PowerPoint 97–2003 AutoPlay'),
        ('application/vnd.ms-powerpoint.presentation.macroEnabled.12', 'PowerPoint 2007–365 VBA'),
        ('application/vnd.oasis.opendocument.presentation', 'ODF Presentation'),
        ('application/vnd.oasis.opendocument.presentation-flat-xml', 'Flat XML ODF Presentation'),
        ('application/vnd.openxmlformats-officedocument.presentationml.presentation', 'Office Open XML Presentation'),
        ('application/vnd.openxmlformats-officedocument.presentationml.presentation', 'PowerPoint 2007–365'),
        ('application/vnd.openxmlformats-officedocument.presentationml.slideshow', 'Office Open XML Presentation AutoPlay'),
        ('application/vnd.openxmlformats-officedocument.presentationml.slideshow', 'PowerPoint 2007–365 AutoPlay'),
        ('image/emf', 'EMF - Enhanced Metafile'),
        ('image/gif', 'GIF - Graphics Interchange Format'),
        ('image/jpeg', 'JPEG - Joint Photographic Experts Group'),
        ('image/png', 'PNG - Portable Network Graphics'),
        ('image/svg+xml', 'SVG - Scalable Vector Graphics'),
        ('image/tiff', 'TIFF - Tagged Image File Format'),
        ('image/webp', 'WEBP - WebP Image'),
        ('image/wmf', 'WMF - Windows Metafile'),
        ('image/x-ms-bmp', 'BMP - Windows Bitmap'),
        ('text/html', 'HTML Document (Impress)') ])

  def testGetAllowedConversionFormatList_ApplicationVndOpenxmlformatsOfficedocumentPresentationmlSlideshow(self):
    """Test allowed conversion format for application/vnd.openxmlformats-officedocument.presentationml.slideshow"""
    self.assertEqual(
      sorted(Handler.getAllowedConversionFormatList("application/vnd.openxmlformats-officedocument.presentationml.slideshow;ignored=param")),
      [ ('application/pdf', 'PDF - Portable Document Format'),
        ('application/postscript', 'EPS - Encapsulated PostScript'),
        ('application/vnd.ms-powerpoint', 'PowerPoint 97–2003'),
        ('application/vnd.ms-powerpoint', 'PowerPoint 97–2003 AutoPlay'),
        ('application/vnd.ms-powerpoint.presentation.macroEnabled.12', 'PowerPoint 2007–365 VBA'),
        ('application/vnd.oasis.opendocument.presentation', 'ODF Presentation'),
        ('application/vnd.oasis.opendocument.presentation-flat-xml', 'Flat XML ODF Presentation'),
        ('application/vnd.openxmlformats-officedocument.presentationml.presentation', 'Office Open XML Presentation'),
        ('application/vnd.openxmlformats-officedocument.presentationml.presentation', 'PowerPoint 2007–365'),
        ('application/vnd.openxmlformats-officedocument.presentationml.slideshow', 'Office Open XML Presentation AutoPlay'),
        ('application/vnd.openxmlformats-officedocument.presentationml.slideshow', 'PowerPoint 2007–365 AutoPlay'),
        ('image/emf', 'EMF - Enhanced Metafile'),
        ('image/gif', 'GIF - Graphics Interchange Format'),
        ('image/jpeg', 'JPEG - Joint Photographic Experts Group'),
        ('image/png', 'PNG - Portable Network Graphics'),
        ('image/svg+xml', 'SVG - Scalable Vector Graphics'),
        ('image/tiff', 'TIFF - Tagged Image File Format'),
        ('image/webp', 'WEBP - WebP Image'),
        ('image/wmf', 'WMF - Windows Metafile'),
        ('image/x-ms-bmp', 'BMP - Windows Bitmap'),
        ('text/html', 'HTML Document (Impress)') ])

  def testGetAllowedConversionFormatList_ApplicationVndMsPowerpoint(self):
    """Test allowed conversion format for application/vnd.ms-powerpoint"""
    self.assertEqual(
      sorted(Handler.getAllowedConversionFormatList("application/vnd.ms-powerpoint;ignored=param")),
      [ ('application/pdf', 'PDF - Portable Document Format'),
        ('application/postscript', 'EPS - Encapsulated PostScript'),
        ('application/vnd.ms-powerpoint', 'PowerPoint 97–2003'),
        ('application/vnd.ms-powerpoint', 'PowerPoint 97–2003 AutoPlay'),
        ('application/vnd.ms-powerpoint.presentation.macroEnabled.12', 'PowerPoint 2007–365 VBA'),
        ('application/vnd.oasis.opendocument.presentation', 'ODF Presentation'),
        ('application/vnd.oasis.opendocument.presentation-flat-xml', 'Flat XML ODF Presentation'),
        ('application/vnd.openxmlformats-officedocument.presentationml.presentation', 'Office Open XML Presentation'),
        ('application/vnd.openxmlformats-officedocument.presentationml.presentation', 'PowerPoint 2007–365'),
        ('application/vnd.openxmlformats-officedocument.presentationml.slideshow', 'Office Open XML Presentation AutoPlay'),
        ('application/vnd.openxmlformats-officedocument.presentationml.slideshow', 'PowerPoint 2007–365 AutoPlay'),
        ('image/emf', 'EMF - Enhanced Metafile'),
        ('image/gif', 'GIF - Graphics Interchange Format'),
        ('image/jpeg', 'JPEG - Joint Photographic Experts Group'),
        ('image/png', 'PNG - Portable Network Graphics'),
        ('image/svg+xml', 'SVG - Scalable Vector Graphics'),
        ('image/tiff', 'TIFF - Tagged Image File Format'),
        ('image/webp', 'WEBP - WebP Image'),
        ('image/wmf', 'WMF - Windows Metafile'),
        ('image/x-ms-bmp', 'BMP - Windows Bitmap'),
        ('text/html', 'HTML Document (Impress)') ])
