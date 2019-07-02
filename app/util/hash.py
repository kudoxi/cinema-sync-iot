import hmac
from hashlib import sha1, md5


def hmac_sha1(message, secret):
    hashed = hmac.new(secret.encode('utf8'), message.encode('utf8'), sha1)
    return hashed.hexdigest().upper()


def hash_md5(message):
    m = md5()
    m.update(message)
    return m.hexdigest()


def hash_file_md5(file, return_type='hex'):
    m = md5()
    with open(file, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            m.update(chunk)
    if return_type == 'bytes':
        return m.digest()
    return m.hexdigest()


def hash_bytes_md5(bytes):
    m = md5()
    m.update(bytes)
    return m.digest()
