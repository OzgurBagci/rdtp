import struct
import time
import hashlib
from math import sqrt
from fractions import Fraction
from .resolver import resolve_hostname
from .pinger import ping
from .udp import *


SWT_MAX = 65535     # Max value of Sequence Number, Window Size, Timeout
ACK_WINDOW_MAX = 255    # Max value of ACK Window Size
HEADER_STRUCT = '!BBHHHI'   # For struct.pack and struct.unpack functions


def send_rdtp(d_hostname, data):
    my_socket = get_socket()
    resolve_hostname(data)


def configure(d_ip_list):
    """Using 'pinger' configures Window Size, decides on Bulk ACK, Timeout and if decided on Bulk ACK, ACK Window.
    Takes one argument which is a list of Destination IPs.

    Note that the function calls some functions in which multiprocessing is used.

    For more information about this function refer to README."""

    values = ping(d_ip_list)

    bulk_size = []
    for value in values:
        bulk_size.append(round(10/sqrt(value[2])))
    bulk_size = tuple(bulk_size)

    packet_quantity = []
    for i in range(len(values) - 1):
        x = values[i][2]
        m = values[i][0]
        y = values[i + 1][2]
        n = values[i + 1][0]
        a_divided_b = Fraction(n * (100 + y)) / Fraction(m * (100 + x))
        if not packet_quantity:
            packet_quantity.append(a_divided_b.numerator)
            packet_quantity.append(a_divided_b.denominator)
        else:
            packet_quantity.append(a_divided_b.denominator)
            multiplier = packet_quantity.append(a_divided_b.numerator) / packet_quantity[i]
            if multiplier < 1:
                packet_quantity[i + 1] /= multiplier
            else:
                for j in range(i):
                    packet_quantity[j] *= multiplier
    packet_quantity = tuple(packet_quantity)

    timeout = []
    for value in values:
        my_value = value[2]
        if my_value > 12:
            timeout.append(1)
        elif my_value > 6:
            timeout.append(2)
        elif my_value > 4:
            timeout.append(3)
        elif my_value > 3:
            timeout.append(4)
        elif my_value > 2:
            timeout.append(5)
        elif my_value > 1:
            timeout.append(7)
        else:
            timeout.append(9)
    timeout = tuple(timeout)

    window_size = []
    for ack_window in bulk_size:
        window_size.append(ack_window * ack_window)
    window_size = tuple(window_size)

    return packet_quantity, bulk_size, window_size, timeout


def connect(d_host, my_socket):
    pass    # TODO: Establish connection with destination


def disconnect(d_host, my_socket):
    pass    # TODO: End connection with destination
