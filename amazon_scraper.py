#!python3
# amazon_scraper.py

from utilities import *
import re
import datetime as dt
import pandas as pd


def ele2url(ele):
    return create_full_url(ele['href'])


def review_url2format(url):
    return url_change_query(url, pageNumber='{:d}')


def create_full_url(rel_url):
    az_base_url = 'https://www.amazon.com'
    return az_base_url + rel_url


def get_product_info(soup):
    name = soup.find('span', {'id': 'productTitle'}).text.strip()
    vendor = soup.find('a', {'id': 'bylineInfo'}).text.strip()
    description = soup.find('div', {'id': 'productDescription'}).text.strip()
    price = soup.find('span', {'id': 'priceblock_ourprice'}).text.strip()
    price = float(price.strip('$'))
    asin = str(soup.find('b', text=re.compile('ASIN')).next.next)
    return dict(product_name=name,
                product_vendor=vendor,
                product_description=description,
                product_price=price,
                product_asin=asin)


def get_review_structure(soup):
    see_all_ele = soup.find('a',
                            {'data-hook': 'see-all-reviews-link-foot'})
    all_reviews_url = ele2url(see_all_ele)
    all_reviews_soup = get_soup(all_reviews_url)
    next_button_ele = all_reviews_soup.find('li', {'class': 'a-last'}).next
    num_review_pages = int(next_button_ele.previous.previous)
    review_page_url = ele2url(next_button_ele)
    review_page_url_fmt = review_url2format(review_page_url)
    return num_review_pages, review_page_url_fmt


def get_review_boxes(soup):
    review_boxes = soup.find_all('div', {'class': 'a-section review',
                                         'data-hook': 'review'})
    return review_boxes


def rb_get_rating(rb_soup):
    rating_soup = rb_soup.find('i', {'data-hook':
                                     'review-star-rating'})
    if rating_soup is None:
        return None
    rating_str = rating_soup.text.strip()
    review_pattern = re.compile(r'\s*(?P<rating>\d*\.\d*)\s.*')
    m = review_pattern.match(rating_str)
    return float(m.group('rating')) if m else None


def rb_get_title(rb_soup):
    title = rb_soup.find('a', {'data-hook': 'review-title'})
    return title.text.strip() if title else None


def rb_get_date(rb_soup):
    date_soup = rb_soup.find('span', {'data-hook': 'review-date'})
    if date_soup is None:
        return None
    messy_datestr = date_soup.text.strip()
    date_pattern = re.compile(r'(on\s*)?(?P<datestr>.*)')
    datestr = date_pattern.match(messy_datestr).group('datestr')
    date = dt.datetime.strptime(datestr, '%B %d, %Y').date()
    return date.strftime('%m/%d/%Y')


def rb_get_product_style(rb_soup):
    style = rb_soup.find('a', {'data-hook': 'format-strip'})
    return style.text.strip() if style else None


def rb_get_body(rb_soup):
    body_soup = rb_soup.find('span', {'data-hook': 'review-body'})
    return '\n'.join(body_soup.stripped_strings) if body_soup else None


def scrape_reviews(product_url, excel_writer):
    main_soup = get_soup(product_url)
    metadata = get_product_info(main_soup)
    num_review_pages, review_url_fmt = get_review_structure(main_soup)

    df_format = [(rb_get_title, 'review_title', str),
                 (rb_get_date, 'review_date', str),
                 (rb_get_product_style, 'review_product_style', str),
                 (rb_get_rating, 'review_rating', float),
                 (rb_get_body, 'review_body', str)]

    (data_funcs, column_names, types) = zip(*df_format)
    review_data = []
    for i in range(num_review_pages):
        p_idx = i + 1
        print('Scraping Review Page %d of %d ...' % (p_idx, num_review_pages))
        rp_url = review_url_fmt.format(p_idx)
        review_boxes = get_review_boxes(get_soup(rp_url))
        review_data += [[f(rb) for f in data_funcs] for rb in review_boxes]

    review_data = dict([(name, pd.Series(col, dtype=typ))
                        for name, col, typ
                        in zip(column_names, zip(*review_data), types)])
    review_df = pd.DataFrame(review_data)
    print(review_df)
    print('Done.')
    print('Successfully scraped %d reviews.' % len(review_df))
    return metadata, review_df





