"""The whole point of this script is to ping the receiver and decide on configurations of RDTP such as Window Size,
Bulk ACK... It may ping more than 1 receivers with 1 function call."""

from multiprocessing import Process, Queue
import socket
import struct
import time


IP_STRUCT = '!BBHHHBBH4s4s'     # For struct.pack and struct.unpack functions
HEAD_STRUCT = '!BBHHH'  # For struct.pack and struct.unpack functions
IP_OFF = 20     # Until IP_OFF it is IP Header
PAYLOAD_OF = 28     # Until byte 28 it is IP and ICMP Headers

last_id = None


def checksum(data):
    """"Calculates the ICMP checksum. Takes 1 argument which is raw will be sent. Received data is autocalculated by
    OS. Because we specify 'socket.IPPROTO_ICMP' while receiving it is being calculated. Because we are specifying
    'socket.SOCK_RAW' while sending we need to create the ICMP Header."""
    final = 0
    for i in range(0, len(data), 2):
        tmp = (data[i] << 8) + data[i + 1]
        final = ((final + tmp) & 0xffff) + ((final + tmp) >> 16)
    return ~final & 0xffff


def ping_it(d_address_list, my_socket):
    """This function sends ping requests to list of IPs specified in the only argument this function takes.
    This function should called as sync coordinated with 'receive_ping' function which should be a process."""

    global last_id

    last_id += 1

    # Sends Ping Packet to specified destinations.
    seq_number = 0
    for d_address in d_address_list:
        seq_number += 1
        initial_header = bytearray(struct.pack(HEAD_STRUCT, 8, 0, 0, last_id, seq_number))
        payload = struct.pack("d", time.time())
        my_checksum = checksum(initial_header + payload)
        final_header = bytearray(struct.pack(HEAD_STRUCT, 8, 0, my_checksum, last_id, seq_number))
        packet = final_header + payload
        my_socket.sendto(packet, (d_address, 0))


def receive_ping(d_address_list, my_queue):
    """This function receives ping requests to list of IPs specified in the only argument this function takes.
    This function should called as a process coordinated with 'ping_it' function which should be called sync.

    You should wait until processes close for return since it waits at max 4 seconds for the responses and it
    is running parallel to main process."""

    timeout = 4    # Timeout is default and 4 seconds at max. Lesser if received a response from all IPs in the list
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
        raise Exception('Cannot create ICMP Socket. Please ensure that you are root and try again.')

    # In case socket may time out or in non-blocking mode no more data left, we cover it with try-except block.
    i = 1
    while time.time() - timeout < start_time and i <= 64 * len(d_address_list):
        try:
            my_socket.settimeout(timeout)
            packet = my_socket.recvfrom(64)
            # Checks for duplicates
            if packet and not list(filter(lambda x: x[0][IP_OFF:] == packet[0][IP_OFF:], packets)):
                packets.append((packet[0], time.time()))
                i += 1
        except socket.timeout:
            pass

    # Unpacks received packets and adds it to results dictionary.
    for pack, recv_time in packets:
        ip_header = pack[:IP_OFF]
        # The portion that is source IP in IP header processed by 'inet_ntoa'
        destination_ip = socket.inet_ntoa(struct.unpack(IP_STRUCT, ip_header)[8])
        if destination_ip in d_address_list:
            packet_id = struct.unpack(HEAD_STRUCT, pack[IP_OFF:PAYLOAD_OF])[3]
            send_time = struct.unpack('d', pack[PAYLOAD_OF:PAYLOAD_OF + timestamp_size])[0]
            results[destination_ip].append((packet_id, send_time, recv_time))

    my_socket.close()

    # Removes empty lists in dictionary.
    for key in list(results.keys()):
        if not results[key]:
            del results[key]
    if results:
        my_queue.put(results)


def ping(d_ip_list):
    """Pings the given destination IPs, in only argument, times of 64. Creates a queue for async appending the results
    from threads. Creates 2 threads, one for 'ping_it' function and one for 'receive_ping' function. Waits for threads
    to finish before starting the next loop or ending it."""

    global last_id

    # Trying to create a raw socket for ICMP.
    try:
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    except socket.error:
        raise Exception('Cannot create ICMP Socket. Please ensure that you are root and try again.')

    results = Queue()

    receive_process = Process(target=receive_ping, args=(d_ip_list, results))
    receive_process.start()
    last_id = 0
    for i in range(64):
        ping_it(d_ip_list, my_socket)
        time.sleep(0.01)     # Sleeps in order to give time to receiver process to calculate data
    receive_process.join()

    my_socket.close()

    # In order not to do calculations if Queue is empty since it may cause errors.
    if results.empty():
        return

    # Calculates results based on our query. Dumps it to a list.
    total_ping = {}
    while not results.empty():
        result = results.get()
        for d in result.keys():
            total_ping[d] = []
            for res in result[d]:
                total_ping[d].append((res[0], res[2] - res[1]))

    # Iterates over the results and calculates various characteristics like loss and latency.
    final_results = {}
    for d in total_ping.keys():
        unsorted = 0
        avg_ping = 0
        packet_count = 0
        mad_max = 0     # Reference to the movie Mad Max, Maximum Latency
        for i in range(len(total_ping[d])):
            if total_ping[d][i][0] < total_ping[d][i-1][0]:
                unsorted += 1   # A naive implementation for approximating what is the condition of sorting on link
            avg_ping += total_ping[d][i][1]
            mad_max = max(mad_max, int(total_ping[d][i][1] * 1000))     # Converts Max Latency to ms
            packet_count += 1
        loss = 64 - packet_count
        avg_ping /= packet_count
        avg_ping = int(avg_ping * 1000)    # To convert it from second to millisecond and dump the decimals
        loss_percent = (loss / 64) * 100    # Turns Loss into 0.xx format
        unsorted_percent = ((unsorted - 1) / 64) * 100   # Turns Unsorted Packages into 0.xx format

        final_results[d] = (avg_ping, mad_max, loss_percent, unsorted_percent)

    return final_results
