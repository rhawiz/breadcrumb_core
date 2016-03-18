import hashlib


def is_ascii(s):
    return all(ord(c) < 128 for c in s)

def get_hash(s):
    s=str(s)
    return int(hashlib.sha1(s).hexdigest(), 16) % (10 ** 8)
