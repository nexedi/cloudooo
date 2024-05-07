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

import email
import email.message
import logging
import mimetypes
import pkg_resources
import os
from zipfile import ZipFile, ZIP_DEFLATED

logger = logging.getLogger('Cloudooo')

PYTHON_ENVIRONMENT = [
      'PYTHONHOME',
      'PYTHONPATH',
      'PYTHONSTARTUP',
      'PYTHONY2K',
      'PYTHONOPTIMIZE',
      'PYTHONDEBUG',
      'PYTHONDONTWRITEBYTECODE',
      'PYTHONINSPECT',
      'PYTHONNOUSERSITE',
      'PYTHONNOUSERSITE',
      'PYTHONUNBUFFERED',
      'PYTHONVERBOSE'
]


def loadMimetypeList():
  mime_types_url = pkg_resources.resource_filename(__name__,
                                                   "mime.types")
  mimetypes.init(files=[mime_types_url, ])


def configureLogger(level=None, debug_mode=False, logfile=None):
  """Configure logger.
  Keyword arguments:
  level -- Level to prints the log messages
  """
  if level is None:
    level = logging.INFO

  if debug_mode:
    level = logging.DEBUG

  handler_list = logger.handlers
  if handler_list:
    for handler in iter(handler_list):
      logger.removeHandler(handler)
  # The propagate value indicates whether or not parents of this loggers will
  # be traversed when looking for handlers. It doesn't really make sense in the
  # root logger - it's just there because a root logger is almost like any
  # other logger.
  logger.propagate = 0
  logger.setLevel(level)
  # create console handler and set level to debug
  if logfile:
    ch = logging.FileHandler(logfile)
  else:
    ch = logging.StreamHandler()
  ch.setLevel(level)
  # create formatter
  format = "%(asctime).19s - %(name)s - %(levelname)s - %(message)s"
  formatter = logging.Formatter(format)
  # add formatter to ch
  ch.setFormatter(formatter)
  # add ch to logger
  logger.addHandler(ch)

convertStringToBool = ('false', 'true').index

def zipTree(destination, *tree_path_list):
  """
    destination may be a path or a file-like

    tree_path_list is a list that may contain a path or a couple(path, archive_root)
  """
  def archive(arg, archive_root):
    archive_name = os.path.join(archive_root, os.path.basename(arg))
    if os.path.islink(arg):
      pass  # XXX logger.warn("zipTree: symlink %r ignored\n" % arg)
    elif os.path.isdir(arg):
      for r, _, ff in os.walk(arg):
        zfile.write(r, archive_name)
        for f in ff:
          archive(os.path.join(r, f), archive_name)
    elif os.path.isfile(arg):
      zfile.write(arg, archive_name)
    else:
      pass  # XXX logger.warn("zipTree: unknown %r ignored\n" % arg)
  zfile = ZipFile(destination, "w", ZIP_DEFLATED)
  for tree_path in tree_path_list:
    if isinstance(tree_path, tuple):
      archive(*tree_path)
    else:
      archive(tree_path, os.path.dirname(tree_path))
  zfile.close()
  return destination

def unzip(source, destination):
  with ZipFile(source) as zipfile:
    zipfile.extractall(destination)

def parseContentType(content_type:str) -> email.message.EmailMessage:
  """Parses `text/plain;charset="utf-8"` to an email object.

  Note: Content type or MIME type are built like `maintype/subtype[;params]`.

      parsed_content_type = parseContentType('text/plain;charset="utf-8"')
      parsed_content_type.get_content_type()  -> 'text/plain'
      parsed_content_type.get_charset()  -> 'utf-8'
  """
  return email.message_from_string("Content-Type:" + content_type.replace("\r\n", "\r\n\t"))
