#! /usr/bin/env python3

import re
import urllib.request
import urllib.parse
import sys
import json
import time
import sqlite3


geo_code_url = 'https://maps.googleapis.com/maps/api/geocode/json'


class timeout_crawler():
    def __init__(self, url):
        input_url_pattern = '(?<=//).*'
        self.root = ('http://'
                     + re.search(input_url_pattern, url).group().split('/')[0])
        self.start_url = url
        self.target_checked = set()
        self.target_notchecked = set()
        self.target_url_pattern = '(?<=href\=")/ja/tokyo/venue/[0-9]+'
        self.url_pattern = '(?<=href\=")/ja/tokyo/.*?(?=")'
        self.nontarget_checked = set()
        self.nontarget_notchecked = set()
        self.headers = {'User-Agent': 'NewsCrawler(phigasui.com)'}


    def crawl(self, checked=[]):
        checked = list(map(lambda x: x.replace(self.root, ''), checked))
        self.target_checked.update(checked)
        req = urllib.request.Request(self.start_url, None, self.headers)
        res = urllib.request.urlopen(req)
        html_str = ''.join(res.read().decode('utf-8').split('\n'))
        self.target_notchecked.update(
            re.findall(self.target_url_pattern, html_str))
        self.nontarget_notchecked.update(re.findall(self.url_pattern, html_str))


        while True:
            time.sleep(1)

            self.nontarget_notchecked -= self.target_notchecked
            self.target_notchecked -= self.target_checked
            self.nontarget_notchecked -= self.nontarget_checked

            if len(self.target_notchecked) > 0:
                target_url = self.target_notchecked.pop()
                self.target_checked.add(target_url)

                print(self.root + target_url)
                venue = mesi_news(self.root + target_url)
                venue.extract()
                if venue.limit_geocoding_api:
                    print('apilimit')
                    break

                yield (venue.url, venue.title, venue.ll, venue.img_url)

                self.target_notchecked.update(
                    re.findall(self.target_url_pattern, venue.html_str))
                self.nontarget_notchecked.update(
                    re.findall(self.url_pattern, venue.html_str))

                continue

            elif len(self.nontarget_notchecked) >= 0:
                nontarget_url = self.nontarget_notchecked.pop()
                self.nontarget_checked.add(nontarget_url)
                req = urllib.request.Request(self.root + nontarget_url,
                                             None,
                                             self.headers)
                res = urllib.request.urlopen(req)
                html_str = ''.join(res.read().decode('utf-8').split('\n'))

                print(self.root + nontarget_url)

                self.target_notchecked.update(
                    re.findall(self.target_url_pattern, html_str))
                self.nontarget_notchecked.update(
                    re.findall(self.url_pattern, html_str))

            else:
                print('source empty')
                break


class mesi_news:
    def __init__(self, url):
        input_url_pattern = '(?<=//).*'
        self.url = url
        self.root = ('http://'
                     + re.search(input_url_pattern, url).group().split('/')[0])
        self.headers = {'User-Agent': 'NewsCrawler(phigasui.com)'}
        self.limit_geocoding_api = False
        self.zero_geocoding_api = False
        self.invalid_geocoding_api = False


    def extract(self):
        def get_html():
            req = urllib.request.Request(self.url, None, self.headers)
            res = urllib.request.urlopen(self.url)
            return res.read().decode('utf-8')

        def get_addr():
            pattern_frame = '住所.*?<p>.*?</p>'
            pattern_addr = '(?<=<p>).*[都道府県市区町村].*(?=</p>)'
            addr_frame = re.search(pattern_frame, self.html_str)

            if addr_frame != None:
                addr = re.search(pattern_addr, addr_frame.group())
                if addr != None: return addr.group().strip()
                else: return

            else: return

        def get_ll():
            query = urllib.parse.urlencode({'address': self.addr,
                                            'sensor': False})
            res = urllib.request.urlopen(geo_code_url + '?' + query)
            res_json = json.loads(res.read().decode('utf-8'))
            ll = (res_json['results'][0]['geometry']['location']
                  if res_json['status'] == 'OK'
                  else {'lat': None, 'lng': None})
            if res_json['status'] == 'OVER_QUERY_LIMIT':
                self.limit_geocoding_api = True
            if res_json['status'] == 'ZERO_RESULTS':
                self.zero_geocoding_api = True
            if res_json['status'] == 'INVALID_REQUEST':
                self.invalid_geocoding_api = True

            return ll

        def get_img_url():
            pattern_width = '(?<=width=")[0-9]+(?=")'
            pattern_img_tag = '<img.*?/>'
            pattern_img_url = '(?<=src=").*\.jpe?g'

            img_list = re.findall(pattern_img_tag, self.html_str)
            max_width = max(map(int, re.findall(pattern_width,
                                                "".join(img_list))))

            return [re.search(pattern_img_url, i).group()
                    for i in img_list
                    if i.find('width="{0}"'.format(max_width)) >= 0
                    and re.search(pattern_img_url, i) != None]

        def get_title():
            pattern_title = '(?<=<title>).*?(?=</title>)'
            return re.search(pattern_title,
                             self.html_str).group().split('-')[0].strip()

        self.html_str = ''.join(get_html().split('\n'))
        self.title = get_title()
        self.addr = get_addr()
        self.ll = get_ll() if self.addr != None else {'lat': None, 'lng': None}
        imgs = get_img_url()
        self.img_url = self.root + imgs[0] if len(imgs) !=0 else None


if __name__ == '__main__':
    # test = mesi_news('http://timeout.jp/ja/tokyo/venue/12278')
    # test.extract()
    # print(test.url, test.title, test.addr, test.ll, test.img_url)
    url = sys.argv[1] if len(sys.argv) > 1 else 'http://timeout.jp/ja/tokyo'
    timeout = timeout_crawler(url)
    con = sqlite3.connect('timeout.db')
    cur = con.cursor()
    cur.execute(
        '''
        create table if not exists venues(url, title, lat, lon, img_url)
        '''
    )

    cur.execute(
        '''
        select url from venues
        '''
    )
    checked = list(map(lambda x : x[0], cur.fetchall()))

    for v in timeout.crawl(checked):
        print(v)
        cur.execute(
            '''
            replace into venues values(?, ?, ?, ?, ?)
            ''',
            (v[0], v[1], v[2]['lat'], v[2]['lng'], v[3])
        )
        con.commit()
    cur.close()
