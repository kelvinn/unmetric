#!/usr/bin/python
import timeit
import httplib
import gc
from urllib2 import  Request, urlopen, URLError
import sys
from random import randrange
from time import sleep, time

probe_loc = 'us'

def check_url(url):
    try:
        start = time()
        response = urlopen(url)
        conn = httplib.HTTPConnection("www.google.com")

        ttlb = int((time() - start) * 10000)
        #len(response.read())
    except URLError, e:
        if hasattr(e, 'reason'):
            ttlb = 0
        elif hasattr(e, 'code'):
            #e.code
            ttlb = 0
    callback_url = 'http://unmetric.appspot.com/api/websites/return/?website=%s&probe_loc=%s&ttlb=%s' % (url, probe_loc, ttlb)
    #callback_url = 'http://localhost:8080/api/websites/return/?website=%s&probe_loc=%s&ttlb=%s' % (url, probe_loc, ttlb)
    try:
        print callback_url
        cb_response = urlopen(callback_url)
    except:
        pass


if __name__ == "__main__":
    while True:

        try:
            website_list = urlopen('http://unmetric.appspot.com/api/websites/read/?probe_loc=%s' % probe_loc).read()
            #website_list = urlopen('http://localhost:8080/api/websites/read/?probe_loc=%s' % probe_loc).read()
            for url in website_list.split(" "):
                check_url(url) # eventually send this to Queue  
        except:
            pass
        sleep(randrange(10,20))

