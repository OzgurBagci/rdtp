# TODO: Script definition

from multiprocessing import Process, Queue
from common import *
from udp import *
import time
import pickle

HEADER_STRUCT = '!BBHHHI'   # For struct.pack and struct.unpack functions
HEADER_SIZE = 12    # Size of the RDTP Header in bytes.
SOCKET_NUMBER = 1111    # Preferred UDP Port


def receive_rdtp(bind_ip, packets_queue):
    # TODO: Function definition

    my_socket = get_socket()
    my_socket.bind((bind_ip, SOCKET_NUMBER))

    my_queue = Queue()
    processing = Process(target=process_rdtp, args=(my_socket, my_queue, packets_queue))
    processing.start()

    connected = False

    while True:
        print('Receiving RDTP Packet')
        packet = receive_udp(my_socket, SOCKET_NUMBER)

        if not packet:
            continue

        data, addr = packet
        unpacked_header = struct.unpack(HEADER_STRUCT, data[:HEADER_SIZE])
        bytes_data = data[HEADER_SIZE:]
        if checksum(data) != unpacked_header[5] or unpacked_header[0] - (unpacked_header[0] >> 1) * 2 != \
                        unpacked_header[5] % 2:
            print('Packet arrived, checksum is not matching.')
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
                if send_udp(my_socket, addr[0], SOCKET_NUMBER, ack_header):
                    connected = True
                    break
            continue

        if not connected:
            continue

        if (unpacked_header[0] >> 7) == 1:
            my_queue.put(pickle.dumps((bind_ip, addr, unpacked_header, bytes_data)))
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
                if send_udp(my_socket, addr[0], SOCKET_NUMBER, ack_header):
                    break
            break

    processing.join()
    packets_queue.put(pickle.dumps(None))


def process_rdtp(my_socket, my_queue, packet_queue):
    # TODO: Function definition

    expected_seq = 0
    packets = []

    finish = False
    packets_done = False

    while True:
        while not my_queue.empty():
            print('Processing RDTP Packet')
            packet = pickle.loads(my_queue.get())

            packet_queue.put(pickle.dumps(packet))

            unpacked_header = packet[2]
            if packet[2][4] not in [x[2][4] for x in packets]:
                packets.append(packet)

            if (unpacked_header[0] >> 2) - (unpacked_header[0] >> 3) * 2 == 1:
                finish = True
            sorted(packets, key=lambda x: x[2][4])

            print(len(packets), unpacked_header[4] + 1)

            if len(packets) % unpacked_header[1] == 0 and (unpacked_header[4] + 1) % unpacked_header[1] == 0 \
                    or finish:
                packets_done = True
                bulk_ack = 0
                if unpacked_header[1] > 1:
                    bulk_ack = 1
                check = checksum(
                    create_header(
                        get_bool((0, 0, 0, 0, 1, 0, bulk_ack, 1)), unpacked_header[1], unpacked_header[2],
                        unpacked_header[3], unpacked_header[4], 0))
                check_bool = check % 2
                ack_header = \
                    create_header(get_bool((check_bool, 0, 0, 0, 1, 0, bulk_ack, 1)),
                                  unpacked_header[1], unpacked_header[2], unpacked_header[3], unpacked_header[4], check)
                if finish:
                    for _ in range(9):
                        time.sleep(0.1)
                        send_udp(my_socket, packet[1][0], SOCKET_NUMBER, ack_header)
                for _ in range(3):  # Max 3 attempts to send ACK Packet
                    time.sleep(0.1)
                    if send_udp(my_socket, packet[1][0], SOCKET_NUMBER, ack_header):
                        packets = []

                        break

            if finish and packets_done:
                break

        if finish and packets_done:
            break
