import multiprocessing
import socket
import soundcard as sc
from notifypy import Notify


def send_notification(text: str):
    notification = Notify()
    notification.title = "小雨妙享-音频串流"
    notification.message = text
    notification.send()


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


def send_data(tcp_socket: socket, data_queue: list, lock: multiprocessing.Lock):
    while True:
        if len(data_queue) > 0:
            lock.acquire()
            data = data_queue.pop(0)
            lock.release()
            data = data.astype("float32")
            if data.any():
                tcp_socket.send(data.tobytes())


def server():
    print(f"Waiting for connection...")
    send_notification("等待连接...")
    tcp_socket = socket.create_server(("0.0.0.0", 39393))
    tcp_socket, client_addr = tcp_socket.accept()
    print("Connected")
    print(f"Client address: {client_addr}")
    send_notification(f"已连接至{client_addr}")
    loopback_device = init_loopback_device()
    data_queue = multiprocessing.Manager().list()
    share_lock = multiprocessing.Manager().Lock()
    multiprocessing.Process(target=get_audio_slice, args=(loopback_device, data_queue, share_lock)).start()
    send_data(tcp_socket, data_queue, share_lock)


if __name__ == '__main__':
    server()
