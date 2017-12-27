"""This script consist of functions which are used both in source and destination scrits."""

import struct
from hashlib import blake2b


HEADER_STRUCT = '!BBHHHI'   # For struct.pack and struct.unpack functions
HEADER_SIZE = 12    # Size of the RDTP Header in bytes.


def get_bool(my_bool_tuple):
    """Gives a number consists of booleans of RDTP Header. Argument type has more than 7 elements. Returns a integer."""

    check_bool, my_open, finish, close, ack, nack, bulk_ack, seq_num_import = my_bool_tuple
    return check_bool + (my_open << 1) + (finish << 2) + (close << 3) + (ack << 4) + (nack << 5) + \
           (bulk_ack << 6) + (seq_num_import << 7)


def create_header(bools, ack_window, window, timeout, seq_number, check):
    """Creates header of RDTP. Returns byte string."""

    return struct.pack(HEADER_STRUCT, bools, ack_window, window, timeout, seq_number, check)


def checksum(packet):
    """Calculates checksum with 4 byte digest size for RDTP Header. Returns a integer."""

    unpacked_header = struct.unpack(HEADER_STRUCT, packet[:HEADER_SIZE])
    bytes_data = packet[HEADER_SIZE:]
    if unpacked_header[0] - (unpacked_header[0] >> 1) * 2 == 1:
        initial_bool = (unpacked_header[0] >> 1) * 2
    else:
        initial_bool = unpacked_header[0]
    initial_header = create_header(initial_bool, unpacked_header[1], unpacked_header[2], unpacked_header[3],
                                   unpacked_header[4], 0)
    initial_packet = initial_header + bytes_data
    hash4 = blake2b(digest_size=4)     # Uses built in blake2b Hash with 4 byte digest size
    hash4.update(initial_packet)
    return int(hash4.hexdigest(), 16)  # Returns an integer since it is needed for 'struct.pack'
