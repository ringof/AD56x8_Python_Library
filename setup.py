from setuptools import setup, find_packages

setup(
    name='AD56x8',
    url='https://github.com/ringof/AD56x8_Python_Library',
    author='David Goncalves',
    author_email='davegoncalves@gmail.com',
    packages=find_packages(),
    # Needed for dependencies
    install_requires=['Adafruit-GPIO', 'bitstring'],
    version='0.1',
    license='MIT',
    description='Library for Analog Devices AD56x8 series DACs on a RasPi or BB SBC')

