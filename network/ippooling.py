import socket
import random
import struct
from time import sleep

real_create_conn = socket.create_connection


def generate_random_ip():
    return socket.inet_ntoa(struct.pack('>I', random.randint(1, 0xffffffff)))

true_socket = socket.socket
def bound_socket(*a, **k):
    sock = true_socket(*a, **k)
    sock.bind((generate_random_ip(), 0))
    return sock
socket.socket = bound_socket
