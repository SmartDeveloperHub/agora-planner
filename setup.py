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

import json

from setuptools import setup, find_packages

__author__ = 'Fernando Serena'

with open("agora/planner/metadata.json", 'r') as stream:
    metadata = json.load(stream)

setup(
    name="Agora-Planner",
    version=metadata['version'],
    author=metadata['author'],
    author_email=metadata['email'],
    description=metadata['description'],
    license="Apache 2",
    keywords=["linked-data", "path", "ontology", "plan"],
    url=metadata['github'],
    download_url="https://github.com/smartdeveloperhub/agora-planner/tarball/0.3.5-alpha1",
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['agora.planner'],
    install_requires=['flask', 'Flask-Negotiate', 'requests', 'rdflib', 'networkx'],
    classifiers=[],
    scripts=['planner'],
    package_dir={'agora.planner': 'agora/planner', 'agora.planner.server': 'agora/planner/server'},
    package_data={'agora.planner.server': ['templates/*.*', 'static/*.*'], 'agora.planner': ['metadata.json']},
)
