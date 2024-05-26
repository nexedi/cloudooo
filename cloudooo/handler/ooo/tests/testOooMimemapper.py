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

from cloudooo.tests.handlerTestCase import HandlerTestCase
from cloudooo.handler.ooo.application.openoffice import openoffice
from cloudooo.handler.ooo.mimemapper import MimeMapper

# XXX depending on wether allowed targets are evaluated by mime or by
# extension/document_type, the returned mime types are different for text
text_expected_tuple = (
    ('doc', 'Word 97–2003'),
    ('docx', 'Word 2010–365 Document'),
    ('epub', 'EPUB Document'),
    ('fodt', 'Flat XML ODF Text Document'),
    ('html', 'HTML Document (Writer)'),
    ('jpg', 'JPEG - Joint Photographic Experts Group'),
    ('ms.docx', 'Word 2007'),
    ('odt', 'ODF Text Document'),
    ('pdf', 'PDF - Portable Document Format'),
    ('png', 'PNG - Portable Network Graphics'),
    ('rtf', 'Rich Text'),
    ('txt', 'Text - Choose Encoding'),
    ('webp', 'WEBP - WebP Image'),
    )
extra_text_expected_tuple = (
    ('docm', 'Word 2007 VBA'),
    )

global_expected_tuple = (
    )

drawing_expected_tuple = (
    ('apng', 'APNG - Animated Portable Network Graphics'),
    ('bmp', 'BMP - Windows Bitmap'),
    ('emf', 'EMF - Enhanced Metafile'),
    ('emz', 'EMZ - Compressed Enhanced Metafile'),
    ('eps', 'EPS - Encapsulated PostScript'),
    ('fodg', 'Flat XML ODF Drawing'),
    ('gif', 'GIF - Graphics Interchange Format'),
    ('html', 'HTML Document (Draw)'),
    ('jpg', 'JPEG - Joint Photographic Experts Group'),
    ('odg', 'ODF Drawing'),
    ('pdf', 'PDF - Portable Document Format'),
    ('png', 'PNG - Portable Network Graphics'),
    ('svg', 'SVG - Scalable Vector Graphics'),
    ('svgz', 'SVGZ - Compressed Scalable Vector Graphics'),
    ('tiff', 'TIFF - Tagged Image File Format'),
    ('webp', 'WEBP - WebP Image'),
    ('wmf', 'WMF - Windows Metafile'),
    ('wmz', 'WMZ - Compressed Windows Metafile'),
    )

web_expected_tuple = (
    ('html', 'HTML Document'),
    ('odt', 'Text (Writer/Web)'),
    ('pdf', 'PDF - Portable Document Format'),
    ('sxw', 'OpenOffice.org 1.0 Text Document (Writer/Web)'),
    ('txt', 'Text (Writer/Web)'),
    ('txt', 'Text - Choose Encoding (Writer/Web)'),
    )

presentation_expected_tuple = (
    ('bmp', 'BMP - Windows Bitmap'),
    ('emf', 'EMF - Enhanced Metafile'),
    ('eps', 'EPS - Encapsulated PostScript'),
    ('fodp', 'Flat XML ODF Presentation'),
    ('gif', 'GIF - Graphics Interchange Format'),
    ('html', 'HTML Document (Impress)'),
    ('jpg', 'JPEG - Joint Photographic Experts Group'),
    ('odp', 'ODF Presentation'),
    ('pdf', 'PDF - Portable Document Format'),
    ('png', 'PNG - Portable Network Graphics'),
    ('pps', 'PowerPoint 97–2003 AutoPlay'),
    ('ppsx', 'Office Open XML Presentation AutoPlay'),
    ('ppsx', 'PowerPoint 2007–365 AutoPlay'),
    ('ppt', 'PowerPoint 97–2003'),
    ('pptm', 'PowerPoint 2007–365 VBA'),
    ('pptx', 'Office Open XML Presentation'),
    ('pptx', 'PowerPoint 2007–365'),
    ('svg', 'SVG - Scalable Vector Graphics'),
    ('tiff', 'TIFF - Tagged Image File Format'),
    ('webp', 'WEBP - WebP Image'),
    ('wmf', 'WMF - Windows Metafile'),
    )

spreadsheet_expected_tuple = (
    ('csv', 'Text CSV'),
    ('fods', 'Flat XML ODF Spreadsheet'),
    ('html', 'HTML Document (Calc)'),
    ('jpg', 'JPEG - Joint Photographic Experts Group'),
    ('ods', 'ODF Spreadsheet'),
    ('pdf', 'PDF - Portable Document Format'),
    ('png', 'PNG - Portable Network Graphics'),
    ('slk', 'SYLK'),
    ('webp', 'WEBP - WebP Image'),
    ('xls', 'Excel 97–2003'),
    ('ms.xlsx', 'Excel 2007–365'),
    ('xlsm', 'Excel 2007–365 (macro-enabled)'),
    ('xlsx', 'Office Open XML Spreadsheet'),
    )

math_expected_tuple = (
    ('mml', 'MathML 1.01'),
    ('odf', 'ODF Formula'),
    ('pdf', 'PDF - Portable Document Format'),
    ('smf', 'StarMath 3.0'),
    ('smf', 'StarMath 4.0'),
    ('smf', 'StarMath 5.0'),
    )


OPENOFFICE = True


class TestMimeMapper(HandlerTestCase):
  """Test if object load filters correctly of OOo."""

  def afterSetUp(self):
    """Mimemapper is created and load uno path."""
    self.mimemapper = MimeMapper()
    openoffice.acquire()
    hostname, port = openoffice.getAddress()
    self.mimemapper.loadFilterList(hostname,
                                  port,
                                  python_path=self.python_path)
    openoffice.release()

  def testGetFilterWhenExtensionNotExist(self):
    """Test the case that the user passes extension which does not exist."""
    empty_list = self.mimemapper.getFilterList('xxx')
    self.assertEqual(empty_list, [])

  def testIfThereIsDuplicateData(self):
    """Test if there is duplicate data."""
    # XXX It can not exists multiple keys inside a dictionary
    extension_list = list(self.mimemapper._doc_type_list_by_extension.keys())
    self.assertEqual(len(extension_list), len(set(extension_list)))
    for type_list in list(self.mimemapper._doc_type_list_by_extension.values()):
      self.assertEqual(len(type_list), len(set(type_list)))
    document_type_list = list(self.mimemapper._document_type_dict.keys())
    self.assertEqual(len(document_type_list), len(set(document_type_list)))
    document_service_list = list(self.mimemapper._document_type_dict.values())
    self.assertEqual(len(document_service_list), len(set(document_service_list)))
    document_service_list = list(self.mimemapper._extension_list_by_type.keys())
    self.assertEqual(len(document_service_list), len(set(document_service_list)))
    extension_list = list(self.mimemapper._extension_list_by_type.values())
    for extension in extension_list:
      self.assertEqual(len(extension), len(set(extension)),
          "extension_list_by_type has duplicate data")

  def testGetFilterByExt(self):
    """Test if passing the extension the filter returns corretcly."""
    pdf_filter_list = self.mimemapper.getFilterList('pdf')
    self.assertEqual(len(pdf_filter_list), 5)
    xls_filter_list = self.mimemapper.getFilterList('xls')
    self.assertEqual(len(xls_filter_list), 1)
    doc_filter_list = self.mimemapper.getFilterList('doc')
    self.assertEqual(len(doc_filter_list), 1)

  def testGetDocumentTypeDict(self):
    """Test if dictonary document type returns type correctly."""
    document_type_dict = self.mimemapper._document_type_dict
    type = document_type_dict.get("text")
    self.assertEqual(type, 'com.sun.star.text.TextDocument')
    type = document_type_dict.get("drawing")
    self.assertEqual(type, 'com.sun.star.drawing.DrawingDocument')
    type = document_type_dict.get("presentation")
    self.assertEqual(type, 'com.sun.star.presentation.PresentationDocument')
    type = document_type_dict.get("spreadsheet")
    self.assertEqual(type, 'com.sun.star.sheet.SpreadsheetDocument')
    type = document_type_dict.get("web")
    self.assertEqual(type, 'com.sun.star.text.WebDocument')

  def testGetAllowedExtensionListByExtension(self):
    """Test if function getAllowedExtensionList returns correctly a list with
    extensions that can generate with extension passed."""
    doc_got_list = list(self.mimemapper.getAllowedExtensionList('doc'))
    _text_expected_tuple = text_expected_tuple + extra_text_expected_tuple
    for arg in doc_got_list:
      self.assertIn(arg, _text_expected_tuple)
    jpeg_got_list = list(self.mimemapper.getAllowedExtensionList('jpeg'))
    jpeg_expected_list = list(set(presentation_expected_tuple +
        drawing_expected_tuple))
    for arg in jpeg_got_list:
      self.assertIn(arg, jpeg_expected_list)
    pdf_got_list = list(self.mimemapper.getAllowedExtensionList('pdf'))
    pdf_expected_list = list(set(presentation_expected_tuple +
      drawing_expected_tuple + web_expected_tuple + global_expected_tuple +
      math_expected_tuple + _text_expected_tuple + spreadsheet_expected_tuple))
    for arg in pdf_got_list:
      self.assertIn(arg, pdf_expected_list)

  def testGetAllowedExtensionListForText(self):
    """Passing document_type equal to 'text', the return must be equal
    to text_expected_tuple."""
    self.assertEqual(
      sorted(self.mimemapper.getAllowedExtensionList(document_type='text')),
      sorted(text_expected_tuple + extra_text_expected_tuple)
    )

  def testGetAllowedExtensionListForGlobal(self):
    """Passing document_type equal to 'global', the return must be equal
    to global_expected_tuple."""
    self.assertEqual(
      sorted(self.mimemapper.getAllowedExtensionList(document_type='global')),
      sorted(global_expected_tuple)
    )

  def testGetAllAllowedExtensionListForDrawing(self):
    """Passing document_type equal to 'drawing', the return must be equal
    to drawing_expected_tuple."""
    self.assertEqual(
      sorted(self.mimemapper.getAllowedExtensionList(document_type='drawing')),
      sorted(drawing_expected_tuple)
    )

  def testGetAllAllowedExtensionListForWeb(self):
    """Passing document_type equal to 'web', the return must be equal
    to web_expected_tuple."""
    self.assertEqual(
      sorted(self.mimemapper.getAllowedExtensionList(document_type='web')),
      sorted(web_expected_tuple)
    )

  def testGetAllAllowedExtensionListForPresentation(self):
    """Passing document_type equal to 'presentation', the return must be equal
    to presentation_expected_tuple."""
    self.assertEqual(
      sorted(self.mimemapper.getAllowedExtensionList(document_type='presentation')),
      sorted(presentation_expected_tuple)
    )

  def testGetAllAllowedExtensionListForSpreadsheet(self):
    """Passing document_type equal to 'spreadsheet', the return must be equal
    to spreadsheet_expected_tuple."""
    self.assertEqual(
      sorted(self.mimemapper.getAllowedExtensionList(document_type='spreadsheet')),
      sorted(spreadsheet_expected_tuple)
    )

  def testGetFilterName(self):
    """Test if passing extension and document_type, the filter is correct."""
    filtername = self.mimemapper.getFilterName("xls",
                                            'com.sun.star.sheet.SpreadsheetDocument')
    self.assertEqual(filtername, "MS Excel 97")
    filtername = self.mimemapper.getFilterName("pdf",
                                            'com.sun.star.text.TextDocument')
    self.assertEqual(filtername, "writer_pdf_Export")
    filtername = self.mimemapper.getFilterName('ppt',
                             'com.sun.star.presentation.PresentationDocument')
    self.assertEqual(filtername, "MS PowerPoint 97")
    filtername = self.mimemapper.getFilterName("html",
                             'com.sun.star.presentation.PresentationDocument')
    self.assertEqual(filtername, "impress_html_Export")


