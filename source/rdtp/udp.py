import socket


def get_socket():
    """Gives the UDP socket for use. We don't create the socket in 'send_udp' because if we do that, every time we
    send a package we need to create a socket."""
    try:
        return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except socket.error:
        raise Exception('Cannot create UDP Socket for sending the data. Please ensure that you are root and try again.')


def send_udp(my_socket, d_ip, d_port, data):
    """Sends the UDP Package. Takes the socket as first argument. Second argument is Destination IP and the third is
    Destination Port. Lastly, Raw Data is the final argument."""
    try:
        my_socket.sendto(data, (d_ip, d_port))
    except socket.error:
        raise Exception('Cannot send UDP Packet for sending the data. Please ensure that you are root and try again.')
