from digest import *
from source import send_rdtp
import time


def wrap_source(filename, hostname):
    for _ in range(100):
        time.sleep(1)
        data = digest(filename, True, 476)
        first_time = time.time()
        send_rdtp(hostname, data)
        second_time = time.time()
        with open('time.txt', 'a') as time_file:
            time_file.write(str(second_time - first_time) + '\n')
