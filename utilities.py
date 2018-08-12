#!python3
# utilities.py

from bs4 import BeautifulSoup
import requests
import pprint as pp
import time
import urllib.parse as urlparse
import random
import math
import uuid
import selenium


def try_click_element(ele):
    random_sleep()
    try:
        ele.click()
        return True
    except selenium.common.exceptions.ElementNotVisibleException:
        return False



def random_sleep_time():
    f = 0.2
    return f + (math.sin(((random.random() * 2) - 1) * math.pi / 2) * f)


def random_sleep():
    time.sleep(random_sleep_time())


def get_page_text(url):
    random_sleep()
    headers = {'User-Agent':
               'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) '
               'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 '
               'Safari/537.36'}
    page = requests.get(url, headers=headers)
    return page.text


def get_soup(url):
    html_text = get_page_text(url)
    return BeautifulSoup(html_text, 'html.parser')


def tup_sub(tup, i, v):
    return tup[:i] + (v,) + tup[(i + 1):]


def url_change_query(url, **kwargs):
    parsed_url = urlparse.urlparse(url)
    url_query_dict = urlparse.parse_qs(parsed_url.query)
    id_tups = []
    for k, v in kwargs.items():
        _uuid = uuid.uuid4().hex
        id_tups.append((_uuid, str(v)))
        url_query_dict[k] = _uuid
    new_query_str = urlparse.urlencode(url_query_dict, doseq=True)
    new_url = urlparse.urlunparse(tup_sub(parsed_url, 4, new_query_str))
    for _uuid, v in id_tups:
        new_url = new_url.replace(_uuid, v)
    return new_url


def url_get_query(url, query_key):
    parsed_url = urlparse.urlparse(url)
    url_query_dict = urlparse.parse_qs(parsed_url.query)
    result = url_query_dict.get(query_key, None)
    return result[0] if len(result) is 1 else result


def parse_url(url):
    return urlparse.urlparse(url)
