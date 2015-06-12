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

from rdflib import RDF
from agora_planner.plan.agp import AgoraGP, prefixes_dict
from agora_planner.plan import fountain
from flask import request, make_response, jsonify, render_template
from flask_negotiate import produces
from agora_planner.server import app
from agora_planner.plan.graph import graph_plan, AGORA
import json
import base64

def __subject_join(tp_paths, graph, tp1, tp2):
    subject, pr1, o1 = tp1
    _, pr2, o2 = tp2
    print 'trying to s-join {} and {}'.format(tp1, tp2)
    if pr2 == RDF.type:
        o2 = graph.qname(o2)
        tp2_domain = [o2]
        tp2_domain.extend(fountain.get_type(o2).get('sub'))
    else:
        tp2_domain = fountain.get_property(graph.qname(pr2)).get('domain')

    join_paths = tp_paths[tp1][:]

    if pr1 == RDF.type:
        for path in tp_paths[tp1]:
            steps = path.get('steps')
            if len(steps):
                last_prop = path.get('steps')[-1].get('property')
                dom_r = fountain.get_property(last_prop).get('range')
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


def __subject_object_join(tp_paths, graph, tp1, tp2):
    subject, pr1, o1 = tp1
    _, pr2, o2 = tp2
    print 'trying to so-join {} and {}'.format(tp1, tp2)

    pr2 = graph.qname(pr2)
    join_paths = tp_paths[tp1][:]

    if pr1 == RDF.type:
        return []
    elif pr2 == graph.qname(RDF.type):
        tp1_range = fountain.get_property(graph.qname(pr1)).get('range')
        o2 = graph.qname(o2)
        for r_type in tp1_range:
            check_types = fountain.get_type(r_type).get('super')
            check_types.append(r_type)
            if o2 in check_types:
                return []
    else:
        if not subject == o2:
            for path in tp_paths[tp1]:
                steps = path.get('steps', [])
                if len(steps):
                    subject_prop = steps[-1].get('property')
                    subject_range = fountain.get_property(subject_prop).get('range')
                    for join_subject in subject_range:
                        if pr2 in fountain.get_type(join_subject).get('properties'):
                            join_paths.remove(path)
        else:
            subject_range = fountain.get_property(pr2).get('range')
            for path in tp_paths[tp1]:
                steps = path.get('steps', [])
                if len(steps):
                    last_type = steps[-1].get('type')
                    try:
                        previous_prop = steps[-2].get('property')
                    except IndexError:
                        previous_prop = pr2
                    if previous_prop == pr2:
                        if last_type in subject_range:
                            join_paths.remove(path)
    return join_paths


def __object_join(tp_paths, graph, tp1, tp2):
    _, pr1, obj = tp1
    _, pr2, _ = tp2
    print 'trying to o-join {} and {}'.format(tp1, tp2)

    tp2_range = fountain.get_property(graph.qname(pr2)).get('range')
    tp1_range = fountain.get_property(graph.qname(pr1)).get('range')

    if len(filter(lambda x: x in tp1_range, tp2_range)):
        return []

    return tp_paths[tp1]

def __graph_plan(g):
    def __add_node(nid, end=False, shape='roundrectangle', label=None, seed=False):
        node_data = {'data': {'id': base64.b16encode(nid), 'label': nid, 'shape': shape,
                              'width': max(80, len(nid) * 12)}}
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
        edge_data = {'data': {'id': eid, 'source': nodes[source]['data']['id'], 'label': label,
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
                    pred_range = fountain.get_property(t_pred)['range']
                    pred_range = [d for d in pred_range if not set.intersection(set(fountain.get_type(d).get('super')),
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

@app.route('/plan')
@app.route('/plan/view')
@produces('application/json', 'text/turtle', 'text/html')
def get_plan():
    def __get_context((s, p, o), graph):
        return str(list(graph.contexts((s, p, o))).pop().identifier)

    def get_tp_paths(graph):

        def __join(f, joins):
            for (sj, pj, oj) in joins:
                invalid_paths = f(tp_paths, c, (s, pr, o), (sj, pj, oj))
                join_paths.extend(invalid_paths)
            if len(joins):
                tp_paths[(s, pr, o)] = filter(lambda z: z not in join_paths, tp_paths[(s, pr, o)])

        tp_paths = {}
        for c in graph.contexts():
            for (s, pr, o) in c.triples((None, None, None)):
                if pr == RDF.type:
                    tp_paths[(s, pr, o)] = fountain.get_property_paths(graph.qname(o))
                else:
                    tp_paths[(s, pr, o)] = fountain.get_property_paths(graph.qname(pr))

            type_joins = []

            for (s, pr, o) in c.triples((None, None, None)):
                if len(tp_paths[(s, pr, o)]):
                    join_paths = []
                    so_join = [(x, pj, y) for (x, pj, y) in c.triples((None, None, s))]
                    so_join.extend([(x, pj, y) for (x, pj, y) in c.triples((o, None, None))])

                    if pr == RDF.type:
                        type_joins.append(((s, pr, o), so_join))
                        continue

                    __join(__subject_object_join, so_join)
                    s_join = [(x, pj, y) for (x, pj, y) in c.triples((s, None, None)) if pj != pr]
                    __join(__subject_join, s_join)
                    o_join = [(x, pj, y) for (x, pj, y) in c.triples((None, None, o)) if pj != pr]
                    __join(__object_join, o_join)

            for (s, pr, o), joins in type_joins:
                if len(joins):
                    paths_to_remove = []
                    for path in tp_paths[(s, pr, o)]:
                        for join in joins:
                            if path not in tp_paths[join]:
                                paths_to_remove.append(path)
                                print 'remove', path
                    tp_paths[(s, pr, o)] = [p for p in tp_paths[(s, pr, o)] if p not in paths_to_remove]

        return tp_paths

    gp_str = request.args.get('gp', '{}')
    gp = AgoraGP().from_string(gp_str)

    ugp = gp.graph

    print ugp.serialize(format='turtle')

    paths = get_tp_paths(ugp)

    plan = {"plan": [{"context": __get_context(tp, ugp), "pattern": tp, "paths": path}
                     for (tp, path) in paths.items()], "prefixes": prefixes_dict}

    mimetypes = str(request.accept_mimetypes).split(',')
    if 'application/json' in mimetypes:
        return jsonify(plan)

    g_plan = graph_plan(plan)

    if 'view' in request.url_rule.rule:
        tps = [tp.strip() for tp in gp_str.replace('"', "'").lstrip('{').rstrip('}').split('.') if tp != '']

        nodes, edges, roots = __graph_plan(g_plan)
        return render_template('graph.html',
                               nodes=json.dumps(nodes),
                               edges=json.dumps(edges), roots=json.dumps(roots), tps=json.dumps(tps))

    response = make_response(g_plan.serialize(format='turtle'))
    response.headers['Content-Type'] = 'text/turtle'
    return response
