import multiprocessing
import socket
import numpy as np
import soundcard as sc
from notifypy import Notify


def send_notification(text: str):
    notification = Notify()
    notification.title = "小雨妙享-音频串流"
    notification.message = text
    notification.send()


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
                except ValueError:
                    print(f"Invalid shape: {d.shape}")
                    continue
                p.play(d)


def recv_data(tcp_socket: socket, data_queue: list, lock: multiprocessing.Lock):
    while True:
        # 480 * 8 * 2 = 7680 bytes
        try:
            buf = tcp_socket.recv(15360)
            data = np.frombuffer(buf, dtype=np.float32)
            data.resize((960, 2))
        except Exception as e:
            print(f"Failed to receive data: {e}")
            continue
        lock.acquire()
        data_queue.append(data)
        lock.release()


def client(address: str):
    send_notification(f"正在连接至{address}")
    server_addr = (address, 39393)
    tcp_socket = socket.create_connection(server_addr)
    print(f"Connected")
    send_notification(f"已连接至{address}")
    data_queue = multiprocessing.Manager().list()
    share_lock = multiprocessing.Manager().Lock()
    multiprocessing.Process(target=play_data, args=(data_queue, share_lock)).start()
    recv_data(tcp_socket, data_queue, share_lock)


if __name__ == '__main__':
    # client("192.168.39.233")
    client("127.0.0.1")
