from setuptools import setup, find_packages

name = "cloudooo.handler.imagemagick"
version = '0.1'

def read(name):
  return open(name).read()

long_description=(read('README.txt')
                  + '\n' +
                  read('CHANGES.txt')
                 )

install_requires = ["zope.interface",
                    "cloudooo"]

setup(
    name = name,
    version = version,
    author = "Gabriel M. Monnerat",
    author_email = "gabriel@tiolive.com",
    description = "Python Package to handle Images",
    long_description=long_description,
    license = "GPLv3",
    keywords = "python imagemagick",
    classifiers=[
      "Programming Language :: Python :: 2.6",
      "Natural Language :: English",
      "Topic :: Software Development :: Libraries :: Python Modules",
      "License :: OSI Approved :: GNU General Public License (GPL)",
    ],
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    install_requires = install_requires,
    namespace_packages = ["cloudooo", "cloudooo.handler"],
    entry_points="""
    [console_scripts]
    runImageMagickHandlerUnitTest = cloudooo.handler.imagemagick.tests.runImageMagickHandlerUnitTest:run
    """,
    )