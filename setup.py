from distutils.core import setup  
setup(name='yaha',
      version='0.01.alpha',  
      description='Chinese Words Segementation Utilities',  
      author='Janson, Yuzheng',  
      author_email='gandancing@gmail.com',  
      url='http://github.com/jannson/yaha',  
      packages=['yaha'],  
      package_dir={'yaha':'yaha'},
      package_data={'yaha':['*.*','analyse/*','dict/*']}
)
