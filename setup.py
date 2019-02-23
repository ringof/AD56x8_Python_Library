from setuptools import setup

setup(
    name='AD56x8 Python Library',
    url='https://github.com/ringof/AD56x8_Python_Library',
    author='David Goncalves',
    author_email='davegoncalves@gmail.com',
    packages=['AD56x8_Python_Library'],
    # Needed for dependencies
    install_requires=['Adafruit-GPIO', 'bitstring'],
    version='0.1',
    license='MIT',
    description='An example of a python package from pre-existing code',
    long_description=open('README.md').read(),
)
