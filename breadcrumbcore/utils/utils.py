import hashlib
import random
import string


def is_ascii(s):
    return all(ord(c) < 128 for c in s)


def get_hash8(s):
    if not s:
        return int(hashlib.sha1(s).hexdigest(), 16) % (10 ** 8)
    return 0000000


def random_hash8():
    rand_str = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(10))
    return get_hash8(rand_str)


if __name__ == "__main__":
    print random_hash8()
