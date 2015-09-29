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
import socket

__author__ = 'Fernando Serena'

from rdflib import RDF
from agora.planner.plan import Plan
from flask import request, make_response, jsonify, render_template, Response
from flask_negotiate import produces
from agora.planner.server import app
from agora.planner.plan.graph import AGORA
import json
import base64
from agora.client.agora import PlanExecutor


class APIError(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


class NotFound(APIError):
    def __init__(self, message, payload=None):
        super(NotFound, self).__init__(message, 404, payload)


class Conflict(APIError):
    def __init__(self, message, payload=None):
        super(Conflict, self).__init__(message, 409, payload)


@app.errorhandler(APIError)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route('/plan')
@app.route('/plan/view')
@produces('application/json', 'text/turtle', 'text/html')
def get_plan():
    def __graph_plan(g):
        def __add_node(nid, end=False, shape='roundrectangle', label=None, seed=False):
            node_data = {'data': {'id': base64.b16encode(nid), 'label': nid, 'shape': shape,
                                  'width': max(100, len(nid) * 12)}}
            if label is not None:
                node_data['data']['label'] = str(label)
            if end:
                node_data['classes'] = 'end'
            if seed:
                node_data['classes'] = 'seed'
            if nid in nodes:
                prev_data = nodes[nid]
                if 'classes' in prev_data:
                    node_data['classes'] = prev_data['classes']
            nodes[nid] = node_data

        def __add_edge(source, label, target, end=False):
            eid = base64.b64encode(source + label + target)
            edge_data = {'data': {'id': eid, 'source': nodes[source]['data']['id'], 'label': label + '\n\n',
                                  'target': nodes[target]['data']['id']}}
            if end:
                edge_data['classes'] = 'end'
            if eid in edges:
                prev_data = edges[eid]
                if 'classes' in prev_data:
                    edge_data['classes'] = prev_data['classes']
            edges[eid] = edge_data

        def __check_pattern(parent, link, sources):
            patterns = g.objects(parent, AGORA.byPattern)
            for tp in patterns:
                t_pred = list(g.objects(tp, AGORA.predicate)).pop()
                if t_pred == RDF.type:
                    p_type = g.qname(list(g.objects(tp, AGORA.object)).pop())
                    __add_node(p_type, end=True)
                    if sources is not None:
                        for st in sources:
                            __add_edge(st, link, p_type)
                else:
                    t_pred = g.qname(t_pred)
                    t_obj = list(g.objects(tp, AGORA.object)).pop()
                    if (t_obj, RDF.type, AGORA.Literal) in g:
                        filter_value = list(g.objects(t_obj, AGORA.value)).pop()
                        filter_id = 'n{}'.format(len(nodes))
                        __add_node(filter_id, end=True, shape='ellipse', label='"{}"'.format(filter_value))
                        for st in sources:
                            __add_edge(st, t_pred, filter_id, end=True)
                    else:
                        pred_range = plan.fountain.get_property(t_pred)['range']
                        pred_range = [d for d in pred_range if
                                      not set.intersection(set(plan.fountain.get_type(d).get('super')),
                                                           set(pred_range))]
                        for st in sources:
                            for rt in pred_range:
                                __add_node(rt)
                                __add_edge(st, t_pred, rt, end=True)

        def __follow_next(parent, link=None, sources=None):
            child = list(g.objects(parent, AGORA.next))

            __check_pattern(parent, link, sources)

            for ch in child:
                expected_types = [g.qname(x) for x in g.objects(ch, AGORA.expectedType)]
                for et in expected_types:
                    __add_node(et)
                try:
                    for et in expected_types:
                        if link is not None:
                            for st in sources:
                                __add_edge(st, link, et)
                    on_property = g.qname(list(g.objects(ch, AGORA.onProperty)).pop())
                    last_property = on_property
                    source_types = expected_types
                    __follow_next(ch, last_property, source_types)
                except IndexError:
                    __check_pattern(ch, None, expected_types)

        nodes = {}
        edges = {}
        roots = set([])

        trees = g.subjects(RDF.type, AGORA.SearchTree)

        for tree in trees:
            seed_type = g.qname(list(g.objects(tree, AGORA.fromType)).pop())
            __add_node(seed_type, seed=True)
            roots.add(nodes[seed_type]['data']['id'])
            __follow_next(tree)

        return nodes.values(), edges.values(), list(roots)

    gp_str = request.args.get('gp', '{}')
    try:
        plan = Plan(gp_str)
    except EnvironmentError as e:
        raise NotFound(e.message)
    except (AttributeError, NameError, TypeError) as e:
        raise APIError(e.message)

    mimetypes = str(request.accept_mimetypes).split(',')
    if 'application/json' in mimetypes:
        return jsonify(plan.json)

    if 'view' in request.url_rule.rule:
        tps = [tp.strip() for tp in gp_str.replace('"', "'").lstrip('{').rstrip('}').split('.') if tp != '']

        nodes, edges, roots = __graph_plan(plan.graph)
        return render_template('graph.html',
                               nodes=json.dumps(nodes),
                               edges=json.dumps(edges), roots=json.dumps(roots), tps=json.dumps(tps))

    response = make_response(plan.graph.serialize(format='turtle'))
    response.headers['Content-Type'] = 'text/turtle'
    return response


@app.route('/fragment')
def get_fragment():
    def get_triples():
        for prefix, uri in ns:
            yield '@prefix {}: <{}> .\n'.format(prefix, uri)
        yield '\n'
        for (_, s, p, o) in gen:
            yield '{} {} {} .\n'.format(s.n3(graph.namespace_manager), p.n3(graph.namespace_manager),
                                        o.n3(graph.namespace_manager))

    gp_str = request.args.get('gp', '{}')
    plan = Plan(gp_str)
    executor = PlanExecutor(plan.graph)
    gen, ns, graph = executor.get_fragment_generator(queue_wait=1)
    return Response(get_triples(), mimetype='text/n3')


@app.route('/sparql')
def query_fragment():
    q_str = request.args.get('q', None)
    pattern = q_str[q_str.find('{'):]
    plan = Plan(pattern.lstrip().rstrip())
    executor = PlanExecutor(plan.graph)
    fragment = executor.get_fragment()
    result = fragment.query(q_str)
    return jsonify({"result": list(result)})
