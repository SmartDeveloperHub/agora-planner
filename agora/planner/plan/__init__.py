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

from agora.planner.plan.fountain import Fountain
from agora.planner.server import app
from agora.planner.plan.agp import AgoraGP
from rdflib import RDF, BNode, Literal
from agora.planner.plan.graph import graph_plan
import logging
from rdflib.namespace import FOAF

log = logging.getLogger('agora_planner.plan')


def make_fountain():
    return Fountain(app.config['FOUNTAIN'])


def _stringify_tp(context, (s, p, o)):
    def stringify_elm(elm):
        if isinstance(elm, BNode):
            return elm.n3(context.namespace_manager)
        elif isinstance(elm, Literal):
            return elm.toPython()

        return context.qname(elm)

    return '{} {} {} .'.format(stringify_elm(s), stringify_elm(p), stringify_elm(o))


class Plan(object):
    def __subject_join(self, tp_paths, context, tp1, tp2, **kwargs):
        subject, pr1, o1 = tp1
        _, pr2, o2 = tp2

        log.debug('trying to s-join {} and {}'.format(_stringify_tp(context, tp1), _stringify_tp(context, tp2)))
        if pr2 == RDF.type:
            o2 = context.qname(o2)
            tp2_domain = [o2]
            tp2_domain.extend(self.__fountain.get_type(o2).get('sub'))
        else:
            tp2_domain = self.__fountain.get_property(context.qname(pr2)).get('domain')

        join_paths = tp_paths[tp1][:]

        if pr1 == RDF.type:
            for path in tp_paths[tp1]:
                steps = path.get('steps')
                if len(steps):
                    last_prop = path.get('steps')[-1].get('property')
                    dom_r = self.__fountain.get_property(last_prop).get('range')
                    if len(filter(lambda x: x in tp2_domain, dom_r)):
                        join_paths.remove(path)
                else:
                    join_paths.remove(path)
        elif pr2 == RDF.type:
            for path in tp_paths[tp1]:
                last_type = path.get('steps')[-1].get('type')
                if last_type in tp2_domain:
                    join_paths.remove(path)
        else:
            for path in tp_paths[tp1]:
                if path.get('steps')[-1].get('type') in tp2_domain:
                    join_paths.remove(path)

        return join_paths

    def __subject_object_join(self, tp_paths, context, tp1, tp2, hints=None):
        subject, pr1, o1 = tp1
        _, pr2, o2 = tp2
        log.debug('trying to so-join {} and {}'.format(_stringify_tp(context, tp1), _stringify_tp(context, tp2)))

        pr2 = context.qname(pr2)
        join_paths = tp_paths[tp1][:]

        if pr1 == RDF.type or subject == o2:
            for path in tp_paths[tp1]:
                steps = path.get('steps', [])
                if len(steps):
                    if pr1 == RDF.type:
                        matching_steps = steps[:]
                    else:
                        matching_steps = steps[:-1]
                    for o_path in tp_paths[tp2]:
                        if o_path.get('steps') == matching_steps:
                            join_paths.remove(path)
        elif pr2 == context.qname(RDF.type):
            tp1_range = self.__fountain.get_property(context.qname(pr1)).get('range')
            o2 = context.qname(o2)
            for r_type in tp1_range:
                check_types = self.__fountain.get_type(r_type).get('super')
                check_types.append(r_type)
                if o2 in check_types:
                    join_paths = []
                    break
            if not join_paths and hints is not None:
                hints[tp2]['check'] = hints[tp2].get('check', False) or len(tp1_range) > 1
        else:
            if not subject == o2:
                for path in tp_paths[tp1]:
                    steps = path.get('steps', [])
                    if len(steps):
                        subject_prop = steps[-1].get('property')
                        subject_range = self.__fountain.get_property(subject_prop).get('range')
                        for join_subject in subject_range:
                            if pr2 in self.__fountain.get_type(join_subject).get('properties') and path in join_paths:
                                join_paths.remove(path)
        return join_paths

    def __object_join(self, tp_paths, context, tp1, tp2, **kwargs):
        _, pr1, obj = tp1
        _, pr2, _ = tp2
        log.debug('trying to o-join {} and {}'.format(_stringify_tp(context, tp1), _stringify_tp(context, tp2)))

        tp2_range = self.__fountain.get_property(context.qname(pr2)).get('range')
        tp1_range = self.__fountain.get_property(context.qname(pr1)).get('range')

        if len(filter(lambda x: x in tp1_range, tp2_range)):
            return []

        return tp_paths[tp1]

    def __get_tp_paths(self):
        def __join(f, joins):
            invalid_paths = []
            for (sj, pj, oj) in joins:
                invalid_paths.extend(f(tp_paths, c, (s, pr, o), (sj, pj, oj), hints=tp_hints))
            if len(joins):
                tp_paths[(s, pr, o)] = filter(lambda z: z not in invalid_paths, tp_paths[(s, pr, o)])
            join_paths.extend(invalid_paths)

        tp_paths = {}
        tp_hints = {}
        for c in self.__agp.contexts():
            for (s, pr, o) in c.triples((None, None, None)):
                tp_hints[(s, pr, o)] = {}
                try:
                    if pr == RDF.type:
                        tp_paths[(s, pr, o)] = self.__fountain.get_property_paths(self.__agp.qname(o))
                    else:
                        tp_paths[(s, pr, o)] = self.__fountain.get_property_paths(self.__agp.qname(pr))
                except IOError as e:
                    raise NameError('Cannot get a path to an unknown subject: {}'.format(e.message))

            while True:
                join_paths = []

                for (s, pr, o) in c.triples((None, None, None)):
                    if len(tp_paths[(s, pr, o)]):
                        s_join = [(x, pj, y) for (x, pj, y) in c.triples((s, None, None)) if pj != pr]
                        __join(self.__subject_join, s_join)
                        o_join = [(x, pj, y) for (x, pj, y) in c.triples((None, None, o)) if pj != pr]
                        __join(self.__object_join, o_join)
                        so_join = [(x, pj, y) for (x, pj, y) in c.triples((None, None, s))]
                        so_join.extend([(x, pj, y) for (x, pj, y) in c.triples((o, None, None))])
                        __join(self.__subject_object_join, so_join)
                if not join_paths:
                    break

        for (s, pr, o) in tp_hints:
            if pr == RDF.type and 'check' not in tp_hints[(s, pr, o)]:
                tp_hints[(s, pr, o)]['check'] = len(self.__fountain.get_type(self.__agp.qname(o)).get('super')) > 0

        return tp_paths, tp_hints

    def __get_context(self, (s, p, o)):
        return str(list(self.__agp.contexts((s, p, o))).pop().identifier)

    def __init__(self, gp):
        self.__fountain = make_fountain()
        agora_gp = AgoraGP.from_string(gp, self.fountain.prefixes)
        if agora_gp is None:
            raise AttributeError('{} is not a valid graph pattern'.format(gp))

        self.__agp = agora_gp.graph
        log.debug('Agora Graph Pattern:\n{}'.format(self.__agp.serialize(format='turtle')))

        try:
            paths, hints = self.__get_tp_paths()
            self.__plan = {
                "plan": [{"context": self.__get_context(tp), "pattern": tp, "paths": path, "hints": hints[tp]}
                         for (tp, path) in paths.items()], "prefixes": agora_gp.prefixes}

            self.__g_plan = graph_plan(self.__plan, self.__fountain)
        except TypeError:
            raise NameError

    @property
    def json(self):
        return self.__plan

    @property
    def graph(self):
        return self.__g_plan

    @property
    def fountain(self):
        return self.__fountain
