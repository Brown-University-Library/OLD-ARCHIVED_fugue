from setuptools import setup

setup(
    name='Furnace',
    version='0.8b',
    py_modules=['furnace'],
    install_requires=[
        "certifi>=2018.8.24",
        "Click>=7.0",
        "lxml>=4.1.0",
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
        furnace=furnace:furnace
    ''',
)