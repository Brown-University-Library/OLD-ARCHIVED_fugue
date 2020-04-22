from setuptools import setup

setup(
    name='Fugue',
    author="Adam Bradley",
    author_email='adam_bradley@brown.edu',
    version='0.9a',
    packages=['fugue', 
            'fugue.tools',
            'fugue.tools.datasource_handlers',
            'fugue.tools.datasource_handlers.filetype_handlers'],
    install_requires=[
        "certifi>=2018.8.24",
        "Click>=7.0",
        "lxml>=4.1.0",
        "markdown2==2.3.8",
        "pytidylib>=0.3.2",
        "PyYAML>=5.1",
        "urllib3>=1.25.3",
    ],
    package_data={
        # Include mimetypes data.
        '': ['mime.types'],
    },
    entry_points='''
        [console_scripts]
        fugue=fugue:fugue
    ''',
)