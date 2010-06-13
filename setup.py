try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

           
setup(name='replaylib',
      version='0.1',
      description='Record and replay httplib actions for testing.'
      packages=find_packages(exclude=['ez_setup', 'tests']),
      include_package_data=True,
      package_data={
          'replaylib': ['static/*', 'templates/*']},
      test_suite='nose.collector',
      zip_safe=False)
