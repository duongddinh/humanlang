# setup.py

from setuptools import setup, find_packages

setup(
    name="humanlang",
    version="3.0.0", 
    packages=find_packages(),
    author="Duong Dinh",
    author_email="bobdinh139@gmail.com",
    description="An object-oriented, asynchronous language with advanced networking tools.",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/duongddinh/humanlang", 
    python_requires='>=3.7',
    install_requires=[
        'aiohttp>=3.8.0',
        'scapy>=2.5.0', 
    ],
    entry_points={
        'console_scripts': [
            'humanlang=humanlang.__main__:main',
        ],
    },
)