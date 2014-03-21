#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" hatepos.py

from https://gist.github.com/ottatiyarou/6448440


"""

import base64
import codecs
import datetime
import hashlib
import json
import os
import random
import sys
import time


__dirname__ = os.path.dirname(os.path.abspath(__file__))

# add ./lib directory to loadpath
sys.path.append(__dirname__ + "/lib")

import requests

config = {
    "domain": None,
    "user": None,
    "api_key": None
}

atompub_template = """<?xml version="1.0" encoding="utf-8"?>
<entry xmlns="http://www.w3.org/2005/Atom"
       xmlns:app="http://www.w3.org/2007/app">
  <title>{title}</title>
  <author><name>{name}</name></author>
  <content type="text/plain">{content}</content>
  <updated></updated>
  <app:control>
    <app:draft>{draft}</app:draft>
  </app:control>
</entry>
"""

def get_stdin():
    try:
        input = raw_input
    except NameError:
        pass
    return input()

def load_config():
    global __dirname__
    global config

    fp = open(__dirname__ + "/config.json")
    config.update(json.load(fp))
    fp.close()

def load_postfile(textfile):
    fp = open(textfile)

    # determine title
    title = None
    for line in fp:
        buf = line.rstrip("\r\n")
        # skip blank line
        if buf != "":
            title = buf
            break

    # read body
    body = None

    arr = []
    for line in fp:
        buf = line.rstrip("\r\n")
        arr.append(buf)
 
    # skip blank line at head
    while len(arr) > 0 and arr[0] == "":
        arr.pop(0)

    body = "\n".join(arr)

    fp.close()

    return title, body

def create_wsse(username, password):
    """X-WSSEヘッダの内容を作成
 
    ユーザネームとAPIキーからWSSE認証用文字列を作成し、返します。
    
    Args:
        @username: はてなID
        @password: はてなブログで配布されるAPIキー
    Returns:
        WSSE認証用文字列
    """
    
    # セキュリティトークン
    nonce = hashlib.sha1(str(time.time()) + str(random.random())).digest() 
    # Nonceの作成時刻
    created = datetime.datetime.now().isoformat() + "Z"
    # PasswordDigest
    digest = base64.b64encode(hashlib.sha1(nonce+created+password).digest()) 
    # WSSE認証用文字列として整形して返す
    return 'UsernameToken Username="{0}", PasswordDigest="{1}", Nonce="{2}", Created="{3}"'.format(username, digest, base64.b64encode(nonce), created)

def post(title, body):
    global config
    user = str(config["user"])
    api_key = str(config["api_key"])
    domain = str(config["domain"])

    entry = atompub_template.format(
        title = title,
        name = user,
        content = body,
        draft = "no"
    )

    # atompub url
    url = "http://blog.hatena.ne.jp/{0}/{1}/atom/entry".format(user, domain)
    # WSSE認証用文字列
    wsse = create_wsse(user, api_key)
    # post
    r = requests.post(url, data=entry, headers={'X-WSSE': wsse})

    if r.status_code == 201:
        print u"succeeded." # 成功メッセージ
    else:
        print u"failed." # 失敗メッセージ

def main():
    if len(sys.argv) != 2:
        print("usage: %s <textfile to post>" % __file__)
        sys.exit(1)

    load_config()

    title, body = load_postfile(sys.argv[1])
    post(title, body)

if __name__ == "__main__":
    main()
