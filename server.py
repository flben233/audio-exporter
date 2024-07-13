import multiprocessing
import socket
import soundcard as sc
import numpy as np


def get_audio_slice(device, data_queue: list, lock: multiprocessing.Lock):
    with device.recorder(samplerate=48000) as d:
        while True:
            audio_slice = d.record(numframes=960)
            lock.acquire()
            data_queue.append(audio_slice)
            lock.release()


def init_loopback_device():
    default_speaker = sc.default_speaker()
    print(f"Default speaker: {default_speaker}")
    mics = sc.all_microphones(include_loopback=True)
    for mic in mics:
        if mic.name == default_speaker.name:
            return mic
    print("Default speaker not found in loopback devices, using default microphone.")
    return sc.default_microphone()


def send_data(udp_socket: socket, data_queue: list, client_addr: tuple, lock: multiprocessing.Lock):
    while True:
        if len(data_queue) > 0:
            lock.acquire()
            data = data_queue.pop(0)
            lock.release()
            data = data.astype("float32")
            if data.any():
                data_chunks = np.split(data, 20)
                for chunk in data_chunks:
                    udp_socket.sendto(chunk.tobytes(), client_addr)
                # udp_socket.sendto(data.tobytes(), client_addr)


def server():
    print(f"Waiting for connection...")
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(("0.0.0.0", 39393))
    data, client_addr = udp_socket.recvfrom(1024)
    while data.decode() != "hello":
        data, client_addr = udp_socket.recvfrom(1024)
    udp_socket.sendto("hello".encode(), client_addr)
    print("Connected")
    print(f"Client address: {client_addr}")
    loopback_device = init_loopback_device()
    data_queue = multiprocessing.Manager().list()
    share_lock = multiprocessing.Manager().Lock()
    multiprocessing.Process(target=get_audio_slice, args=(loopback_device, data_queue, share_lock)).start()
    send_data(udp_socket, data_queue, client_addr, share_lock)


if __name__ == '__main__':
    server()
