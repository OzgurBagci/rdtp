"""The whole point of this script is to ping the receiver and decide on configurations of RDTP such as Window Size,
Bulk ACK... It may ping more than 1 receivers with 1 function call."""

from queue import Queue
import socket
import struct
import time
import threading


IP_STRUCT = '!BBHHHBBH4s4s' # For struct.pack and struct.unpack functions.
HEAD_STRUCT = '!BBHHH'  # For struct.pack and struct.unpack functions.
ID_OFF = 24     # Until byte 24 it is IP Header.
PAYLOAD_OF = 28     # Until byte 28 it is IP and ICMP Headers.


def checksum(data):
    """"Calculates the ICMP checksum. Takes 1 argument which is raw will be sent. Received data is autocalculated by
    OS. Because we specify 'socket.IPPROTO_ICMP' while receiving it is being calculated. Because we are specifying
    'socket.SOCK_RAW' while sending we need to create the ICMP Header."""
    final = 0
    for i in range(0, len(data), 2):
        tmp = (data[i] << 8) + data[i + 1]
        final = ((final + tmp) & 0xffff) + (final >> 16)
    return ~final & 0xffff


def ping_it(d_address_list):
    """This function sends ping requests to list of IPs specified in the only argument this function takes.
    This function should called as a thread coordinated with 'receive_ping' function which should be another thread."""

    # ID field created for distinguishing packets from each other in order to calculate the latency.
    id_to_address = {}
    last_id = None

    # Trying to create a raw socket for ICMP.
    try:
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    except socket.error:
        raise Exception('Cannot create ICMP Socket for pinging the destination. Please ensure that you are root'
                        'and try again.')

    # Sending Ping Packet to specified destinations.
    if last_id is None:
        last_id = int(time.time()) & 0xffff
    for d_address in d_address_list:
        last_id = (last_id + 1) & 0xffff
        id_to_address[last_id] = d_address
        initial_header = bytearray(struct.pack(HEAD_STRUCT, 8, 0, 0, last_id, 0))
        payload = struct.pack("d", time.time())
        my_checksum = checksum(initial_header + payload)
        final_header = bytearray(struct.pack(HEAD_STRUCT, 8, 0, my_checksum, last_id, 0))
        packet = final_header + payload
        my_socket.sendto(packet, (d_address, 0))
    my_socket.close()
    return id_to_address


def receive_ping(d_address_list, my_queue):
    """This function receives ping requests to list of IPs specified in the only argument this function takes.
    This function should called as a thread coordinated with 'ping_it' function which should be the earlier thread.

    You should wait until threads close seconds for return since it waits at max 10 seconds for the responses and it
    is a thread."""

    timeout = 10    # Timeout is default and 10 seconds at max. Lesser if received a response from all IPs in the list.
    start_time = time.time()
    packets = []

    results = {}
    for d in d_address_list:
        results[d] = []

    timestamp_size = struct.calcsize('d')

    # Trying to create a raw socket for ICMP.
    try:
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    except socket.error:
        raise Exception('Cannot create ICMP Socket for pinging the destination. Please ensure that you are root'
                        'and try again.')

    # In case socket may time out or in non-blocking mode no more data left, we cover it with try-except block.
    while d_address_list and time.time() - timeout < start_time:
        try:
            my_socket.settimeout(timeout)
            i = len(d_address_list)
            while i >= 0:
                packet = my_socket.recv(64)  # Buffer size set to small power of 2 as suggested in documentation.
                packets.append((packet, time.time()))
                my_socket.settimeout(0)     # Since first packet is received set socket to non-blocking mode.
                i = i - 1
        except socket.timeout or socket.error.errno == 11 or socket.error.errno == 10035:
            pass

    # Unpack received packets and add it to results dictionary.
    for pack, recv_time in packets:
        ip_header = pack[:HEAD_STRUCT]
        destination_ip = socket.inet_ntoa(struct.unpack(ip_header)[8])  # 8th element is source IP in IP header.
        if destination_ip in d_address_list:
            packet_id = (pack[ID_OFF] << 8) + pack[ID_OFF + 1]
            send_time = struct.unpack('d', pack[:timestamp_size])[0]
            results[destination_ip].append((packet_id, send_time, recv_time))

    my_queue.put(results)


def ping(d_ip_list, times):
    """Pings the given destination IPs, in first argument, times of second argument. Creates a queue for async
    appending the results from threads. Creates 2 threads, one for 'ping_it' function and one for 'receive_ping'
    function. Waits for threads to finish before starting the next loop or ending it."""
    results = Queue()

    # Creates threads for receive and send. Receive thread created first in order to prevent missing packages.
    for i in range(times):
        sender_thread = threading.Thread(target=ping_it(d_ip_list))
        receiver_thread = threading.Thread(target=receive_ping(d_ip_list, results))
        receiver_thread.start()
        sender_thread.start()
        sender_thread.join()
        receiver_thread.join()

    # Calculates results based on our query. Dumps it to a list.
    total_ping = {}
    for d in d_ip_list:
        total_ping[d] = []
    while not result.empty():
        result = results.get();
        for d in d_ip_list:
            total_ping[d].append((result[d][0], result[d][2] - result[d][1]))

    # Iterates over the results and calculates various characteristics like loss and latency.
    final_results = {}
    for d in d_ip_list:
        total_ping[d].sort(key=lambda t: t[0])
        unsorted = 0
        avg_ping = 0
        packet_count = 0
        for i in range(len(total_ping[d])):
            if total_ping[d][i][0] - total_ping[d][i-1][0] != 1:
                unsorted += 1
                avg_ping += total_ping[d][i][1]
                packet_count += 1
        loss = times - packet_count
        avg_ping /= packet_count
        avg_ping = int(avg_ping * 1000)    # To convert it from second to millisecond and dump the decimals
        loss_percent = loss / times     # Turns Loss into 0.xx format
        unsorted_percent = unsorted / times     # Turns Unsorted Packages into 0.xx format

        final_results[d] = (avg_ping, loss_percent, unsorted_percent)

    return final_results
