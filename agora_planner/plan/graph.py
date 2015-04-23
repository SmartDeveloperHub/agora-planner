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

from rdflib import ConjunctiveGraph, URIRef, BNode, RDF, Literal
from rdflib.namespace import Namespace, XSD, RDFS
from uuid import uuid1

AGORA = Namespace('http://agora.org#')

def extend_uri(prefixes, short):
    (prefix, u) = short.split(':')
    try:
        return prefixes[prefix] + u
    except KeyError:
        return short

def add_variable(graph, p_node, id, subject=True):
    sub_node = BNode(str(id).replace('?', '_'))
    if subject:
        graph.add((p_node, AGORA.subject, sub_node))
    else:
        graph.add((p_node, AGORA.object, sub_node))
    graph.set((sub_node, RDF.type, AGORA.Variable))
    graph.set((sub_node, RDFS.label, Literal(str(id), datatype=XSD.string)))


def graph_plan(plan):
    plan_graph = ConjunctiveGraph()
    plan_graph.bind('agora', AGORA)
    prefixes = plan.get('prefixes')
    ef_plan = plan.get('plan')
    tree_lengths = {}
    s_trees = set([])

    for (prefix, u) in prefixes.items():
        plan_graph.bind(prefix, u)

    def inc_tree_length(tree, l):
        if tree not in tree_lengths:
            tree_lengths[tree] = 0

        tree_lengths[tree] += l

    def include_path(ty, p_seeds, p_steps, p_pattern, p_context):
        ty = extend_uri(prefixes, ty)
        path_g = plan_graph.get_context(ty)
        b_tree = BNode(ty)
        s_trees.add(b_tree)
        path_g.set((b_tree, RDF.type, AGORA.SearchTree))
        path_g.set((b_tree, AGORA.fromType, URIRef(ty)))

        for seed in p_seeds:
            path_g.add((b_tree, AGORA.hasSeed, URIRef(seed)))

        previous_node = b_tree
        prop = None
        inc_tree_length(b_tree, len(p_steps))
        for i, step in enumerate(p_steps):
            prop = step.get('property')
            b_node = BNode(previous_node.n3() + prop)
            if i < len(p_steps) - 1 or pattern[1] == RDF.type:
                path_g.add((b_node, AGORA.onProperty, URIRef(extend_uri(prefixes, prop))))
            path_g.add((b_node, AGORA.expectedType, URIRef(extend_uri(prefixes, step.get('type')))))
            path_g.add((previous_node, AGORA.next, b_node))
            previous_node = b_node
            if i < len(p_steps) - 1:
                path_g.add((b_node, AGORA.inSearchSpace, p_context))
        pattern_node = BNode()
        path_g.add((pattern_node, AGORA.inSearchSpace, p_context))
        path_g.add((previous_node, AGORA.byPattern, pattern_node))
        if p_pattern[1] == RDF.type:
            path_g.add((pattern_node, AGORA.patternType, URIRef(extend_uri(prefixes, p_pattern[2]))))
        else:
            if isinstance(p_pattern[2], URIRef):
                path_g.add((pattern_node, AGORA.objectFilter, URIRef(p_pattern[2])))
            elif isinstance(p_pattern[0], URIRef):
                path_g.add((pattern_node, AGORA.subjectFilter, URIRef(p_pattern[0])))
            elif isinstance(p_pattern[2], Literal):
                path_g.add((pattern_node, AGORA.objectFilter, Literal(p_pattern[2])))
            path_g.add((pattern_node, AGORA.patternProperty, URIRef(extend_uri(prefixes, prop))))

    for tp_plan in ef_plan:
        paths = tp_plan.get('paths')
        pattern = tp_plan.get('pattern')
        context = BNode(tp_plan.get('context'))
        for path in paths:
            steps = path.get('steps')
            seeds = path.get('seeds')
            if not len(steps) and len(seeds):
                include_path(pattern[2], seeds, steps, pattern, context)
            elif len(steps):
                ty = steps[0].get('type')
                include_path(ty, seeds, steps, pattern, context)

        for t in s_trees:
            plan_graph.set((t, AGORA.length, Literal(tree_lengths.get(t, 0), datatype=XSD.integer)))

        pattern_node = BNode()
        plan_graph.add((context, AGORA.definedBy, pattern_node))
        plan_graph.set((context, RDF.type, AGORA.SearchSpace))
        plan_graph.add((pattern_node, RDF.type, AGORA.TriplePattern))
        (sub, pred, obj) = pattern
        if isinstance(sub, BNode):
            add_variable(plan_graph, pattern_node, str(sub))

        if isinstance(obj, BNode):
            add_variable(plan_graph, pattern_node, str(obj), subject=False)
        elif isinstance(obj, Literal):
            node = BNode(str(obj))
            plan_graph.add((pattern_node, AGORA.object, node))
            plan_graph.set((node, RDF.type, AGORA.Literal))
            plan_graph.set((node, AGORA.value, Literal(str(obj), datatype=XSD.string)))
        else:
            plan_graph.add((pattern_node, AGORA.object, obj))

        plan_graph.add((pattern_node, AGORA.predicate, pred))

    # print plan_graph.serialize(format='turtle')
    return plan_graph

