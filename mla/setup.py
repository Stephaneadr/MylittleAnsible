from setuptools import setup

setup(
    name='MLA_haggag_Andre',
    version='1.0.0',
    author='Andre_Haggag',
    author_email='s.andre@etna-alternace.net',
    description='MyLittleAnsible',
    py_modules=['mla'],
    install_requires=['paramiko', 'click', 'PyYAML', 'jinja2'],
    entry_points={
        'console_scripts': [
            'mla = mla:main',
        ],
    },
)