import struct
import time
from .pinger import *
from .udp import *


def send_rdtp(d_hostname, d_port, data):
    my_socket = get_socket()
