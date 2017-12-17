import struct
import time
import hashlib
from .pinger import ping
from .udp import *

SWT_MAX = 65535     # Max value of Sequence Number, Window Size, Timeout
ACK_WINDOW_MAX = 255    # Max value of ACK Window Size
HEADER_STRUCT = '!BBHHHI'   # For struct.pack and struct.unpack functions


def send_rdtp(d_hostname, data):
    my_socket = get_socket()



def configure(d_ip_list):
    """Using 'pinger' configures Window Size, decides on Bulk ACK, Timeout and if decided on Bulk ACK, ACK Window.
    Takes one argument which is a list of Destination IPs.

    Note that the function calls some functions in which multiprocessing is used."""

    values = ping(d_ip_list)


def connect(d_host, my_socket):
    pass    # TODO: Establish connection with destination

def disconnect(d_host, my_socket):
    pass    # TODO: End connection with destination

def resolve_hostname(hostname):
    pass    # TODO: Resolve hostname using Routing Table
