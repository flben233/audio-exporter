import argparse
import multiprocessing

from server import server
from client import client

if __name__ == '__main__':
    multiprocessing.freeze_support()
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", type=str, default="127.0.0.1")
    parser.add_argument("--mode", type=str, default="server")
    args = parser.parse_args()
    if args.mode == "server":
        server()
    elif args.mode == "client":
        client(args.address)
    else:
        print("Invalid mode")
