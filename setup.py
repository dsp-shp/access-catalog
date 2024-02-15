#!usr/bin/env python
from json import loads
from setuptools import setup, find_packages

setup(
    **loads(open('info.json', 'r').read()),
    packages=find_packages(),
    setup_requires=['setuptools_scm'],
    include_package_data=True,
    long_description=open('README.md').read(),
    install_requires=open('requirements.txt').read().splitlines()
)
