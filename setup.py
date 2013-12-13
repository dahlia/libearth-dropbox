import os.path

try:
    from setuptools import find_packages, setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import find_packages, setup


def readme():
    try:
        with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as f:
            return f.read()
    except (IOError, OSError):
        return ''


install_requires = [
    'dropbox >= 1.6',
    'libearth == 0.1.0',
]


setup(
    name='libearth-dropbox',
    description='Dropbox repository for Earth Reader',
    long_description=readme(),
    url='http://earthreader.org/',
    author='Earth Reader Project',
    author_email='earthreader' '@' 'librelist.com',
    license='MIT License',
    packages=find_packages(),
    install_requires=install_requires,
    dependency_links=[
        'https://github.com/earthreader/libearth/archive/master.zip'
        '#egg=libearth-dev'
    ],
    entry_points='''
        [libearth.repositories]
        dropbox = libearth_dropbox:DropboxRepository
    '''
)

