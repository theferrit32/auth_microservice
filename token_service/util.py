import base64
import binascii
import hashlib
import math
import logging
import os
import stat
try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote
from token_service import config

try:
    FileNotFoundError
except NameError:
    # FileNotFoundError doesn't exist in py27, but it is really an IOError anyway
    FileNotFoundError = IOError

try:
    basestring
except NameError:
    # basestring doesn't exist in py3
    # (or better yet: str in py27 doesn't include unicode)
    basestring = str


def is_str(s):
    return isinstance(s, basestring)


def logging_sensitive(*args, **kwargs):
    """
    Special debug logging, that might log encrypted/decrypted data.
    Only when debug_sensitive is enabled in token_service.config
    """
    if config.debug_sensitive:
        logging.debug(*args, **kwargs)
    else:
        logging.debug("sensitive false: non-templated message %s", args[0])


def generate_nonce(length):
    '''
    Returns a random hex string with provided length. URL safe.
    String returned contains (1/2 * length) bytes of urandom entropy.
    '''
    nonce = os.urandom(int(math.ceil(length)))

    return binascii.b2a_hex(nonce)[:length].decode('utf-8')


def generate_base64(length):
    '''
    Returns a random base64 string with provided length. Not URL safe.
    String returned contains (3/4 * length) bytes of urandom entropy.

    If the output is used for something that might be passed around in urls,
    send it through sanitize_base64 first.
    '''
    nonce = os.urandom(int(math.ceil(int(float(length)*3/4))))
    return base64.b64encode(nonce).decode('utf-8')


def sanitize_base64(s):
    '''
    Expects a base64 encoded string. Replaces non-url-safe characters
    with other characters. This means the return is not standard base64.

    Intended to be used purely for convenience in random base64 tokens,
    as creates a url-safe version of base64 that is not longer and does not
    decrease entropy.
    '''
    s = s.replace('+', '-')
    s = s.replace('/', '_')
    s = s.replace('=', '~')
    return s


def list_subset(A, B):
    '''
    Takes two iterables, returns True if A is a subset of B.
    '''
    if not A or not B:
        return False
    for a in A:
        if a not in B:
            return False
    return True


def sha256(s):
    if not is_str(s):
        logging.debug("not a string instance: %s", s)
        return None
    hasher = hashlib.sha256()
    hasher.update(s.encode('utf-8'))
    return hasher.hexdigest()


def is_sock(path):
    if not path or not is_str(path):
        return False
    try:
        file_stat = os.stat(path)
    except FileNotFoundError:
        return False

    return stat.S_ISSOCK(file_stat.st_mode)


def build_redirect_url(base_url, token):
    # access_token, uid, user_name=None, first_name=None, last_name=None):
    user = token.user
    url = '{}/?access_token={}'.format(base_url, token.access_token)
    url += '&uid=' + quote(user.sub)
    url += '&user_name=' + quote(user.user_name)
    url += '&name=' + quote(user.name)
    if user.email is not None and len(user.email) > 0:
        url += '&email=' + quote(user.email)

    # body = {
    #        'access_token': token.access_token,
    #        'uid': user.sub,
    #        'user_name': user.user_name,
    #        'name': user.name
    # }
    # body_encoded = base64.b64encode(json.dumps(body))
    # url = '{}/?context={}'.format(base_url, body_encoded)

    return url
