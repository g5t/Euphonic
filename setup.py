try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages

setup(
    name='Euphonic',
    version='0.1dev',
    description="""Module to read CASTEP electronic/vibrational frequency data
                   and output a dispersion/dos plot""",
    packages=find_packages(),
    install_requires=[
        'numpy>=1.9.1',
	'scipy>=1.0.0',
        'seekpath>=1.1.0',
        'pint>=0.8.0',
        'numba>=0.44.1'
    ],
    extras_require={
        'matplotlib': ['matplotlib>=1.4.2']
    }
)
