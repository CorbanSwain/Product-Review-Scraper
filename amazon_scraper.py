#!/usr/bin/python3

from bs4 import BeautifulSoup
import requests
import re
import pprint as pp
import time
import urllib.parse as urlparse
import random
import math
import uuid
import datetime as dt


# General Functions
def random_sleep_time():
    return 0.5 + (math.sin(((random.random() * 2) - 1) * math.pi / 4) / 2)


def get_page_text(url):
    time.sleep(random_sleep_time())
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
        id_tups.append((_uuid, v))
        url_query_dict[k] = _uuid
    new_query_str = urlparse.urlencode(url_query_dict, doseq=True)
    new_url = urlparse.urlunparse(tup_sub(parsed_url, 4, new_query_str))
    for _uuid, v in id_tups:
        new_url = new_url.replace(_uuid, v)
    return new_url


# Amazon Specific Functions
def az_ele2url(ele):
    return az_create_full_url(ele['href'])


def az_review_url2format(url):
    return url_change_query(url, pageNumber='{:d}')


def az_create_full_url(rel_url):
    az_base_url = 'https://www.amazon.com'
    return az_base_url + rel_url


def az_get_product_info(soup):
    name = soup.find('span', {'id': 'productTitle'}).text.strip()
    vendor = soup.find('a', {'id': 'bylineInfo'}).text.strip()
    description = soup.find('div', {'id': 'productDescription'}).text.strip()
    price = soup.find('span', {'id': 'priceblock_ourprice'}).text.strip()
    price = float(price.strip('$'))
    asin = str(soup.find('b', text=re.compile('ASIN')).next.next)
    return dict(name=name, vendor=vendor, description=description, price=price,
                asin=asin)


def az_get_review_structure(soup):
    see_all_ele = soup.find('a',
                            {'data-hook': 'see-all-reviews-link-foot'})
    all_reviews_url = az_ele2url(see_all_ele)
    all_reviews_soup = get_soup(all_reviews_url)
    next_button_ele = all_reviews_soup.find('li', {'class': 'a-last'}).next
    num_review_pages = int(next_button_ele.previous.previous)
    review_page_url = az_ele2url(next_button_ele)
    review_page_url_fmt = az_review_url2format(review_page_url)
    return num_review_pages, review_page_url_fmt


def az_get_reviews(soup):
    review_boxes = soup.find_all('div', {'class': 'a-section review',
                                         'data-hook': 'review'})
    return [azrb_get_review_data(rb_soup) for rb_soup in review_boxes]


def azrb_get_review_data(rb_soup):
    return [azrb_get_title(rb_soup),
            azrb_get_date(rb_soup),
            azrb_get_product_style(rb_soup),
            azrb_get_rating(rb_soup),
            azrb_get_body(rb_soup)]


def azrb_get_rating(rb_soup):
    rating_soup = rb_soup.find('i', {'data-hook':
                                    'review-star-rating'})
    if rating_soup is None:
        return None

    rating_str = rating_soup.text.strip()
    review_pattern = re.compile(r'\s*(?P<rating>\d*\.\d*)\s.*')
    m = review_pattern.match(rating_str)
    return float(m.group('rating')) if m else None


def azrb_get_title(rb_soup):
    title = rb_soup.find('a', {'data-hook': 'review-title'})
    return title.text.strip() if title else None


def azrb_get_date(rb_soup):
    date_soup = rb_soup.find('span', {'data-hook': 'review-date'})

    if date_soup is None:
        return None

    messy_datestr = date_soup.text.strip()
    date_pattern = re.compile(r'(on\s*)?(?P<datestr>.*)')
    datestr = date_pattern.match(messy_datestr).group('datestr')
    date = dt.datetime.strptime(datestr, '%B %d, %Y').date()
    return date.strftime('%m/%d/%Y')


def azrb_get_product_style(rb_soup):
    style = rb_soup.find('a', {'data-hook': 'format-strip'})
    return style.text.strip() if style else None


def azrb_get_body(rb_soup):
    body_soup = rb_soup.find('span', {'data-hook': 'review-body'})
    return '\n'.join(body_soup.stripped_strings) if body_soup else None


def az_scrape_reviews(product_url):
    main_soup = get_soup(product_url)
    product_dict = az_get_product_info(main_soup)
    product_dict['url'] = product_url
    num_review_pages, review_url_fmt = az_get_review_structure(main_soup)
    reviews = []
    for i in range(num_review_pages):
        pp.pprint('Scraping Review Page %d of %d ...'
                  % (i + 1, num_review_pages))
        rp_url = review_url_fmt.format(i + 1)
        reviews += az_get_reviews(get_soup(rp_url))
    pp.pprint('Done.')
    pp.pprint(len(reviews))



def process(html_text):
    '''deprecated

    '''
    soup = get_soup(html_text)

    see_all_page = get_page_text(see_all_url)
    see_all_soup = get_soup(see_all_page)
    next_button_ele_sib = see_all_soup.find_all('li', {'class': 'a-last'})[0]

    next_button_ele = next_button_ele_sib.next
    max_page_num = int(next_button_ele.previous.previous)
    pp.pprint(max_page_num)
    next_button_url = az_create_full_url(next_button_ele['href'])
    next_button_url_parsed = urlparse.urlparse(next_button_url)
    next_button_url_dict = urlparse.parse_qs(next_button_url_parsed.query)
    next_button_url_dict['pageNumber'] = 4
    new_query = urlparse.urlencode(next_button_url_dict, doseq=True)
    next_button_url_tup = tuple(next_button_url_parsed)
    new_tup = next_button_url_tup[:4] + (new_query,) + next_button_url_tup[5:]
    new_url = urlparse.urlunparse(new_tup)
    pp.pprint(new_url)


if __name__ == '__main__':
    in_filename = 'amazon_links.txt'
    with open(in_filename) as fle:
        urls = [l.strip() for l in fle.readlines()]
    for url in urls:
        az_scrape_reviews(url)
