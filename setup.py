import os.path

try:
    from setuptools import find_packages, setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import find_packages, setup
from setuptools.command.test import test


def readme():
    try:
        with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as f:
            return f.read()
    except (IOError, OSError):
        return ''


class pytest(test):

    def finalize_options(self):
        test.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        from pytest import main
        errno = main(self.test_args)
        raise SystemExit(errno)


install_requires = [
    'dropbox >= 1.6',
    'libearth == 0.1.0, == dev',
]


setup(
    name='libearth-dropbox',
    description='dropbox repository for Earth Reader',
    long_description=readme(),
    url='http://earthreader.org/',
    author='Earth Reader Project',
    author_email='earthreader' '@' 'librelist.com',
    license='MIT License',
    packages=find_packages(exclude=['tests']),
    install_requires=install_requires,
    dependency_links=[
        'https://github.com/earthreader/libearth/archive/master.zip'
        '#egg=libearth-dev'
    ],
    tests_require=['pytest >= 2.3.0'],
    cmdclass={'test': pytest},
    classifiers=[
        'Development Status :: 1 - Planning',  # FIXME
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Programming Language :: Python :: Implementation :: Stackless',
        'Topic :: Communications',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
        'Topic :: Text Processing :: Markup :: XML'
    ]
)

