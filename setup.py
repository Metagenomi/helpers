from distutils.core import setup
import setuptools

version = '1.0.1'

packages = ['metagenomi_helpers']

scripts = ['metagenomi_helpers/helpers.py']

classifiers = ['Programming Language :: Python', 'Programming Language :: Python :: 3']

requirements = ['boto3']

setup(
    name='metagenomi_helpers',
    author='Metagenomi.co',
    author_email='info@metagenomi.co',
    version=version,
    packages=packages,
    license='MIT',
    long_description=open('README.md').read(),
    install_requires=requirements,
    classifiers=classifiers,
    url='http://metagenomi.co'
)
