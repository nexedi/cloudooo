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

from os.path import join, exists
from os import remove
from base64 import encodebytes, decodebytes
from io import BytesIO
from lxml import etree
from zipfile import ZipFile, is_zipfile
from cloudooo.tests.cloudoooTestCase import TestCase
from unittest import expectedFailure
import magic
import xmlrpc.client
from cloudooo.handler.ooo.tests.testOooMimemapper import text_expected_tuple, presentation_expected_tuple


"""Tests for XmlRpc Server. Needs cloudooo server started"""

class TestAllowedExtensions(TestCase):

  def testGetAllowedTextExtensionListByType(self):
    """Verify if getAllowedExtensionList returns is a list with extension and
    ui_name. The request is by document type as text"""
    text_request = {'document_type': "text"}
    text_allowed_list = self.proxy.getAllowedExtensionList(text_request)
    # XXX slightly different allowed formats with document_type !?
    _text_expected_tuple = text_expected_tuple + (
      ('docm', 'Word 2007 VBA'),
    )
    self.assertEqual(
      sorted([tuple(x) for x in text_allowed_list]),
      sorted(_text_expected_tuple))

  def testGetAllowedPresentationExtensionListByType(self):
    """Verify if getAllowedExtensionList returns is a list with extension and
    ui_name. The request is by document type as presentation"""
    request_dict = {'document_type': "presentation"}
    presentation_allowed_list = self.proxy.getAllowedExtensionList(request_dict)
    self.assertTrue(presentation_allowed_list)
    self.assertEqual(
        sorted([tuple(x) for x in presentation_allowed_list]),
        sorted(presentation_expected_tuple))

  def testGetAllowedExtensionListByExtension(self):
    """Verify if getAllowedExtensionList returns is a list with extension and
    ui_name. The request is by extension"""
    doc_allowed_list = self.proxy.getAllowedExtensionList({'extension': "doc"})
    self.assertEqual(
      sorted([tuple(x) for x in doc_allowed_list]),
      sorted(text_expected_tuple))

  def testGetAllowedExtensionListByMimetype(self):
    """Verify if getAllowedExtensionList returns is a list with extension and
    ui_name. The request is by mimetype"""
    request_dict = {"mimetype": "application/msword"}
    msword_allowed_list = self.proxy.getAllowedExtensionList(request_dict)
    self.assertEqual(sorted([tuple(x) for x in msword_allowed_list]), sorted(text_expected_tuple))


class TestConversion(TestCase):
  """Test that conversion of some test documents to various destination format does not fail.
  """
  def ConversionScenarioList(self):
    return [
            # Test Convert Doc -> Odt
            (join('data', 'test.doc'), "doc", "odt", "application/vnd.oasis."+
            "opendocument.text"),
            # Test export png to svg
            (join('data', 'test.png'), "png", "svg", "image/svg+xml"),
            # Test export docx to odt
            (join('data', 'test.docx'), "docx", "odt", "application/vnd.oasis."+
            "opendocument.text"),
            # Test export python to pdf
            (__file__, "txt", "pdf", "application/pdf"),
            ]

  def testConvert(self):
    """Test convertion of OOofiles"""
    self.runConversionList(self.ConversionScenarioList())

  def FaultConversionScenarioList(self):
    scenario_list = [
      # Test to verify if server fail when a empty file is sent
      (b'', '', ''),
    ]
    # Try convert one document to an invalid format
    with open(join('data', 'test.doc'), 'rb') as f:
      scenario_list.append((f.read(), 'doc', 'xyz'))
    # Try convert one video to format not possible
    with open(join('data', 'test.odp'), 'rb') as f:
      scenario_list.append((f.read(), 'odp', 'doc'))
    return scenario_list

  def testFaultConversion(self):
    """Test fail convertion of Invalid OOofiles"""
    self.runFaultConversionList(self.FaultConversionScenarioList())

  # Expected failure cause zip and pptx files are not supported
  @expectedFailure
  def testConvertWithoutSupport(self):
    """Test convertion of zip files and pptx"""
    self.runConversionList([
            # Test if send a zipfile returns a document correctly
            (join('data', 'test.zip'), "zip", "txt", "application/zip", True),
            # Convert compressed html to txt
            (join('data', 'test.zip'), "zip", "txt", "text/plain"),
            # Test export pptx to odp
            (join('data', 'test.pptx'), "pptx", "odp", "application/vnd.oasis."+
            "opendocument.presentation"),
            ])

  def ConvertScenarioList(self):
    scenario_list = []
    # Test run_convert method
    with open(join('data', 'test.doc'), 'rb') as f:
      scenario_list.append(
        ('test.doc', f.read(), 200, '',
        ['data', 'meta', 'mime'], '', 'application/vnd.oasis.opendocument.text'
      ))
    # Test run_convert method with invalid file
    with open(join('data', 'test.doc'), 'rb') as f:
      scenario_list.append(
        ('test.doc', f.read()[:-300], 402, '',
        ['data', 'meta', 'mime'], '', 'application/vnd.oasis.opendocument.text'
      ))
    return scenario_list

  def testRunConvertMethod(self):
    """Test run_convert method"""
    self.runConvertScenarioList(self.ConvertScenarioList())


class TestGetMetadata(TestCase):
  def GetMetadataScenarioList(self):
    return [
            # Test method getFileMetadataItemList. Without data converted
            (join('data', 'testMetadata.odt'), "odt", dict(Data='', Title='clo'+
            'udooo Test', Subject='Subject Test', Description='cloudooo Comments',
            Type='Text', MIMEType='application/vnd.oasis.opendocument.text',
            Keywords=['Keywords Test'])),
            # Test method getFileMetadataItemList. With data converted
            (join('data', 'testMetadata.odt'), "odt", dict(Title='cloudooo Test',
            Subject='Subject Test', Description='cloudooo Comments',
            Type='Text', MIMEType='application/vnd.oasis.opendocument.text',
            Keywords=['Keywords Test']),
            True),
            ]

  def testGetMetadata(self):
    """test if OOo metadata are extracted correctly"""
    self.runGetMetadataList(self.GetMetadataScenarioList())

  def FaultGetMetadataScenarioList(self):
    return [
            # Test to verify if server fail when a empty string is sent
            ('', ''),
            ]

  def testFaultGetMetadata(self):
    """Test getMetadata from invalid OOofiles"""
    self.runFaultGetMetadataList(self.FaultGetMetadataScenarioList())

  def UpdateMetadataScenarioList(self):
    return [
            # Test server using method updateFileMetadata
            (join('data', 'testMetadata.odt'), "odt", dict(Title='testSetMetadata')),
            # Test server using method updateFileMetadata with unsual metadata
            (join('data', 'testMetadata.odt'), "odt", dict(Reference='testSet'+
            'Metadata')),
            # Test document that already has metadata. Check if the metadata is
            # not deleted, but updated
            (join('data', 'testMetadata.odt'), "odt", dict(Title='cloudooo Title')),
            ]

  def testUpdateMetadata(self):
    """test if OOo metadata are insert correctly"""
    self.runUpdateMetadataList(self.UpdateMetadataScenarioList())

  def testupdateFileMetadataUpdateSomeMetadata(self):
    """Test server using method updateFileMetadata when the same metadata is
    updated"""
    with open(join('data', 'testMetadata.odt'), 'rb') as f:
      data = f.read()
    odf_data = self.proxy.updateFileMetadata(
                encodebytes(data).decode(),
                'odt',
                dict(Reference="testSetMetadata", Something="ABC"))
    new_odf_data = self.proxy.updateFileMetadata(odf_data,
                    'odt',
                    dict(Reference="new value", Something="ABC"))
    self.assertEqual(self._getFileType(new_odf_data), 
                      'application/vnd.oasis.opendocument.text')
    metadata_dict = self.proxy.getFileMetadataItemList(new_odf_data, 'odt')
    self.assertEqual(metadata_dict.get("Reference"), "new value")
    self.assertEqual(metadata_dict.get("Something"), "ABC")


  # XXX: This is a test for ERP5 Backward compatibility,
  # and the support to this kind of tests will be dropped.
  def testRunGenerateMethod(self):
    """Test run_generate method"""
    with open(join('data', 'test.odt'), 'rb') as f:
      data = f.read()
    generate_result = self.proxy.run_generate('test.odt',
                                      encodebytes(data).decode(),
                                      None, 'pdf',
                                      'application/vnd.oasis.opendocument.text')
    response_code, response_dict, response_message = generate_result
    self.assertEqual(response_code, 200)
    self.assertIsInstance(response_dict, dict)
    self.assertNotEqual(response_dict['data'], '')
    self.assertEqual(response_dict['mime'], 'application/pdf')


class TestGenerate(TestCase):
  # XXX: This is a test for ERP5 Backward compatibility,
  # and the support to this kind of tests will be dropped.
  def testRunGenerateMethodConvertOdsToHTML(self):
    """Test run_generate method from ods to html. This test is to validate
     a bug convertions to html"""
    with open(join('data', 'test.ods'), 'rb') as f:
      data = f.read()
    generate_result = self.proxy.run_generate('test.ods',
                                      encodebytes(data).decode(),
                                      None, 'html',
                                      "application/vnd.oasis.opendocument.spreadsheet")
    response_code, response_dict, response_message = generate_result
    self.assertEqual(response_code, 200)
    self.assertIsInstance(response_dict, dict)
    self.assertNotEqual(response_dict['data'], '')
    self.assertEqual(response_dict['mime'], 'application/zip')
    output_url = join(self.tmp_url, "zip.zip")
    with open(output_url, 'wb') as f:
      f.write(decodebytes(response_dict['data'].encode()))
    self.assertTrue(is_zipfile(output_url))
    filename_list = [file.filename for file in ZipFile(output_url).filelist]
    for filename in filename_list:
      if filename.endswith("impr.html"):
        break
    else:
      self.fail("Not exists one file with 'impr.html' format")
    if exists(output_url):
      remove(output_url)

  def testRunGenerateMethodConvertOdsToMsXslx(self):
    """Test run_generate method from ods to ms.xlsx. This test is to validate
     a bug convertions to html"""
    with open(join('data', 'test.ods'), 'rb') as f:
      data = f.read()
    generate_result = self.proxy.run_generate('test.ods',
                                      encodebytes(data).decode(),
                                      None, 'ms.xlsx',
                                      "application/vnd.oasis.opendocument.spreadsheet")
    response_code, response_dict, response_message = generate_result
    self.assertEqual(response_code, 200)
    self.assertIsInstance(response_dict, dict)
    self.assertNotEqual(response_dict['data'], '')
    self.assertEqual(response_dict['mime'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

  # XXX: This is a test for ERP5 Backward compatibility,
  # and the support to this kind of tests will be dropped.
  def testPNGFileToConvertOdpToHTML(self):
    """Test run_generate method from odp with png to html.
     This test if returns good png files"""
    with open(join('data', 'test_png.odp'), 'rb') as f:
      data = f.read()
    generate_result = self.proxy.run_generate('test_png.odp',
                                      encodebytes(data).decode(),
                                      None, 'html',
                                      'application/vnd.oasis.opendocument.presentation')
    response_code, response_dict, response_message = generate_result
    self.assertEqual(response_code, 200)
    self.assertIsInstance(response_dict, dict)
    self.assertNotEqual(response_dict['data'], '')
    self.assertEqual(response_dict['mime'], 'application/zip')
    output_url = join(self.tmp_url, "zip.zip")
    with open(output_url, 'wb') as f:
      f.write(decodebytes(response_dict['data'].encode()))
    self.assertTrue(is_zipfile(output_url))
    with ZipFile(output_url) as zipfile:
      png_path = join(self.tmp_url, "img0.png")
      zipfile.extractall(self.tmp_url)
      with open(png_path, 'rb') as f:
        content_type = self._getFileType(encodebytes(f.read()).decode())
      self.assertEqual(content_type, 'image/png')
      m = magic.Magic()
      self.assertIn("8-bit/color RGB", m.from_file(png_path))
    if exists(output_url):
      remove(output_url)

  # XXX: This is a test for ERP5 Backward compatibility,
  # and the support to this kind of tests will be dropped.
  def testRunGenerateMethodConvertOdpToHTML(self):
    """Test run_generate method from odp to html. This test is to validate
     a bug convertions to html"""
    with open(join('data', 'test.odp'), 'rb') as f:
      data = f.read()
    generate_result = self.proxy.run_generate('test.odp',
                                      encodebytes(data).decode(),
                                      None, 'html',
                                      'application/vnd.oasis.opendocument.presentation')
    response_code, response_dict, response_message = generate_result
    self.assertEqual(response_code, 200)
    self.assertIsInstance(response_dict, dict)
    self.assertNotEqual(response_dict['data'], '')
    self.assertEqual(response_dict['mime'], 'application/zip')
    output_url = join(self.tmp_url, "zip.zip")
    with open(output_url, 'wb') as f:
      f.write(decodebytes(response_dict['data'].encode()))
    self.assertTrue(is_zipfile(output_url))
    filename_list = [file.filename for file in ZipFile(output_url).filelist]
    for filename in filename_list:
      if filename.endswith("impr.html"):
        break
    else:
      self.fail("Not exists one file with 'impr.html' format")
    if exists(output_url):
      remove(output_url)

  # XXX: This is a test for ERP5 Backward compatibility,
  # and the support to this kind of tests will be dropped.
  # XXX LibreOffice 3.3 can open such a broken document and convert
  @expectedFailure
  def testRunGenerateMethodFailResponse(self):
    """Test run_generate method with invalid document"""
    with open(join('data', 'test.odt')) as f:
      data = f.read()[:100]
    generate_result = self.proxy.run_generate('test.odt',
                                      encodebytes(data).decode(),
                                      None, 'pdf', 'application/vnd.oasis.opendocument.text')
    response_code, response_dict, response_message = generate_result
    self.assertEqual(response_code, 402)
    self.assertIsInstance(response_dict, dict)
    self.assertEqual(response_dict, {})
    self.assertTrue(response_message.startswith('Traceback'))


class TestSetMetadata(TestCase):
  def testRunSetMetadata(self):
    """Test run_setmetadata method, updating the same metadata"""
    with open(join('data', 'testMetadata.odt'), 'rb') as f:
      data = f.read()
    setmetadata_result = self.proxy.run_setmetadata('testMetadata.odt',
                          encodebytes(data).decode(),
                          {"Title": "testSetMetadata", "Description": "Music"})
    response_code, response_dict, response_message = setmetadata_result
    self.assertEqual(response_code, 200)
    new_data = response_dict['data']
    self.assertNotEqual(new_data, '')
    getmetadata_result = self.proxy.run_getmetadata('testMetadata.odt',
                                                  new_data)
    response_code, response_dict, response_message = getmetadata_result
    self.assertEqual(response_code, 200)
    self.assertEqual(response_dict['meta']['MIMEType'],
                      'application/vnd.oasis.opendocument.text')
    self.assertEqual(response_dict['meta']['Description'], "Music")
    setmetadata_result = self.proxy.run_setmetadata('testMetadata.odt',
                          new_data,
                          {"Title": "Namie's working record",
                           "Description": "Music"})
    response_code, response_dict, response_message = setmetadata_result
    getmetadata_result = self.proxy.run_getmetadata('testMetadata.odt',
                                                  response_dict['data'])
    response_code, response_dict, response_message = getmetadata_result
    self.assertEqual(response_code, 200)
    self.assertEqual(response_dict['meta']['title'],
                      "Namie's working record")

  def testRunSetMetadataFailResponse(self):
    """Test run_setmetadata method with invalid document"""
    with open(join('data', 'testMetadata.odt'), 'rb') as f:
      data = f.read()[:100]
    setmetadata_result = self.proxy.run_setmetadata('testMetadata.odt',
                          encodebytes(data).decode(),
                          {"Title": "testSetMetadata", "Description": "Music"})
    response_code, response_dict, response_message = setmetadata_result
    self.assertEqual(response_code, 402)
    self.assertEqual(response_dict, {})
    self.assertTrue(response_message.startswith('Traceback'))


class TestGetAllowedTargetItemList(TestCase):
  def testGetAllowedTargetItemList(self):
    """Test if filter name returns correctly with ERP5 API"""
    mimetype = 'application/vnd.oasis.opendocument.text'
    response_code, response_dict, response_message = \
                  self.proxy.getAllowedTargetItemList(mimetype)
    self.assertEqual(response_code, 200)
    # XXX in this test, docy is present in the allowed target extensions
    self.assertEqual(
        sorted([(extension, ui_name)
                for (extension, ui_name) in response_dict['response_data']
                if extension not in ('docy',)]),
        sorted(text_expected_tuple))


class TestGetTableItemList(TestCase):
  def testGetTableItemListFromOdt(self):
    """Test if getTableItemList can get the table item list from odt file"""
    table_list = [['Developers', ''],
                  ['Prices', 'Table 1: Prices table from Mon Restaurant'],
                  ['SoccerTeams', 'Tabela 2: Soccer Teams']]
    with open("data/granulate_table_test.odt", "rb") as f:
      data = f.read()
    granulated_table = self.proxy.getTableItemList(
                        encodebytes(data).decode(),
                        "odt")
    self.assertEqual(table_list, granulated_table)

  def testGetTableItemListFromDoc(self):
    """Test if getTableItemList can get the table item list from doc file"""
    table_list = [['Table1', ''],
                  ['Table2', 'Table 1: Prices table from Mon Restaurant'],
                  ['Table3', 'Tabela 2: Soccer Teams']]
    with open("data/granulate_table_test.doc", "rb") as f:
      data = f.read()
    granulated_table = self.proxy.getTableItemList(
                        encodebytes(data).decode(),
                        "doc")
    self.assertEqual(table_list, granulated_table)

  def testGetTableFromOdt(self):
    """Test if getTableItemList can get a item of some granulated table from odt file"""
    with open("./data/granulate_table_test.odt", "rb") as f:
      data = encodebytes(f.read()).decode()
    granulated_table = self.proxy.getTableItemList(data, "odt")
    table_item = decodebytes(self.proxy.getTable(data, granulated_table[1][0],
                                                      "odt").encode())
    content_xml_str = ZipFile(BytesIO(table_item)).read('content.xml')
    content_xml = etree.fromstring(content_xml_str)
    table_list = content_xml.xpath('//table:table',
                                   namespaces=content_xml.nsmap)
    self.assertEqual(1, len(table_list))
    table = table_list[0]
    name_key = '{urn:oasis:names:tc:opendocument:xmlns:table:1.0}name'
    self.assertEqual(granulated_table[1][0], table.attrib[name_key])

  def testGetTableFromDoc(self):
    """Test if getTableItemList can get a item of some granulated table from doc file"""
    with open("./data/granulate_table_test.odt", "rb") as f:
      data = encodebytes(f.read()).decode()
    granulated_table = self.proxy.getTableItemList(data, "doc")
    self.proxy.getTable(data, granulated_table[1][0], "doc")
    table_item = decodebytes(self.proxy.getTable(data, granulated_table[1][0],
                                                      "doc").encode())
    content_xml_str = ZipFile(BytesIO(table_item)).read('content.xml')
    content_xml = etree.fromstring(content_xml_str)
    table_list = content_xml.xpath('//table:table',
                                   namespaces=content_xml.nsmap)
    self.assertEqual(1, len(table_list))
    table = table_list[0]
    name_key = '{urn:oasis:names:tc:opendocument:xmlns:table:1.0}name'
    self.assertEqual(granulated_table[1][0], table.attrib[name_key])

  def testGetColumnItemListFromOdt(self):
    """Test if getColumnItemList can get the list of column item from odt file"""
    with open("./data/granulate_table_test.odt", "rb") as f:
      data = encodebytes(f.read()).decode()
    columns = self.proxy.getColumnItemList(
                data,
                "SoccerTeams",
                "odt")
    self.assertEqual([[0, 'Name'], [1, 'Country']], columns)

  def testGetColumnItemListFromDoc(self):
    """Test if getColumnItemList can get the list of column item from doc file"""
    with open("./data/granulate_table_test.doc", "rb") as f:
      data = encodebytes(f.read()).decode()
    #in the doc format the tables lose their names
    columns = self.proxy.getColumnItemList(
              data,
              "Table3",
              "doc")
    self.assertEqual([[0, 'Name'], [1, 'Country']], columns)

  def testGetLineItemListFromOdt(self):
    """Test if getLineItemList can get the list of lines items from odt file"""
    with open("./data/granulate_table_test.odt", "rb") as f:
      data = encodebytes(f.read()).decode()
    line_item_list = self.proxy.getLineItemList(data, "Developers", "odt")
    self.assertEqual([['Name', 'Hugo'], ['Phone', '+55 (22) 8888-8888'],
                       ['Email', 'hugomaia@tiolive.com'], ['Name', 'Rafael'],
                       ['Phone', '+55 (22) 9999-9999'],
                       ['Email', 'rafael@tiolive.com']], line_item_list)

  def testGetLineItemListFromDoc(self):
    """Test if getLineItemList can get the list of lines items from doc file"""
    with open("./data/granulate_table_test.doc", "rb") as f:
      data = encodebytes(f.read()).decode()
    line_item_list = self.proxy.getLineItemList(data, "Table1", "doc")
    self.assertEqual([['Name', 'Hugo'], ['Phone', '+55 (22) 8888-8888'],
                       ['Email', 'hugomaia@tiolive.com'], ['Name', 'Rafael'],
                       ['Phone', '+55 (22) 9999-9999'],
                       ['Email', 'rafael@tiolive.com']], line_item_list)


class TestImagetItemList(TestCase):
  def testGetImageItemListFromOdt(self):
    """Test if getImageItemList can get the list of images items from odt file"""
    with open("./data/granulate_test.odt", "rb") as f:
      data = encodebytes(f.read()).decode()
    image_list = self.proxy.getImageItemList(data, "odt")
    self.assertEqual(
      [['10000000000000C80000009C38276C51.jpg', ''],
       ['10000201000000C80000004E7B947D46.png', 'TioLive Logo'],
       ['10000201000000C80000004E7B947D46.png', ''],
       ['2000004F00004233000013707E7DE37A.svm', 'Python Logo'],
       ['10000201000000C80000004E7B947D46.png', 'Again TioLive Logo']],
       image_list)
    # the image filenames are the ones from the original document
    with open("./data/granulate_test.odt", "rb") as f:
      self.assertIn('Pictures/10000000000000C80000009C38276C51.jpg', ZipFile(f).namelist())

  def testGetImageItemListFromDoc(self):
    """Test if getImageItemList can get the list of images items from doc file"""
    with open("./data/granulate_test.doc", "rb") as f:
      data = encodebytes(f.read()).decode()
    image_list = self.proxy.getImageItemList(data, "doc")
    # the doc has been converted to odt, so the image ids are
    # not really predictable (they seem to depend on Libreoffice version)
    self.assertIn('.jpg', image_list[0][0])
    self.assertIn('TioLive Logo', [i[1] for i in image_list])

  def testGetImageFromOdt(self):
    """Test if getImage can get a image from odt file after zip"""
    with open("./data/granulate_test.odt", "rb") as f:
      data = encodebytes(f.read()).decode()
    with ZipFile('./data/granulate_test.odt') as zip:
      original_image = zip.read('Pictures/10000201000000C80000004E7B947D46.png')
    geted_image = decodebytes(self.proxy.getImage(data, '10000201000000C80000004E7B947D46.png', "odt").encode())
    self.assertEqual(original_image, geted_image)

  def testGetImageFromDoc(self):
    """Test if getImage can get a image from doc file after zip"""
    with open("./data/granulate_test.doc", "rb") as f:
      data = encodebytes(f.read()).decode()
    #This conversion is necessary to catch the image from the doc file;
    #so compare with the server return.
    data_odt = self.proxy.convertFile(data, 'doc', 'odt', False)
    zip = ZipFile(BytesIO(decodebytes(data_odt.encode())))
    png_filename = [
      name for name in zip.namelist()
      if name.startswith('Pictures/')
      and name.endswith('.png')][0]
    image_id = png_filename[len('Pictures/'):]
    original_image = zip.read(png_filename)
    geted_image = decodebytes(self.proxy.getImage(data, image_id, "doc").encode())
    self.assertEqual(original_image, geted_image)

class TestParagraphItemList(TestCase):
  def testGetParagraphItemList(self):
    """Test if getParagraphItemList can get paragraphs correctly from document"""
    with open("./data/granulate_test.odt", "rb") as f:
      data = encodebytes(f.read()).decode()
    paragraph_list = self.proxy.getParagraphItemList(data, "odt")
    self.assertEqual([[0, 'P3'], [1, 'P1'], [2, 'P12'], [3, 'P6'], [4, 'P7'],
                      [5, 'P8'], [6, 'P6'], [7, 'P6'], [8, 'P13'], [9, 'P9'],
                      [10, 'P9'], [11, 'P9'], [12, 'P4'], [13, 'P10'], [14,
                      'P5'], [15, 'P5'], [16, 'P14'], [17, 'P11'], [18, 'P11'],
                      [19, 'Standard'], [20, 'P2'], [21, 'P2'], [22, 'P2'],
                      [23, 'P2'], [24, 'P2'], [25, 'P2'], [26, 'P2'], [27,
                      'P2'], [28, 'P2'], [29, 'P2']], paragraph_list)

  def testGetParagraphItem(self):
    """Test if getParagraph can get a paragraph"""
    with open("./data/granulate_test.odt", "rb") as f:
      data = encodebytes(f.read()).decode()
    paragraph = self.proxy.getParagraph(data, 1, "odt")
    self.assertEqual(['', 'P1'], paragraph)


class TestChapterItemList(TestCase):
  def testGetChapterItemList(self):
    """Test if getChapterItemList can get the chapters list correctly from document"""
    with open("./data/granulate_chapters_test.odt", "rb") as f:
      data = encodebytes(f.read()).decode()
    chapter_list = self.proxy.getChapterItemList(data, "odt")
    self.assertEqual([[0, 'Title 0'], [1, 'Title 1'], [2, 'Title 2'],
                       [3, 'Title 3'], [4, 'Title 4'], [5, 'Title 5'],
                       [6, 'Title 6'], [7, 'Title 7'], [8, 'Title 8'],
                       [9, 'Title 9'], [10, 'Title 10']] , chapter_list)

  def testGetChapterItem(self):
    """Test if getChapterItem can get a chapter"""
    with open("./data/granulate_chapters_test.odt", "rb") as f:
      data = encodebytes(f.read()).decode()
    chapter = self.proxy.getChapterItem(1, data, "odt")
    self.assertEqual(['Title 1', 1], chapter)


class TestCSVEncoding(TestCase):
  """Cloudoo tries to be "a bit" clever with CSV:
   * the supported encoding is UTF-8, but also accepts latin9, for compatibility.
   * the fields delimiter is guessed by python csv module.
  """
  def test_decode_ascii(self):
    with open("./data/csv_ascii.csv", "rb") as f:
      data = encodebytes(f.read()).decode()
    converted = decodebytes(self.proxy.convertFile(data, "csv", "html").encode())
    parser = etree.HTMLParser()
    tree = etree.parse(BytesIO(converted), parser)
    self.assertEqual(
        ["test", "1234"],
        [x.text for x in tree.getroot().find('.//tr[1]').iterdescendants() if x.text])

  def test_decode_utf8(self):
    with open("./data/csv_utf8.csv", "rb") as f:
      data = encodebytes(f.read()).decode()
    converted = decodebytes(self.proxy.convertFile(data, "csv", "html").encode())
    parser = etree.HTMLParser()
    tree = etree.parse(BytesIO(converted), parser)
    self.assertEqual(
        ["Jérome", "ジェローム"],
        [x.text for x in tree.getroot().find('.//tr[1]').iterdescendants() if x.text])
    self.assertEqual(
        ["नमस्ते", "여보세요"],
        [x.text for x in tree.getroot().find('.//tr[2]').iterdescendants() if x.text])

  def test_decode_latin9(self):
    with open("./data/csv_latin9.csv", "rb") as f:
      data = encodebytes(f.read()).decode()
    converted = decodebytes(self.proxy.convertFile(data, "csv", "html").encode())
    parser = etree.HTMLParser()
    tree = etree.parse(BytesIO(converted), parser)
    self.assertEqual(
        ["Jérome", "1€"],
        [x.text for x in tree.getroot().find('.//tr[1]').iterdescendants() if x.text])

  def test_separator_semicolon(self):
    with open("./data/csv_semicolon.csv", "rb") as f:
      data = encodebytes(f.read()).decode()
    converted = decodebytes(self.proxy.convertFile(data, "csv", "html").encode())
    parser = etree.HTMLParser()
    tree = etree.parse(BytesIO(converted), parser)
    self.assertEqual(
        ['a a', '1'],
        [x.text for x in tree.getroot().find('.//tr[1]').iterdescendants() if x.text])
    self.assertEqual(
        ['b b', '2;x'],
        [x.text for x in tree.getroot().find('.//tr[2]').iterdescendants() if x.text])

  def test_separator_tab(self):
    with open("./data/tsv.tsv", "rb") as f:
      data = encodebytes(f.read()).decode()
    converted = decodebytes(self.proxy.convertFile(data, "csv", "html").encode())
    parser = etree.HTMLParser()
    tree = etree.parse(BytesIO(converted), parser)
    self.assertEqual(
        ['a', 'b'],
        [x.text for x in tree.getroot().find('.//tr[1]').iterdescendants() if x.text])
    self.assertEqual(
        ['1,3', 'c'],
        [x.text for x in tree.getroot().find('.//tr[2]').iterdescendants() if x.text])

  def test_empty_csv(self):
    data = ''
    converted = decodebytes(self.proxy.convertFile(data, "csv", "html").encode())
    parser = etree.HTMLParser()
    tree = etree.parse(BytesIO(converted), parser)
    self.assertEqual(
        [],
        [x.text for x in tree.getroot().findall('.//td')])

class TestInvalidFile(TestCase):
  """cloudoo should refuse potentially unsafe files."""
  def test_with_link(self):
    for ext in ('odt', 'ods', 'odp', 'odg', 'html'):
      with open('./data/with_link.%s' % ext, 'rb') as f:
        data = encodebytes(f.read()).decode()
      self.assertRaisesRegex(
        xmlrpc.client.Fault,
        'This document contains unsafe links .*',
        self.proxy.convertFile, data, ext, 'pdf'
      )
