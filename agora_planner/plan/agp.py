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
from collections import namedtuple
from urlparse import urlparse
from rdflib import ConjunctiveGraph, URIRef, BNode, RDF, Literal
from agora_planner.plan import fountain
from uuid import uuid1
from shortuuid import uuid


prefixes_dict = fountain.prefixes
prefixes = [(uri, p) for (p, uri) in prefixes_dict.items()]


def extend_uri(uri):
    if ':' in uri:
        prefix_parts = uri.split(':')
        if len(prefix_parts) == 2 and prefix_parts[0] in prefixes_dict:
            return prefixes_dict[prefix_parts[0]] + prefix_parts[1]

    return uri


def is_variable(arg):
    return arg.startswith('?')


def is_uri(uri):
    if uri.startswith('<') and uri.endswith('>'):
        uri = uri.lstrip('<').rstrip('>')
        parse = urlparse(uri, allow_fragments=True)
        return bool(len(parse.scheme))
    if ':' in uri:
        prefix_parts = uri.split(':')
        return len(prefix_parts) == 2 and prefix_parts[0] in prefixes_dict

    return False


class TP(namedtuple('TP', "s p o")):
    @classmethod
    def _make(cls, iterable, new=tuple.__new__, len=len):
        def transform_elm(elm):
            if is_variable(elm):
                return elm
            elif is_uri(elm):
                elm = extend_uri(elm)
                return URIRef(elm.lstrip('<').rstrip('>'))
            elif elm == 'a':
                return RDF.type
            else:
                return Literal(elm)

        res = filter(lambda x: x, map(transform_elm, iterable))
        if len(res) == 3:
            return new(cls, res)

        raise TypeError('Bad TP arguments: {}'.format(iterable))

    def __repr__(self):
        def elm_to_string(elm):
            if isinstance(elm, URIRef):
                if elm == RDF.type:
                    return 'a'
                return '<%s>' % elm

            return str(elm)
        strings = map(elm_to_string, [self.s, self.p, self.o])
        return '{} {} {}'.format(*strings)

    @staticmethod
    def from_string(st):
        parts = st.split(' ')
        return TP._make(parts)


class AgoraGP(object):
    def __init__(self):
        self._tps = []
        pass

    @property
    def triple_patterns(self):
        return self._tps

    @property
    def graph(self):
        g = ConjunctiveGraph()
        for prefix in prefixes_dict:
            g.bind(prefix, prefixes_dict[prefix])
        variables = {}
        contexts = {}

        def nodify(elm):
            if is_variable(elm):
                if not (elm in variables):
                    elm_node = BNode(elm)
                    variables[elm] = elm_node
                return variables[elm]
            else:
                if elm == 'a':
                    return RDF.type
                elif elm.startswith('"'):
                    return Literal(elm.lstrip('"').rstrip('"'))
                else:
                    try:
                        return float(elm)
                    except ValueError:
                        return URIRef(elm)

        for (s, p, o) in self._tps:
            included = False
            for ctx in contexts.values():
                if s in ctx:
                    ctx.add(o)
                    included = True
                elif o in ctx:
                    ctx.add(s)
                    included = True
            if not included:
                contexts[str(len(contexts))] = {s, o}

        for (s, p, o) in self._tps:
            s_node = nodify(s)
            o_node = nodify(o)
            p_node = nodify(p)

            context = None
            for uid in contexts:
                if s in contexts[uid]:
                    context = str(uid)

            g.get_context(context).add((s_node, p_node, o_node))

        return g

    @staticmethod
    def from_string(st):
        gp = None
        if st.startswith('{') and st.endswith('}'):
            st = st.replace('{', '').replace('}', '').strip()
            tps = st.split('.')
            tps = map(lambda x: x.strip(), filter(lambda y: y != '', tps))
            gp = AgoraGP()
            for tp in tps:
                gp.triple_patterns.append(TP.from_string(tp))
        return gp

    def __repr__(self):
        tp_strings = map(lambda x: str(x), self._tps)
        return '{ %s}' % reduce(lambda x, y: (x + '%s . ' % str(y)), tp_strings, '')



