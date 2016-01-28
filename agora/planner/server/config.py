"""
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  This file is part of the Smart Developer Hub Project:
    http://www.smartdeveloperhub.org

  Center for Open Middleware
        http://www.centeropenmiddleware.com/
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  Copyright (C) 2015 Center for Open Middleware.
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

            http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
"""

import logging
import os

__author__ = 'Fernando Serena'


def _api_port():
    return int(os.environ.get('PLANNER_API_PORT', 5000))


def _fountain_conf(def_host, def_port):
    return {'host': os.environ.get('PLANNER_FOUNTAIN_HOST', def_host),
            'port': os.environ.get('PLANNER_FOUNTAIN_PORT', def_port)}


class Config(object):
    PORT = _api_port()


class DevelopmentConfig(Config):
    DEBUG = True
    LOG = logging.DEBUG
    FOUNTAIN = _fountain_conf('localhost', 5002)


class ProductionConfig(Config):
    DEBUG = False
    LOG = logging.INFO
    FOUNTAIN = _fountain_conf('fountain', 5002)


class TestingConfig(Config):
    DEBUG = True
    LOG = logging.DEBUG
    FOUNTAIN = _fountain_conf('localhost', 5002)
