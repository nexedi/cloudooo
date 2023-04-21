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
from os.path import join
from cloudooo.tests.cloudoooTestCase import TestCase


class TestServer(TestCase):
  """Test XmlRpc Server. Needs cloudooo server started"""

  def ConversionScenarioList(self):
    return [
            (join('data', 'test.png'), "png", "jpg", "image/jpeg"),
            ]

  def testConvertPNGtoJPG(self):
    """Converts png to jpg"""
    self.runConversionList(self.ConversionScenarioList())

  def FaultConversionScenarioList(self):
    scenario_list = [
      # Test to verify if server fail when a empty file is sent
      (b'', '', ''),
    ]
    # Try convert one png for a invalid format
    with open(join('data', 'test.png'), 'rb') as f:
      scenario_list.append((f.read(), 'png', 'xyz'))
    # Try convert one png to format not possible
    with open(join('data', 'test.png'), 'rb') as f:
      scenario_list.append((f.read(), 'png', '8bim'))
    return scenario_list

  def testFaultConversion(self):
    """Test fail convertion of Invalid image files"""

  def GetMetadataScenarioList(self):
    return [
            (join('data', 'test.png'), "png", dict(Compression='Zip')),
            ]

  def testGetMetadataFromPNG(self):
    """test if metadata are extracted correctly from png image file"""
    self.runGetMetadataList(self.GetMetadataScenarioList())

  def FaultGetMetadataScenarioList(self):
    return [
            # Test to verify if server fail when a empty string is sent
            ('', ''),
            ]

  def testFaultGetMetadata(self):
    """Test getMetadata from invalid image file"""
    self.runFaultGetMetadataList(self.FaultGetMetadataScenarioList())


