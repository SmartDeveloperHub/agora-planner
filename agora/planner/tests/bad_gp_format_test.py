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

__author__ = 'Fernando Serena'

from nose.tools import *

from agora.planner.tests import PlannerTest


class MissingBracketTest(PlannerTest):
    def test_1(self):
        r = self.app.get('/plan?gp={', headers={'accept': 'text/turtle'})
        eq_(r.status_code, 400, r.data)

    def test_2(self):
        r = self.app.get('/plan?gp=}', headers={'accept': 'text/turtle'})
        eq_(r.status_code, 400, r.data)

    def test_3(self):
        r = self.app.get('/plan?gp={ ?s a prefix:Concept', headers={'accept': 'text/turtle'})
        eq_(r.status_code, 400, r.data)


class BadTripleSeparatorFormatTest(PlannerTest):
    def test_missing_separator(self):
        r = self.app.get('/plan?gp={?s a prefix:Concept ?f prefix:property ?s', headers={'accept': 'text/turtle'})
        eq_(r.status_code, 400, r.data)

    # separator must be '. '
    def test_incomplete_separator(self):
        self.post_vocabulary('simple_two_concepts')
        r = self.app.get('/plan?gp={?s a test:Concept1.?p a test:Concept2}', headers={'accept': 'text/turtle'})
        self.delete_vocabulary('stwoc')
        eq_(r.status_code, 400, r.data)


class WrongSubjectAndPredicateTypesInTripleTest(PlannerTest):
    # 'ns' should be an unknown prefix
    def test_subject_as_literal(self):
        r = self.app.get('/plan?gp={ns:subject a ns:Concept }', headers={'accept': 'text/turtle'})
        eq_(r.status_code, 400, r.data)

    def test_predicate_as_literal(self):
        r = self.app.get('/plan?gp={<http://subject.org> ns:p ns:Concept }', headers={'accept': 'text/turtle'})
        eq_(r.status_code, 400, r.data)

    def test_both_as_literal(self):
        r = self.app.get('/plan?gp={ns:s ns:p ns:Concept }', headers={'accept': 'text/turtle'})
        eq_(r.status_code, 400, r.data)
