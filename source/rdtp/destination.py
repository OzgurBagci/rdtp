# TODO: Script definition

from .common import *
from .udp import *

HEADER_STRUCT = '!BBHHHI'   # For struct.pack and struct.unpack functions
HEADER_SIZE = 12    # Size of the RDTP Header in bytes.
SOCKET_NUMBER = 1111    # Preferred UDP Port


def receive_rdtp(bind_ip, my_queue):
    # TODO: Function definition

    my_socket = get_socket()
    my_socket.bind((bind_ip, SOCKET_NUMBER))

    connected = False

    while True:
        packet = receive_udp(my_socket, SOCKET_NUMBER)

        if packet is None:
            continue

        data, addr = packet
        unpacked_header = struct.unpack(HEADER_STRUCT, data[:HEADER_SIZE])
        bytes_data = data[HEADER_SIZE:]

        if checksum(data) != unpacked_header[5] or unpacked_header[0] - (unpacked_header[0] >> 1) * 2 != \
                        unpacked_header[5] % 2:
            continue

        if (unpacked_header[0] >> 1) - (unpacked_header[0] >> 2) * 2 == 1:
            ack_window = unpacked_header[1]
            window = unpacked_header[2]
            timeout = unpacked_header[3]
            bulk_ack = 0
            if ack_window > 1:
                bulk_ack = 1
            check = \
                checksum(create_header(get_bool((0, 1, 0, 0, 1, 0, bulk_ack, 0)), ack_window, window, timeout, 0, 0))
            check_bool = check % 2
            ack_header = \
                create_header(get_bool((check_bool, 1, 0, 0, 1, 0, bulk_ack, 0)), ack_window, window, timeout, 0, check)
            for _ in range(3):  # Max 3 attempts to send ACK Packet
                if send_udp(my_socket, addr[1][0], SOCKET_NUMBER, ack_header):
                    connected = True
                    break
            continue

        if not connected:
            continue

        if (unpacked_header[0] >> 7) == 1:
            my_queue.put((bind_ip, addr, unpacked_header, bytes_data))
            continue

        if (unpacked_header[0] >> 3) - (unpacked_header[0] >> 4) * 2 == 1:
            ack_window = unpacked_header[1]
            window = unpacked_header[2]
            timeout = unpacked_header[3]
            bulk_ack = 0
            if ack_window > 1:
                bulk_ack = 1
            check = \
                checksum(create_header(get_bool((0, 0, 0, 1, 1, 0, bulk_ack, 0)), ack_window, window, timeout, 0, 0))
            check_bool = check % 2
            ack_header = \
                create_header(get_bool((check_bool, 0, 0, 1, 1, 0, bulk_ack, 0)), ack_window, window, timeout, 0, check)
            for _ in range(3):  # Max 3 attempts to send ACK Packet
                if send_udp(my_socket, addr[1][0], SOCKET_NUMBER, ack_header):
                    break
            break


def process_rdtp(my_socket, my_queue):
    # TODO: Function definition

    packets = []

    while True:
        finish = False
        packets_done = False

        while not my_queue.empty():
            packet = my_queue.get()
            unpacked_header = packet[2]
            my_socket.bind(packet[0], SOCKET_NUMBER)

            if (unpacked_header[0] >> 2) - (unpacked_header[0] >> 3) * 2 == 1:
                finish = True

            # TODO: Process Packets

            if finish and packets_done:
                addr = packet[1]
                ack_window = unpacked_header[1]
                window = unpacked_header[2]
                timeout = unpacked_header[3]
                bulk_ack = 0
                if ack_window > 1:
                    bulk_ack = 1
                check = \
                    checksum(
                        create_header(get_bool((0, 0, 1, 0, 1, 0, bulk_ack, 0)), ack_window, window, timeout, 0, 0))
                check_bool = check % 2
                ack_header = \
                    create_header(
                        get_bool((check_bool, 0, 1, 0, 1, 0, bulk_ack, 0)), ack_window, window, timeout, 0, check)
                for _ in range(3):  # Max 3 attempts to send ACK Packet
                    if send_udp(my_socket, addr[1][0], SOCKET_NUMBER, ack_header):
                        break
                break

        if finish and packets_done:
            break
