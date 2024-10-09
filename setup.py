from setuptools import setup

setup(
    name='tiletif',
    url='https://github.com/twheele3/tiletif',
    author='Tim Wheeler',
    author_email='twheele3@uoregon.edu',
    packages=['tiletif'],
    install_requires=['numpy','os','tifffile'],
    version='0.1',
    license='MIT',
    description='A package to tile large N-dimensional tiff files through memmapping for ease of processing.',
    long_description=open('README.txt').read(),
)