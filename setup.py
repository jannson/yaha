from distutils.core import setup  
setup(name='yaha',
      version='0.03.alpha',  
      keywords=('word', 'segmenetation', 'keyword', 'summerize'),
      description='Chinese Words Segementation Utilities',
      license = 'MIT License',
      author='Janson, Yuzheng',  
      author_email='gandancing@gmail.com',  
      url='http://github.com/jannson/yaha',  
      packages=['yaha'],  
      package_dir={'yaha':'yaha'},
      package_data={'yaha':['*.*','analyse/*','dict/*']}
)
