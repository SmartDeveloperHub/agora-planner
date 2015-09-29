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
import requests

__author__ = 'Fernando Serena'

import unittest

import logging

from agora.planner.server import app


def setup():
    from agora.planner.server.config import TestingConfig

    app.config['TESTING'] = True
    app.config.from_object(TestingConfig)

    from agora.planner import api


class PlannerTest(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        pass

    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        self.app = app.test_client()
        self.log = logging.getLogger('agora.planner.test')

    def tearDown(self):
        pass

    def post_vocabulary(self, filename):
        with open('agora/planner/tests/vocabs/{}.ttl'.format(filename)) as f:
            vocab = f.read()
            response = requests.post('{}/vocabs'.format(app.config['FOUNTAIN']), data=vocab,
                                     headers={'content-type': 'text/turtle'})
            print response

    def delete_vocabulary(self, vid):
        response = requests.delete('{}/vocabs/{}'.format(app.config['FOUNTAIN'], vid))
        print response
