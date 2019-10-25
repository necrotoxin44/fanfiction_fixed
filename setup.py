from distutils.core import setup
setup(
  name = 'fanfictionfixed',
  packages = ['fanfictionfixed'],
  version = '0.1.1',
  description = 'Scraper for http://fanfiction.net',
  author = 'Smitha Milli',
  author_email = 'smitha.milli@gmail.com',
  url = 'https://github.com/slugking/fanfiction-fixed',
  download_url = 'https://github.com/slugking/fanfiction-fixed/tarball/0.1.1',
  keywords = ['nlp'],
  classifiers = [],
  install_requires = [
    'bs4',
    'requests'
  ]
)
