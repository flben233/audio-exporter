import multiprocessing
import socket
from time import sleep
import numpy as np
import soundcard as sc


def play_data(data_queue: list, lock: multiprocessing.Lock):
    play_device = sc.default_speaker()
    print(f"Default speaker: {play_device}")
    with play_device.player(samplerate=48000) as p:
        while True:
            if len(data_queue) > 0:
                lock.acquire()
                # d = np.frombuffer(data_queue.pop(0), dtype=np.float32)
                d = data_queue.pop(0)
                lock.release()
                try:
                    # d.resize((480, 2))
                    pass
                except ValueError as e:
                    print(f"Invalid shape: {d.shape}")
                    continue
                p.play(d)


def recv_data(udp_socket: socket, addr: str, data_queue: list, lock: multiprocessing.Lock):
    while True:
        # 480 * 8 * 2 = 7680 bytes
        try:
            # data, addr2 = udp_socket.recvfrom(768)
            data = None
            for i in range(20):
                data2, addr2 = udp_socket.recvfrom(384)
                if data is None:
                    data = np.frombuffer(data2, dtype=np.float32)
                    data.resize((48, 2))
                else:
                    d1 = np.frombuffer(data2, dtype=np.float32)
                    d1.resize((48, 2))
                    data = np.concatenate((data, d1))
        except socket.timeout:
            continue
        except Exception as e:
            print(f"Failed to receive data: {e}")
            continue
        if addr2 == addr:
            lock.acquire()
            data_queue.append(data)
            lock.release()


def client(address: str):
    server_addr = (address, 39393)
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.settimeout(3)
    data, addr = None, None
    for i in range(5):
        try:
            udp_socket.sendto("hello".encode(), server_addr)
            data, addr = udp_socket.recvfrom(1024)
            break
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            sleep(i + 1)
            if i == 4:
                print(f"Failed to connect to server: {e}")
                return
    while data.decode() != "hello":
        data, addr = udp_socket.recvfrom(1024)
    print(f"Connected")
    data_queue = multiprocessing.Manager().list()
    share_lock = multiprocessing.Manager().Lock()
    multiprocessing.Process(target=play_data, args=(data_queue, share_lock)).start()
    recv_data(udp_socket, addr, data_queue, share_lock)


if __name__ == '__main__':
    # client("192.168.39.233")
    client("127.0.0.1")
