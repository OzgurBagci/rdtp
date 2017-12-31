import time
import subprocess


def calculate():
    for i in range(1000):
        first_time = time.time()
        subprocess.check_call(['./client.o', '10.10.4.2:10.10.2.2', './input.txt'])
        second_time = time.time()
        difference = second_time - first_time
        print(difference)