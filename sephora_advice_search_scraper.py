#!python3
# sephora_advice_search_scraper.py

from utilities import *
import re
import pandas as pd


def get_review_boxes(soup):
    review_boxes = soup.find_all('div', {'ng-repeat': 'advice in reviews'})
    return review_boxes


def rb_get_rating(rb_soup):
    tags = {'class': 'u-mr2 StarRating u-relative u-oh'}
    rating_soup = rb_soup.find('div', tags)
    return int(rating_soup['seph-stars']) if rating_soup else None


def rb_get_name_brand(rb_soup):
    tags = {'class': re.compile(r'SkuItem-nameBrand')}
    brand_soup = rb_soup.find('div', tags)
    return brand_soup.text.strip() if brand_soup else None


def rb_get_name_display(rb_soup):
    tags = {'class': re.compile(r'SkuItem-nameDisplay')}
    name_soup = rb_soup.find('div', tags)
    return name_soup.text.strip() if name_soup else None


def rb_get_product(rb_soup):
    name_brand = rb_get_name_brand(rb_soup)
    name_display = rb_get_name_display(rb_soup)
    if name_brand or name_display:
        name_brand = name_brand if name_brand else ''
        name_display = name_display if name_display else ''
        return ' - '.join([name_brand, name_display])
    else:
        return None


def rb_get_price(rb_soup):
    tags = {'ng-class': re.compile('product_sale_price')}
    product_price_soup = rb_soup.find('span', tags)
    if not product_price_soup:
        return None
    pattern = re.compile(r'\$(?P<price>\d*\.?\d*)')
    m = pattern.match(product_price_soup.text.strip())
    if not m:
        return None
    return float(m.group('price'))


def rb_get_title_date_body(rb_soup):
    # FIXME - this doesn't work for reviews without a title.
    tags = {'class': 'u-linkComplexTarget u-fwb ng-binding'}
    title_soup = rb_soup.find('span', tags)
    if not title_soup:
        return None, None, None
    title = title_soup.text.strip()

    datestr_messy = str(title_soup.next.next).strip()
    pattern = re.compile(r'.*(?P<date>\d{2}\.\d{2}\.\d{4}).*')
    m = pattern.match(datestr_messy)
    if not m:
        datestr = None
    else:
        datestr = m.group('date').replace('.', '/')

    body = str(title_soup.next.next.next).strip()
    return [title, datestr, body]


def close_signup_popup(driver):
    result = driver.find_elements_by_class_name('Modal-close')
    if result:
        close_button = result[0]
        try_click_element(close_button)


def open_all_reviews(driver):
    def get_view_more():
        return driver.find_elements_by_xpath(
            "//*[contains(text(), 'View more reviews')]")
    result = get_view_more()
    did_click = True
    while result and did_click:
        did_click = try_click_element(result[0])
        result = get_view_more()


def get_full_soup(url, driver):
    url = url_change_query(url, review_limit=5000)
    random_sleep()
    driver.get(url)
    close_signup_popup(driver)
    random_sleep()
    open_all_reviews(driver)
    return BeautifulSoup(driver.page_source, 'html.parser')


def scrape_reviews(product_url, driver, excel_writer):
    metadata = {'search_string': url_get_query(product_url, 'keyword')}

    main_soup = get_full_soup(product_url, driver)
    review_boxes = get_review_boxes(main_soup)

    df_format = [
        (lambda s: [rb_get_product(s), ], ['product_name', ], [str, ]),
        (lambda s: [rb_get_price(s), ], ['price', ], [float, ]),
        (lambda s: [rb_get_rating(s), ], ['rating', ], [int, ]),
        (rb_get_title_date_body,
         ['review_title', 'review_date', 'review_body'],
         [str, str, str])
    ]
    (data_funcs, column_names, types) = zip(*df_format)
    (column_names, types) = (sum(ls, []) for ls in (column_names, types))

    review_data = [sum([f(rb) for f in data_funcs], []) for rb in review_boxes]
    review_data = dict([(name, pd.Series(col, dtype=typ))
                        for name, col, typ
                        in zip(column_names, zip(*review_data), types)])
    review_df = pd.DataFrame(review_data)
    print(review_df)
    print('Successfully scraped %d reviews.' % len(review_df))
    return metadata, review_df

