import os.path

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


import replaylib

           
setup(name='replaylib',
      version=replaylib.__version__,
      author="Scott Torborg, Mike Spindel",
      author_email="storborg@mit.edu",
      license="GPL",
      keywords="testing web replay",
      url="http://github.com/storborg/replaylib",
      description='Record and replay httplib actions for testing.',
      packages=find_packages(exclude=['ez_setup', 'tests']),
      long_description=read('README.rst'),
      test_suite='nose.collector',
      zip_safe=False,
      classifiers=[
          "Development Status :: 3 - Alpha",
          "License :: OSI Approved :: GNU General Public License (GPL)",
          "Intended Audience :: Developers",
          "Topic :: Software Development :: Testing",
          "Topic :: Internet",
          "Natural Language :: English",
          "Programming Language :: Python"],
      entry_points="""
      [nose.plugins.0.10]
      replaylib = replaylib.noseplugin:ReplayLibPlugin
      """)
