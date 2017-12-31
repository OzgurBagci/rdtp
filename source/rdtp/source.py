# TODO: Script definition

from multiprocessing import Process, Queue
from math import sqrt
from fractions import Fraction
from resolver import resolve_hostname
from common import *
from pinger import ping
from udp import *
from time import sleep


SWT_MAX = 65535     # Max value of Sequence Number, Window Size, Timeout
ACK_WINDOW_MAX = 255    # Max value of ACK Window Size
HEADER_STRUCT = '!BBHHHI'   # For struct.pack and struct.unpack functions
HEADER_SIZE = 12    # Size of the RDTP Header in bytes.
SOCKET_NUMBER = 1111    # Preferred UDP Port


def send_rdtp(d_hostname, data):
    # TODO: Function definition

    print('Sending RDTP Packet')

    my_socket = get_socket()
    d_dict = resolve_hostname(d_hostname)
    sent = []
    acked = []
    last_seq = 0
    late_seq = 0
    data_index = []

    # Gets IP List from dictionary.
    d_ip_list = []
    for d_ip in list(d_dict.keys()):
        d_ip_list.append(d_ip)
    print('Configuring lines.')
    configuration = configure(d_ip_list)

    connection_list = d_ip_list
    # Removes IPs with 0 packet share assigned from connection and disconnection list.
    for i in range(len(d_ip_list)):
        if configuration[0][i] == 0:
            del connection_list[i]

    d_ip_list = connection_list
    configuration = configure(d_ip_list)

    # Does connection attempts to all IPs of the destination.
    connection_list = []
    results = Queue()
    for i in range(len(d_ip_list)):
        for _ in range(3):  # 3 connection attempts at max
            receive_process = Process(target=wait_response, args=(d_ip_list, results))
            receive_process.start()
            sleep(0.1)
            print('Trying to connect one of the destination IPs...')
            if connect(d_ip_list[i], my_socket, tuple([x[i] for x in configuration])):
                print("Connection Packet sent.")
                receive_process.join()
                ok_break = False
                while not results.empty():
                    result = results.get()
                    if result[1] == d_ip_list[i] and (result[0][0] >> 1) - (result[0][0] >> 2) * 2 == 1 and \
                                            (result[0][0] >> 4) - (result[0][0] >> 5) * 2 == 1:
                        connection_list.append(d_ip_list[i])
                        ok_break = True
                        break
                if ok_break:
                    break

    configuration = configure(connection_list)    # In case an IP is removed reconfigure the links
    d_ip_list = connection_list

    for _ in range(len(d_ip_list)):
        sent.append(0)
        acked.append(0)
        data_index.append([])

    if late_seq < len(data):
        print('Sending data sequence...')

    while late_seq < len(data):
        if not d_ip_list:
            break

        for i in range(len(d_ip_list)):
            if late_seq >= len(data):
                break

            print(d_ip_list, configuration)

            for _ in range(configuration[0][i]):
                if late_seq >= len(data):
                    break

                while configuration[2][i] > sent[i] - acked[i]:
                    if late_seq >= len(data):
                        break

                    print(late_seq, len(data))

                    receive_process = Process(target=wait_response, args=(d_ip_list, results, configuration[3][i]))

                    if (len(data_index[i]) + 1) % configuration[1][i] == 0 or late_seq + 1 == len(data):

                        print('PROPER RECEIVE')

                        receive_process.start()
                        sleep(0.1)

                    bulk_ack = 0
                    if configuration[1][i] > 1:
                        bulk_ack = 1
                    check = checksum(create_header(get_bool((0, 0, 0, 0, 0, 0, bulk_ack, 1)),
                                                   configuration[1][i], configuration[2][i], configuration[3][i],
                                                   last_seq, 0) + data[late_seq])
                    my_data = create_header(get_bool((check % 2, 0, 0, 0, 0, 0, bulk_ack, 1)),
                                            configuration[1][i], configuration[2][i], configuration[3][i], last_seq,
                                            check) + data[late_seq]
                    for _ in range(3):
                        if send_udp(my_socket, d_ip_list[i], SOCKET_NUMBER, my_data):
                            sent[i] += 1
                            last_seq += 1
                            late_seq += 1
                            data_index[i].append(my_data)
                            sleep(0.1)
                            break

                    if late_seq == len(data):

                        finish_check = checksum(create_header(get_bool((0, 0, 1, 0, 0, 1, bulk_ack, 1)),
                                                              configuration[1][i], configuration[2][i],
                                                              configuration[3][i], last_seq, 0))
                        finish_data = create_header(get_bool((finish_check % 2, 0, 1, 0, 0, 1, bulk_ack, 1)),
                                                    configuration[1][i], configuration[2][i], configuration[3][i],
                                                    last_seq, finish_check)
                        for ip in d_ip_list:
                            for _ in range(10):
                                send_udp(my_socket, ip, SOCKET_NUMBER, finish_data)

                    if len(data_index[i]) % configuration[1][i] == 0 or late_seq == len(data):
                        receive_process.join()
                        while True:
                            no_configure = False
                            ack_result = None
                            while not results.empty():
                                ack_result = results.get()

                                print(ack_result)

                                if ack_result[1] != d_ip_list[i]:
                                    continue
                                break

                            if ack_result is None or ack_result[1] == d_ip_list[i] and (ack_result[0][0] >> 4) - \
                                (ack_result[0][0] >> 5) * 2 != 1:
                                for _ in range(10):
                                    my_break = False

                                    fail_results = Queue()

                                    fail_receive = Process(target=wait_response, args=(d_ip_list, fail_results,
                                                                                       configuration[3][i]))

                                    print('FAIL RECEIVE')

                                    for re_packet in data_index[i][len(data_index[i]) - configuration[1][i]:]:
                                        sleep(0.1)
                                        send_udp(my_socket, d_ip_list[i], SOCKET_NUMBER, re_packet)
                                    fail_receive.start()
                                    sleep(0.1)
                                    fail_receive.join()
                                    while not fail_results.empty():
                                        my_ack_result = fail_results.get()
                                        if my_ack_result[1] == d_ip_list[i] and (my_ack_result[0][0] >> 4) - \
                                                        (my_ack_result[0][0] >> 5) * 2 == 1:
                                            my_break = True
                                            no_configure = True
                                            acked[i] += configuration[1][i]
                                            last_seq = 0
                                            break

                                    if my_break:
                                        break

                            else:
                                acked[i] += configuration[1][i]
                                last_seq = 0
                                break

                            if no_configure:
                                break
                            late_seq -= configuration[1][i]
                            data_index[i] = data_index[i][:len(data_index[i]) - configuration[1][i]]
                            configuration = configure(d_ip_list)
                            break

    # Does disconnection attempts to all IPs of the destination.
    for i in range(len(d_ip_list)):
        receive_process = Process(target=wait_response, args=(connection_list, results))
        receive_process.start()
        sleep(0.1)
        for _ in range(3):  # 3 disconnection attempts at max
            print('Trying to disconnect one of the IPs')
            if disconnect(d_ip_list[i], my_socket, tuple([x[i] for x in configuration])):
                receive_process.join()
                ok_break = False
                while not results.empty():
                    result = results.get()
                    # If disconnect fails 3 times it is assumed that host is down else it breaks in order not to do
                    # unnecessary calculations.
                    if result[1] == d_ip_list[i] and (result[0][0] >> 3) - (result[0][0] >> 4) * 2 == 1 and \
                                            (result[0][0] >> 4) - (result[0][0] >> 5) * 2 == 1:
                        ok_break = True
                        break
                if ok_break:
                    break


def configure(d_ip_list):
    """Using 'ping' it configures Window Size, decides on Bulk ACK, Timeout and if decided on Bulk ACK, ACK Window.
    Takes one argument which is a list of Destination IPs.

    Note that the function calls some functions in which multiprocessing is used.

    For more information about this function refer to README."""

    values = ping(d_ip_list)
    tmp = []
    for d in d_ip_list:
        try:
            tmp.append(values[d])
        except KeyError:    # Appends 100% loss if no ping info is received from that IP, excludes that IP
            tmp.append((4001, 4001, 100, 0))    # ms is 4001 since it waits 4 seconds
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
        if x == 100:    # If loss is 100% in 2nd one, makes ms 0 in 1st one in order not to give any packet to 2nd line
            n = 0
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


def wait_response(d_ip_list, my_queue, timeout=4):
    """Should run as a thread. Returns unpacked headers. It must be noted it is for receiving responses to data sent
    only and because of it, this function does not return data. Only argument it takes is the IP List of Destination."""

    print('Waiting for ACK Response')
    m_socket = get_socket()
    m_socket.settimeout(timeout)
    m_socket.bind(('', SOCKET_NUMBER))
    result = None
    result = receive_udp(m_socket, SOCKET_NUMBER)
    if not result:
        print('ACK response did not received.')
        return
    data, addr = result

    if addr[0] in d_ip_list:
        print('A response received.')
        unpacked_data = struct.unpack(HEADER_STRUCT, data[:HEADER_SIZE])     # Takes the header and unpacks it
        if checksum(data) == unpacked_data[5] and unpacked_data[0] - (unpacked_data[0] >> 1) * 2 == \
                        unpacked_data[5] % 2:
            my_queue.put((unpacked_data, addr[0]))

        print(unpacked_data, checksum(data), unpacked_data[5], unpacked_data[0] - (unpacked_data[0] >> 1) * 2, unpacked_data[5] % 2)

    m_socket.close()
