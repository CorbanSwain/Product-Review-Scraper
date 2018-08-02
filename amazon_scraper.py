#!python3

from bs4 import BeautifulSoup
import requests
import re
import pprint as pp
import time
import urllib.parse as urlparse


def az_create_full_link(rel_link):
    az_base_link = 'https://www.amazon.com'
    return az_base_link + rel_link


def get_soup(html_text):
    return BeautifulSoup(html_text, 'html.parser')


def get_page_text(link):
    time.sleep(0.25)
    page = requests.get(link)
    return page.text


def process(html_text):
    soup = get_soup(html_text)
    az_see_all_id = 'dp-summary-see-all-reviews'
    see_all_element = soup.find('a', {'data-hook': 'see-all-reviews-link-foot'})
    see_all_link = az_create_full_link(see_all_element['href'])
    see_all_page = get_page_text(see_all_link)
    see_all_soup = get_soup(see_all_page)
    next_button_ele_sib = see_all_soup.find_all('li', {'class': 'a-last'})[0]

    next_button_ele = next_button_ele_sib.next
    max_page_num = next_button_ele.previous.previous
    next_button_link = az_create_full_link(next_button_ele['href'])
    next_button_link_parsed = urlparse.urlparse(next_button_link)
    next_button_link_dict = urlparse.parse_qs(next_button_link_parsed.query)
    next_button_link_dict['pageNumber'] = 4
    new_query = urlparse.urlencode(next_button_link_dict, doseq=True)
    next_button_link_tup = tuple(next_button_link_parsed)
    new_tup = next_button_link_tup[:4] + (new_query,) + next_button_link_tup[5:]
    new_url = urlparse.urlunparse(new_tup)
    pp.pprint(new_url)



if __name__ == '__main__':
    in_filename = 'amazon_links.txt'
    with open(in_filename) as fle:
        links = [l.strip() for l in fle.readlines()]
    # pp.pprint('Links:')
    # pp.pprint(links)
    html_txt = get_page_text(links[0])
    process(html_txt)

