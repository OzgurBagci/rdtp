from multiprocessing import Process, Queue
from destination import receive_rdtp
import pickle


def wrap_destination(ip_list):
    for _ in range(100):
        packets_queue = Queue(5242880)
        processes = []
        for ip in ip_list:
            my_process = Process(target=receive_rdtp, args=(ip, packets_queue))
            processes.append(my_process)
            my_process.start()

        ordered_packets = []

        cont = True
        none_count = 0
        while cont:
            while not packets_queue.empty():
                packet = pickle.loads(packets_queue.get())

                if packet is None:
                    none_count += 1
                    if none_count == 2:
                        cont = False
                    break

                if packet[3] != b'':
                    ordered_packets.append(packet)

        for proc in processes:
            proc.join()

        sorted(ordered_packets, key=lambda x: x[2][4])
        ordered_packets = list(set(ordered_packets))
        with open(ordered_packets[0][3].decode(), 'wb') as out_file:
            for i in range(1, len(ordered_packets)):
                out_file.write(ordered_packets[i][3].decode('utf-8', 'replace').encode())
