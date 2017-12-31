import os

cwd = os.getcwd()

from distutils.core import setup

os.chdir(cwd)

setup(name='rdtp', packages=['source'], package_dir={'source': 'source'},
      package_data={'source': ['./resource/destination.sh', './resource/source.sh', './source/sctp/sctp/client.o',
                               './source/sctp/scpt/server.o']}, scripts=['./resource/destination.sh',
                                                                         './resource/source_t.sh'], )
