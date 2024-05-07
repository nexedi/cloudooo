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

import gc

from os import path, mkdir, environ
from cloudooo.wsgixmlrpcapplication import WSGIXMLRPCApplication
from cloudooo import util


def application(global_config, **local_config):
  """Method to load all configuration of cloudooo and start the application.
  To start the application a number of params are required:
  Keyword arguments:
  debug_mode -- Mode as the application prints the messages.
      e.g debug_mode=logging.DEBUG
  working_path -- Full path to create the environment of the processes.
      e.g working_path='/var/run/cloudooo'
  application_hostname -- Sets the host to Openoffice.
  office_binary_path -- Folder where soffice.bin is installed.
      e.g office_binary_path='/opt/libreoffice/program'
  uno_path -- Folder where UNO library is installed.
      e.g uno_path='/opt/libreoffice/basis-link/program/'
  """
  prefix = 'env-'
  environment_dict = {}
  for parameter_name, value in local_config.items():
    if parameter_name.startswith(prefix):
      value = value or ''
      variable_name = parameter_name[len(prefix):]
      if variable_name == 'PATH':
        # merge only for PATH
        current_value = environ.get(variable_name, '')
        if current_value:
          value = '%s:%s' % (value, current_value)
      environment_dict[variable_name] = value

  local_config["env"] = environment_dict

  gc.enable()
  util.configureLogger(
    debug_mode=util.convertStringToBool(
    # .lower() is for backward compatibility
    local_config.get('debug_mode', 'false').lower()),
    logfile=local_config.get('logfile')
  )
  # path of directory to run cloudooo
  working_path = local_config.get('working_path')
  if not path.exists(working_path):
    mkdir(working_path)
  # directory to create temporary files
  cloudooo_path_tmp_dir = path.join(working_path, 'tmp')
  if not path.exists(cloudooo_path_tmp_dir):
    mkdir(cloudooo_path_tmp_dir)

  util.loadMimetypeList()

  mimetype_registry = local_config.get("mimetype_registry", "")
  local_config["mimetype_registry"] = handler_mapping_list = \
                                    [_f for _f in mimetype_registry.split("\n") if _f]

  ooo_disable_filter_list = []
  for filter_name in local_config.get("ooo_disable_filter_list", "").split("\n"):
    filter_name = filter_name.strip()
    if filter_name and not filter_name in ooo_disable_filter_list:
      ooo_disable_filter_list.append(filter_name)
  local_config["ooo_disable_filter_list"] = ooo_disable_filter_list

  ooo_disable_filter_name_list = []
  for filter_name in local_config.get("ooo_disable_filter_name_list", "").split("\n"):
    filter_name = filter_name.strip()
    if filter_name and not filter_name in ooo_disable_filter_name_list:
      ooo_disable_filter_name_list.append(filter_name)
  local_config["ooo_disable_filter_name_list"] = ooo_disable_filter_name_list

  handler_dict = {}
  for line in handler_mapping_list:
    input_mimetype, output_mimetype, handler = line.strip().split()
    if handler not in handler_dict:
      import_path = "cloudooo.handler.%s.handler" % handler
      # Import Errors are not catched, check your configuration file
      module = __import__(import_path, globals(), locals(), [''])
      # Call the bootstraping method
      getattr(module, 'bootstrapHandler', lambda x: None)(local_config)
      handler_dict[handler] = module.Handler

  local_config['handler_dict'] = handler_dict
  from .manager import Manager
  cloudooo_manager = Manager(cloudooo_path_tmp_dir, **local_config)
  return WSGIXMLRPCApplication(instance=cloudooo_manager)
