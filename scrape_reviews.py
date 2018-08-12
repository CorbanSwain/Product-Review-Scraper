#!python3
# scrape_reviews.py

import amazon_scraper as az
import sephora_advice_search_scraper as sph
from pandas import ExcelWriter
from selenium import webdriver
from utilities import *
import pandas as pd
import datetime
import wordcloud


def reviews2wordcloud(fname, df):
    text = df['review_body']
    text = ' '.join(list(text)).strip()
    if text:
        wc = wordcloud.WordCloud().generate(text)
        im = wc.to_image()
        im.save(fname, 'png')


if __name__ == '__main__':
    in_filename = 'links/amazon_links.txt'
    with open(in_filename) as fle:
        urls = [l.strip() for l in fle.readlines() if len(l.strip()) > 0]

    amazon = 'amazon'
    sephora = 'sephora'
    scraper_types = (amazon, sephora)

    valid_urls = []
    do_make_webdriver = False
    for url in urls:
        typ = parse_url(url)[1].split('.')[1]
        if typ in scraper_types:
            valid_urls.append((url, typ))
            if not do_make_webdriver and typ == sephora:
                do_make_webdriver = True
        else:
            print('%s \n\t is not a valid url for scraping.')

    if valid_urls:
        excel_writer = ExcelWriter('output/misc.xlsx')
        if do_make_webdriver:
            driver = webdriver.Chrome()

        # Main processing loop
        for i, (url, typ) in enumerate(valid_urls):
            print('Scraping with %s scraper from:\n\t%s' % (typ, url))
            sheet_name_fmt = '%d. %%s' % (i + 1)
            if typ == amazon:
                metadata, review_df = az.scrape_reviews(url, excel_writer)
                sheet_name = sheet_name_fmt % metadata['product_name'][:15]
            elif typ == sephora:
                metadata, review_df = sph.scrape_reviews(url,
                                                         driver,
                                                         excel_writer)
                sheet_name = sheet_name_fmt % metadata['search_string'][:15]

            metadata['url'] = url
            metadata['scraper_type'] = typ
            metadata['scrape_date'] = str(datetime.datetime.now())
            metadata['num_reviews'] = len(review_df)
            metadata = [pd.Series(ls) for ls in metadata.items()]
            metadata = pd.DataFrame(metadata)
            metadata.to_excel(excel_writer,
                              sheet_name=sheet_name,
                              index=False, header=False)
            new_start_row = len(metadata) + 3

            wc_filename = 'output/word_clouds/%s_%s.png' % (typ, sheet_name);
            reviews2wordcloud(wc_filename, review_df)

            review_df.to_excel(excel_writer,
                               sheet_name=sheet_name,
                               index=False,
                               startrow=new_start_row)

        excel_writer.save()
        if do_make_webdriver:
            driver.quit()
    else:
        print('No valid urls provided.')



