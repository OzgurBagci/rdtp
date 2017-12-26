import struct
import time
from math import sqrt
from fractions import Fraction
from .resolver import resolve_hostname
from .common import *
from .pinger import ping
from .udp import *


SWT_MAX = 65535     # Max value of Sequence Number, Window Size, Timeout
ACK_WINDOW_MAX = 255    # Max value of ACK Window Size
HEADER_STRUCT = '!BBHHHI'   # For struct.pack and struct.unpack functions
HEADER_SIZE = 12    # Size of the RDTP Header in bytes.
SOCKET_NUMBER = 1111    # Preferred UDP Port


def send_rdtp(d_hostname, data):
    my_socket = get_socket()
    d_dict = resolve_hostname(data)

    # Gets IP List from dictionary.
    d_ip_list = []
    for d_ip in list(d_dict.keys()):
        d_ip_list.append(d_ip)

    configuration = configure(d_ip_list)

    # Does connection attempts to all IPs of the destination.
    will_remove = []
    for i in range(len(d_ip_list)):
        if not connect(d_ip_list[i], my_socket, tuple([x[i] for x in configuration])):
            will_remove.append(d_ip_list[i])

    d_ip_list = filter(lambda x: x not in will_remove, d_ip_list)   # Removes IPs with connection attempt failed

    


def configure(d_ip_list):
    """Using 'pinger' configures Window Size, decides on Bulk ACK, Timeout and if decided on Bulk ACK, ACK Window.
    Takes one argument which is a list of Destination IPs.

    Note that the function calls some functions in which multiprocessing is used.

    For more information about this function refer to README."""

    values = ping(d_ip_list)
    tmp = []
    for d in d_ip_list:
        tmp.append(values[d])
    values = tmp

    bulk_size = []
    for value in values:
        if value[2] == 0.:  # Prevents zero division error
            bulk_size.append(ACK_WINDOW_MAX)
            continue
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


def connect(d_host, my_socket, configuration):
    """Tries to connect to the given host while passing the configuration to destination. Returns True on success and
    False on failure."""
    if configuration[1] > 1:
        bulk_ack = 1
    else:
        bulk_ack = 0
    check = checksum(create_header(get_bool((0, 1, 0, 0, 0, 0, bulk_ack, 0)), configuration[1], configuration[2],
                                   configuration[3], 0, 0))
    check_bool = check % 2
    data = create_header(get_bool((check_bool, 1, 0, 0, 0, 0, bulk_ack, 0)), configuration[1], configuration[2],
                         configuration[3], 0, check)
    return send_udp(my_socket, d_host, SOCKET_NUMBER, data)


def disconnect(d_host, my_socket, configuration):
    """Tries to disconnect to the given host while passing the configuration to destination. Returns True on success and
    False on failure."""
    if configuration[1] > 1:
        bulk_ack = 1
    else:
        bulk_ack = 0
    check = checksum(create_header(get_bool((0, 0, 0, 1, 0, 0, bulk_ack, 0)), configuration[1], configuration[1],
                                   configuration[3], 0, 0))
    check_bool = check % 2
    data = create_header(get_bool((check_bool, 0, 0, 1, 0, 0, bulk_ack, 0)), configuration[1], configuration[1],
                         configuration[3], 0, check)
    return send_udp(my_socket, d_host, SOCKET_NUMBER, data)


def wait_response(d_ip_list):
    """Should run as a thread. Returns unpacked headers. It must be noted it is for receiving responses to data sent
    only and because of it, this function does not return data. Only argument it takes is the IP List of Destination."""

    m_socket = get_socket()
    result = receive_udp(m_socket, SOCKET_NUMBER)
    if not result:
        return False
    data, addr = result
    if addr[0] in d_ip_list:
        data = struct.unpack(HEADER_STRUCT, data[:HEADER_SIZE])     # Takes the header and unpacks it
        return data
