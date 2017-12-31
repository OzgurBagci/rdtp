# TODO: Script definition

import socket
from time import time


def get_socket():
    """Gives the UDP socket for use. We don't create the socket in 'send_udp' because if we do that, every time we
    send a package we need to create a socket."""

    print('Creating UDP Socket...')

    try:
        return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except socket.error:
        raise Exception('Cannot create UDP Socket for sending the data. Please ensure that you are root and try again.')


def send_udp(my_socket, d_ip, d_port, data):
    """Sends the UDP Package. Takes the socket as first argument. Second argument is Destination IP and the third is
    Destination Port. Lastly, Raw Data is the final argument."""

    print('Sending UDP Packet...')

    try:
        my_socket.sendto(data, (d_ip, d_port))
        print('UDP Packet sent.')
        return True
    except socket.error:
        print('Error while sending UDP Packet')
        return False


def receive_udp(my_socket, s_port):
    """Receives UDP Package from source. If it does not receive a packet until default timeout it returns False. Takes
    socket as first argument and Source Port as second argument."""

    print('Receiving UDP Packet')
    try:
        packet = my_socket.recvfrom(1000)
        print('UDP Packet received.')
    except socket.timeout:
        print('Receive timed out.')
        return False
    return packet
