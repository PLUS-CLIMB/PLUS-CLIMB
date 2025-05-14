from setuptools import setup, find_packages

setup(
    name='rsat_utils',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'rasterio',
        'matplotlib',
        'numpy'
    ],
    author='Khizer Zakir',
    description='Remote sensing utilities for loading bands, computing indices, and plotting.',
    keywords='remote sensing raster landsat ndvi rasterio',
)
