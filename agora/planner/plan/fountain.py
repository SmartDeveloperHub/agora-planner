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
import urlparse

import requests

__author__ = 'Fernando Serena'

log = logging.getLogger('agora.planner.plan')


class Fountain(object):
    def __init__(self, host='localhost', port=5002):
        self.__fountain_url = 'http://{}:{}'.format(host, port)
        self.__types = {}
        self.__properties = {}

    def __send_request(self, path):
        try:
            response = requests.get(urlparse.urljoin(self.__fountain_url, path))
            if response.status_code != 200:
                raise IOError(response.json())
            return response.json()
        except requests.ConnectionError:
            message = 'A fountain is not available'
            log.error(message)
            raise EnvironmentError(message)

    @property
    def types(self):
        response = self.__send_request('types')
        return response.get('types')

    @property
    def properties(self):
        response = self.__send_request('properties')
        return response.get('properties')

    def get_type_seeds(self, ty):
        response = self.__send_request('seeds/{}'.format(ty))
        return response.get('seeds')

    def get_property(self, prop):
        if prop not in self.__properties:
            self.__properties[prop] = self.__send_request('properties/{}'.format(prop))

        return self.__properties[prop]

    def get_type(self, ty):
        if ty not in self.__types:
            self.__types[ty] = self.__send_request('types/{}'.format(ty))
        return self.__types[ty]

    @property
    def prefixes(self):
        response = self.__send_request('prefixes')
        return response

    def get_property_paths(self, prop):
        response = self.__send_request('paths/{}'.format(prop))
        return response.get("paths")
