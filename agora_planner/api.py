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
from flask import request, make_response, jsonify
from flask_negotiate import produces
from agora_planner.server import app
from agora_planner.plan.graph import graph_plan


def subject_join(tp_paths, graph, tp1, tp2):
    subject, pr1, o1 = tp1
    _, pr2, o2 = tp2
    print 'trying to s-join {} and {}'.format(tp1, tp2)
    if pr2 == RDF.type:
        o2 = graph.qname(o2)
        tp2_domain = [o2]
        tp2_domain.extend(fountain.get_type(o2).get('sub'))
    else:
        tp2_domain = fountain.get_property(graph.qname(pr2)).get('domain')

    join_paths = []

    if pr1 == RDF.type:
        for path in tp_paths[tp1]:
            steps = path.get('steps')
            if len(steps):
                last_prop = path.get('steps')[-1].get('property')
                dom_r = fountain.get_property(last_prop).get('range')
                if len(filter(lambda x: x in tp2_domain, dom_r)):
                    join_paths.append(path)
            else:
                join_paths.append(path)
    elif pr2 == RDF.type:
        for path in tp_paths[tp1]:
            last_type = path.get('steps')[-1].get('type')
            if last_type in tp2_domain:
                join_paths.append(path)
    else:
        for path in tp_paths[tp1]:
            if path.get('steps')[-1].get('type') in tp2_domain:
                join_paths.append(path)

    return join_paths


def subject_object_join(tp_paths, graph, tp1, tp2):
    subject, pr1, o1 = tp1
    _, pr2, o2 = tp2
    print 'trying to so-join {} and {}'.format(tp1, tp2)

    pr2 = graph.qname(pr2)
    join_paths = []

    if pr1 == RDF.type:
        tp2_range = fountain.get_property(pr2).get('range')
        for path in tp_paths[tp1]:
            last_prop = path.get('steps')[-1].get('property')
            range_r = fountain.get_property(last_prop).get('range')
            if len(filter(lambda x: x in tp2_range, range_r)):
                join_paths.append(path)
    elif pr2 == graph.qname(RDF.type):
        # TODO: Iterate through tp1 to avoid path leaks
        tp1_range = fountain.get_property(graph.qname(pr1)).get('range')
        o2 = graph.qname(o2)
        for r_type in tp1_range:
            check_types = fountain.get_type(r_type).get('super')
            check_types.append(r_type)
            if o2 in check_types:
                return tp_paths[tp1]
    else:
        if not subject == o2:
            for path in tp_paths[tp1]:
                steps = path.get('steps', [])
                if len(steps):
                    subject_prop = steps[-1].get('property')
                    subject_range = fountain.get_property(subject_prop).get('range')
                    for join_subject in subject_range:
                        if pr2 in fountain.get_type(join_subject).get('properties'):
                            join_paths.append(path)
        else:
            for path in tp_paths[tp1]:
                steps = path.get('steps', [])
                if len(steps):
                    last_type = steps[-1].get('type')
                    subject_range = fountain.get_property(pr2).get('range')
                    if last_type in subject_range:
                        join_paths.append(path)
    return join_paths


def object_join(tp_paths, graph, tp1, tp2):
    _, pr1, obj = tp1
    _, pr2, _ = tp2
    print 'trying to o-join {} and {}'.format(tp1, tp2)

    tp2_range = fountain.get_property(graph.qname(pr2)).get('range')
    tp1_range = fountain.get_property(graph.qname(pr1)).get('range')

    if not len(filter(lambda x: x in tp1_range, tp2_range)):
        tp_paths[tp1] = []

    return tp_paths[tp1]


@app.route('/plan')
@produces('application/json', 'text/turtle', 'text/html')
def get_plan():
    def shorten_part(part, graph):
        if part.startswith('?'):
            return part

        try:
            return graph.qname(part)
        except Exception:
            return part

    def get_context((s, p, o), graph):
        return str(list(graph.contexts((s, p, o))).pop().identifier)

    def get_tp_paths(graph):
        tp_paths = {}
        for (s, pr, o) in graph.triples((None, None, None)):
            print list(graph.contexts((s, pr, o))).pop()

            if pr == RDF.type:
                tp_paths[(s, pr, o)] = fountain.get_property_paths(graph.qname(o))
            else:
                tp_paths[(s, pr, o)] = fountain.get_property_paths(graph.qname(pr))

            if len(tp_paths[(s, pr, o)]):
                join_paths = []
                so_join = [(x, pj, y) for (x, pj, y) in graph.triples((None, None, s))]
                so_join.extend([(x, pj, y) for (x, pj, y) in graph.triples((o, None, None))])
                for (sj, pj, oj) in so_join:
                    so_paths = subject_object_join(tp_paths, graph, (s, pr, o), (sj, pj, oj))
                    if not len(so_paths):
                        join_paths = []
                        break
                    join_paths.extend(so_paths)
                if len(so_join):
                    tp_paths[(s, pr, o)] = filter(lambda z: z in join_paths, tp_paths[(s, pr, o)])

                s_join = [(x, pj, y) for (x, pj, y) in graph.triples((s, None, None)) if pj != pr]
                for (sj, pj, oj) in s_join:
                    s_paths = subject_join(tp_paths, graph, (s, pr, o), (sj, pj, oj))
                    if not len(s_paths):
                        join_paths = []
                        break
                    join_paths.extend(s_paths)
                if len(s_join):
                    tp_paths[(s, pr, o)] = filter(lambda z: z in join_paths, tp_paths[(s, pr, o)])

                o_join = [(x, pj, y) for (x, pj, y) in graph.triples((None, None, o)) if pj != pr]
                for (sj, pj, oj) in o_join:
                    o_paths = object_join(tp_paths, graph, (s, pr, o), (sj, pj, oj))
                    if not len(o_paths):
                        join_paths = []
                        break
                    join_paths.extend(o_paths)
                if len(o_join):
                    tp_paths[(s, pr, o)] = filter(lambda z: z in join_paths, tp_paths[(s, pr, o)])

        return tp_paths

    gp_str = request.args.get('gp', '{}')
    gp = AgoraGP().from_string(gp_str)

    ugp = gp.graph
    paths = get_tp_paths(ugp)

    plan = {"plan": [{"context": get_context(tp, ugp), "pattern": tp, "paths": path}
                     for (tp, path) in paths.items()], "prefixes": prefixes_dict}

    mimetypes = str(request.accept_mimetypes).split(',')
    if 'application/json' in mimetypes:
        return jsonify(plan)

    g_plan = graph_plan(plan)

    response = make_response(g_plan.serialize(format='turtle'))
    response.headers['Content-Type'] = 'text/turtle'
    return response
