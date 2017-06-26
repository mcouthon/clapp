from setuptools import setup


setup(
    name='clad',
    version='0.2',
    author='Pavel Brodsky',
    author_email='mcouthon@gmail.com',
    packages=[
        'clad',
    ],
    description='Cloudify dev/test environment assistant',
    license='Apache License, Version 2.0',
    install_requires=[
        'argh>=0.26.2',
        'sh>=1.12.14',
        'colorama>=0.3.9'
    ],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'clad = clad.clad:command'
        ]
    },
)
