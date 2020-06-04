import requests
from main.utils.agentUtil import *
import random
from main.apis.amazon.cleaner import *
from main.db.db import *
from func_timeout import func_timeout,exceptions
import traceback
import json
import socket
import time
import http.cookiejar, urllib.request
from main.apis.amazon.data import *
from main.utils.decorators import *
from furl import furl

requests.packages.urllib3.disable_warnings()

class AmazonCrawler:
    def __init__(self):
        self.dataCleaner = AmazonCleaner()
        self.redisClient = RedisClient(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=REDIS_PO)
        self.request_time_out = 60
        self.session = None


    def request(self, taskDetail):
        """
        对任务进行详细分发
        :param taskDetail:
        :return:
        """
        task_type = taskDetail['type']
        if task_type == 'amazonKeyword':
            return self.getGoodsByKeyword(self.getParam(taskDetail, 'keyword', ''),
                                          self.getParam(taskDetail, 'page', 1),
                                          self.getParam(taskDetail, 'sort', 'featured_rank'),
                                          self.getParam(taskDetail, 'countryCode', 'CN'),
                                          self.getParam(taskDetail, 'zipCode', ''),
                                          self.getParam(taskDetail, 'language', 'zh_CN'))
        elif task_type == 'amazonDetail':
            return self.getGoodsDetail(self.getParam(taskDetail, 'url', ''),
                                       self.getParam(taskDetail, 'countryCode', 'CN'),
                                       self.getParam(taskDetail, 'zipCode', ''),
                                       self.getParam(taskDetail, 'language', 'zh_CN'),
                                       self.getParam(taskDetail, 'isproxy', ''),)

        elif task_type == 'amazonComments':
            return self.getGoodsComments2(self.getParam(taskDetail, 'itemId', ''),
                                         self.getParam(taskDetail, 'page', 1),
                                         self.getParam(taskDetail, 'sort', 'recent'),
                                         self.getParam(taskDetail, 'reviewerType', 'all_reviews'),
                                         self.getParam(taskDetail, 'filterByStar', 'all_stars'),
                                         self.getParam(taskDetail, 'formatType', 'all_formats'),
                                         self.getParam(taskDetail, 'mediaType', 'all_contents'),
                                         self.getParam(taskDetail, 'language', 'zh_CN'))

    @retry_by_msg(retry_time=5)
    def getGoodsByKeyword(self, keyword, page, sort, country_code, zip_code, language):
        '''
        搜索商品 (requests)
        :param keyword: 关键词
        :param page: 页码
        :param sort: 排序
        :return:
        '''
        res = {}
        keyword = self.cleanArgs(keyword, 'keyword')
        page = self.cleanArgs(page, 'page')
        sort = self.cleanArgs(sort, 'sort')
        country_code = self.cleanArgs(country_code, 'country_code')
        language = self.cleanArgs(language, 'language')

        # url = 'https://www.amazon.com/s?k={keyword}&s={sort}&page={page}&language={language}&qid={qid}'.format(keyword=keyword, sort=sort, page=page,language=language,qid=int(time.time()))
        url = 'https://www.amazon.com/s/ref=nb_sb_noss_1?url=search-alias%3Daps&field-keywords={keyword}&page={page}&s={sort}&language={language}'.format(keyword=keyword, page=page, sort=sort,language=language)
        # url = 'https://www.amazon.com/s?k={keyword}&s={sort}&page={page}&language=zh_CN&qid={qid}&ref=sr_pg_{page}'.format(keyword=keyword, sort=sort, page=page,language=language,qid=int(time.time()))
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9',
            'referer':'https://www.amazon.com/ref=nav_logo',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'
        }

        try:
            self.session = self.get_session() if self.session is None else self.session
            if country_code != 'CN':
                self.session = self.get_country_session(self.session, country_code)
            elif zip_code != '':
                self.session = self.get_zipcode_session(self.session, zip_code)

            result = func_timeout(self.request_time_out, lambda:self.session.get(url, headers=headers))
            html_doc = result.text
            res = self.check_is_limited(html_doc)
            if res is not None:
                self.session = None
                return res

            result = self.dataCleaner.goodsList(html_doc)
            return result

        except exceptions.FunctionTimedOut:
            res['code'] = 401
            res['msg'] = "请求超时"
            return res

        except:
            res['code'] = 401
            res['msg'] = "请求出错"
            # res['msg'] = str(traceback.format_exc())
            return res



    def getGoodsByKeyword2(self, keyword, page, sort, country_code, zip_code, language):
        '''
        搜索商品 (urllib)
        :param keyword: 关键词
        :param page: 页码
        :param sort: 排序
        :return:
        '''
        res = {}
        keyword = self.cleanArgs(keyword, 'keyword')
        page = self.cleanArgs(page, 'page')
        sort = self.cleanArgs(sort, 'sort')
        country_code = self.cleanArgs(country_code, 'country_code')
        language = self.cleanArgs(language, 'language')

        # url = 'https://www.amazon.com/s?k={keyword}&s={sort}&page={page}&language={language}&qid={qid}&ref=sr_pg_{page}'.format(
        #     keyword=keyword, sort=sort, page=page, language=language, qid=int(time.time()))

        url = 'https://www.amazon.com/s'
        data = 'k={keyword}&s={sort}&page={page}&language={language}&qid={qid}&ref=sr_pg_{page}'.format(
            keyword=keyword, sort=sort, page=page, language=language, qid=int(time.time()))
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,und;q=0.7',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36',
            'Host': 'www.amazon.com',
        }

        try:
            cookie = http.cookiejar.CookieJar()
            if country_code != 'CN':
                cookie = self.get_country_cookie(cookie, country_code)
            elif zip_code != '':
                cookie = self.get_zipcode_cookie(cookie, zip_code)

            request = urllib.request.Request(url, headers=headers, data=bytes(data, encoding='utf8'), method='GET')
            handler = urllib.request.HTTPCookieProcessor(cookie)
            opener = urllib.request.build_opener(handler)
            response = opener.open(request)
            html_doc = response.read().decode()

            result = self.dataCleaner.goodsList(html_doc)
            return result

        except exceptions.FunctionTimedOut:
            res['code'] = 401
            res['msg'] = "请求超时"
            return res

        except:
            res['code'] = 401
            res['msg'] = "请求出错"
            return res


    def getProxy(self):
        url = 'http://ip.8sec.cn/getip?channel=vivo'
        result = requests.get(url)
        result = json.loads(result.text)
        ip = result['msg'][0]
        proxies = {
            'http': 'http://' + ip['ip'] + ':' + str(ip['port']),
            'https': 'https://' + ip['ip'] + ':' + str(ip['port']),
        }
        print(proxies)
        return proxies

    def getGoodsDetail(self, url, country_code, zip_code, language, isproxy):
        '''
        获取商品详情 (requests)
        :param itemId: 商品ID
        :return:
        '''
        res = {}
        country_code = self.cleanArgs(country_code, 'country_code')
        language = self.cleanArgs(language, 'language')

        f = furl(url)
        f.args['language'] = language
        url = f.url

        headers = {
            'authority': 'www.amazon.com',
            'method': 'GET',
            'path': '/Carhartt-K87-Workwear-T-Shirt-Regular/dp/B000G73P3G',
            'scheme': 'https',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,und;q=0.7',
            'cache-control':'max-age=0',
            'upgrade-insecure-requests':'1',
            'cookies':'',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36',
            'Host':'www.amazon.com',
            'Connection': 'keep-alive'
        }
        try:
            session = requests.session()
            if country_code != 'CN':
                session = self.get_country_session(session, country_code)
            elif zip_code != '':
                session = self.get_zipcode_session(session, zip_code)
            if isproxy:
                proxy = self.getProxy()
                result = func_timeout(self.request_time_out, lambda: session.get(url=url, headers=headers, proxies=proxy, verify=False))
            else:
                result = func_timeout(self.request_time_out, lambda:session.get(url=url, headers=headers, verify=False))
            html_doc = result.text
            itemId = self.get_item_id_from_detail_url(url)
            result = self.dataCleaner.goodsDetail(html_doc, itemId)
            return result

        except:
            print(traceback.format_exc())
            res['code'] = 401
            res['msg'] = "请求出错"
            return res

    def getGoodsDetail2(self, url, country_code, zip_code, language):
        '''
        获取商品详情 (urllib)
        :param itemId: 商品ID
        :return:
        '''
        res = {}
        country_code = self.cleanArgs(country_code, 'country_code')
        language = self.cleanArgs(language, 'language')

        if 'http' not in url:
            url = 'https://www.amazon.com/dp/{itemId}?language={language}'.format(itemId=url, language=language)
        else:
            url = url + '&language={language}'.format(language=language)

        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,und;q=0.7',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36',
            'Host':'www.amazon.com',
        }
        try:
            cookie = http.cookiejar.CookieJar()
            if country_code != 'CN':
                cookie = self.get_country_cookie(cookie, country_code)
            elif zip_code != '':
                cookie = self.get_zipcode_cookie(cookie, zip_code)

            request = urllib.request.Request(url, headers=headers)
            handler = urllib.request.HTTPCookieProcessor(cookie)
            opener = urllib.request.build_opener(handler)
            response = func_timeout(self.request_time_out, lambda:opener.open(request))

            html_doc = response.read().decode()
            itemId = self.get_item_id_from_detail_url(url)
            result = self.dataCleaner.goodsDetail(html_doc, itemId)
            return result

        except exceptions.FunctionTimedOut:
            res['code'] = 401
            res['msg'] = "请求超时"
            return res

        except:
            res['code'] = 401
            res['msg'] = "请求出错"
            return res

    def getGoodsComments(self, itemId, page, sort, reviewerType, filterByStar, formatType, mediaType, language):
        '''
        商品评论 (requests)
        :param itemId:商品Id
        :param page: 页码
        :param sort: 排序
        :param language: 语言
        :return:
        '''
        res = {}
        page = self.cleanArgs(page, 'page')
        sort = self.cleanArgs(sort, 'comment_sort')
        reviewerType = self.cleanArgs(reviewerType, 'reviewerType')
        filterByStar = self.cleanArgs(filterByStar, 'filterByStar')
        formatType = self.cleanArgs(formatType, 'formatType')
        mediaType = self.cleanArgs(mediaType, 'mediaType')
        language = self.cleanArgs(language, 'language')

        url = 'https://www.amazon.com/product-reviews/{itemId}?sortBy={sortBy}&reviewerType={reviewerType}&filterByStar={filterByStar}&formatType={formatType}&mediaType={mediaType}&pageNumber={pageNumber}&language={language}'.format(itemId=itemId, sortBy=sort, pageNumber=page, reviewerType=reviewerType, filterByStar=filterByStar, formatType=formatType, mediaType=mediaType, language=language)
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'accept-language': 'zh-CN,zh;q=0.9',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'
        }
        try:
            self.session = self.get_session() if self.session is None else self.session
            result = func_timeout(self.request_time_out, lambda:self.session.get(url, headers=headers, verify=False))
            html_doc = result.text
            result = self.dataCleaner.goodsComments(html_doc)
            return result
        except:
            res['code'] = 401
            res['msg'] = "请求出错"
            # res['msg'] = str(traceback.format_exc())
            return res

    def getGoodsComments2(self, itemId, page, sort, reviewerType, filterByStar, formatType, mediaType, language):
        '''
        商品评论 (urllib)
        :param itemId:商品Id
        :param page: 页码
        :param sort: 排序
        :param language: 语言
        :return:
        '''
        res = {}
        page = self.cleanArgs(page, 'page')
        sort = self.cleanArgs(sort, 'comment_sort')
        reviewerType = self.cleanArgs(reviewerType, 'reviewerType')
        filterByStar = self.cleanArgs(filterByStar, 'filterByStar')
        formatType = self.cleanArgs(formatType, 'formatType')
        mediaType = self.cleanArgs(mediaType, 'mediaType')
        language = self.cleanArgs(language, 'language')

        url = 'https://www.amazon.com/product-reviews/{itemId}?sortBy={sortBy}&reviewerType={reviewerType}&filterByStar={filterByStar}&formatType={formatType}&mediaType={mediaType}&pageNumber={pageNumber}&language={language}'.format(itemId=itemId, sortBy=sort, pageNumber=page, reviewerType=reviewerType, filterByStar=filterByStar, formatType=formatType, mediaType=mediaType, language=language)
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'accept-language': 'zh-CN,zh;q=0.9',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'
        }
        try:
            request = urllib.request.Request(url, headers=headers)
            # response = urllib.request.urlopen(request, timeout=self.request_time_out)
            response = func_timeout(self.request_time_out, lambda: urllib.request.urlopen(request))
            html_doc = response.read().decode()
            result = self.dataCleaner.goodsComments(html_doc)
            return result

        except exceptions.FunctionTimedOut:
            res['code'] = 401
            res['msg'] = "请求超时"
            return res

        except:
            res['code'] = 401
            res['msg'] = "请求出错"
            return res

    def getParam(self, taskDetail, param, default=None):
        """
        获取参数
        :param taskDetail:
        :param param:
        :return:
        """
        if param in taskDetail:
            return taskDetail[param]
        else:
            return default

    def cleanArgs(self, data, type):
        '''
        参数清洗 格式化为最终请求携带的参数
        :param data: 参数数据
        :param type: 参数类型
        :return:
        '''
        result = None
        if type == 'keyword':
            result = re.sub(' +', ' ', data.strip()).replace(' ', '+')

        elif type == 'page':
            if not data:
                result = 1
            else:
                try:
                    result = int(data)
                except:
                    result = 1

        elif type == 'sort':
            default_sort = 'featured_rank'
            if not data or data not in ['featured_rank', 'price-asc-rank', 'price-desc-rank', 'review-rank',
                                        'date-desc-rank']:
                result = default_sort
            else:
                result = data

        elif type == 'country_code':
            default_code = 'CN'
            if not data or data not in COUNTRY_CODE_DICT.keys():
                result = default_code
            else:
                result = data

        elif type == 'language':
            default_lang = 'zh_CN'
            data = data.strip()
            if not data or data not in COUNTRY_LANG_DICT.keys():
                result = default_lang
            else:
                result = data

        elif type == 'comment_sort':
            default_sort = 'recent'
            if not data or data not in ['recent', 'helpful']:
                result = default_sort
            else:
                result = data

        elif type == 'reviewerType':
            default = 'all_reviews'
            if not data or data not in REVIEWER_TYPE.keys():
                result = default
            else:
                result = data

        elif type == 'filterByStar':
            default = 'all_stars'
            if not data or data not in FILTER_BY_STAR.keys():
                result = default
            else:
                result = data

        elif type == 'formatType':
            default = 'all_formats'
            if not data or data not in FORMAT_TYPE.keys():
                result = default
            else:
                result = data

        elif type == 'mediaType':
            default = 'all_contents'
            if not data or data not in MEDIA_TYPE.keys():
                result = default
            else:
                result = data

        return result

    def get_country_session(self, session, country_code):
        url = 'https://www.amazon.com/gp/delivery/ajax/address-change.html'
        post_data = f'locationType=COUNTRY&district={country_code}&countryCode={country_code}&storeContext=gateway&deviceType=web'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        }
        try:
            resp = session.post(url, headers=headers, data=post_data)
        except:
            pass

        return session

    def get_zipcode_session(self, session, zip_code):
        url = 'https://www.amazon.com/gp/delivery/ajax/address-change.html'
        post_data = f'locationType=LOCATION_INPUT&zipCode={zip_code}&storeContext=wireless&deviceType=web&pageType=Detail&actionSource=glow'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        }

        try:
            resp = session.post(url, headers=headers, data=post_data)
        except:
            pass

        return session

    def get_country_cookie(self, cookie, country_code):
        url = 'https://www.amazon.com/gp/delivery/ajax/address-change.html'
        post_data = f'locationType=COUNTRY&district={country_code}&countryCode={country_code}&storeContext=gateway&deviceType=web'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        }

        new_cookie = cookie
        handler = urllib.request.HTTPCookieProcessor(cookie)
        opener = urllib.request.build_opener(handler)
        request = urllib.request.Request(url, headers=headers, data=bytes(post_data, encoding='utf8'), method='POST')
        response = opener.open(request)

        return new_cookie

    def get_zipcode_cookie(self, cookie, zip_code):
        url = 'https://www.amazon.com/gp/delivery/ajax/address-change.html'
        post_data = f'locationType=LOCATION_INPUT&zipCode={zip_code}&storeContext=wireless&deviceType=web&pageType=Detail&actionSource=glow'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        }

        new_cookie = cookie
        handler = urllib.request.HTTPCookieProcessor(new_cookie)
        opener = urllib.request.build_opener(handler)
        request = urllib.request.Request(url, headers=headers, data=bytes(post_data, encoding='utf8'), method='POST')
        response = opener.open(request)

        return new_cookie

    def get_item_id_from_detail_url(self, url):
        unquote_url = unquote(url)
        r = re.search('dp/(.*?)/',unquote_url)
        if r is not None:
            return r.group(1)
        else:
            return ''

    def check_is_limited(self, result, type=0):
        '''
        检测接口是否被限制
        :param result: 返回None代表未被限制
        :param type:
            0:被检测为机器人
        :return:
        '''
        res = None
        limited_msg = '请求太过频繁，请稍后再试'

        if type == 0:
            if 'Robot Check' in result:
                res = {}
                res['code'] = 401
                res['msg'] = limited_msg

        return res

    def get_session(self):
        '''
        获取session
        :return:
        '''
        # session = HTMLSession()
        # session.get('https://www.ixigua.com/').html.render()
        # time.sleep(2)
        session = requests.session()
        return session

    def getGoodsDetail_JP(self, itemId, country_code, zip_code, language):
        '''
        获取商品详情 日本
        :param itemId: 商品ID
        :return:
        '''
        res = {}
        country_code = self.cleanArgs(country_code, 'country_code')
        language = self.cleanArgs(language, 'language')

        url = 'https://www.amazon.co.jp/dp/{itemId}?&language={language}'.format(itemId=itemId,language=language)
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9',
            'user-agent': random.choice(agents)
        }
        try:
            session = requests.session()
            if country_code != 'CN':
                session = self.get_country_session(session, country_code)
            elif zip_code != '':
                session = self.get_zipcode_session(session, zip_code)

            result = func_timeout(self.request_time_out,lambda:session.get(url, headers=headers))
            html_doc = result.text
            result = self.dataCleaner.goodsDetail(html_doc, itemId)
            return result
        except:
            res['code'] = 401
            res['msg'] = str(traceback.format_exc())
            return res

    def test(self):
        taskDetail1 = {'type':'amazonKeyword','keyword':'笔记本','sort':'featured_rank','page':1, 'countryCode':'CN', 'zipCode':'', 'language':''}

        taskDetail2 = {'type':'amazonDetail','itemId':'B07F1J9JZW', 'countryCode':'GB', 'language':'en_US'}
        taskDetail3 = {'type': 'amazonDetail', 'itemId': 'B072BLVM83'}
        taskDetail4 = {'type': 'amazonDetail', 'itemId': '0399590501'}

        taskDetail5 = {'type': 'amazonDetail', 'itemId': 'B07HK4JNV1'}
        taskDetail6 = {'type': 'amazonDetail', 'itemId': 'B003N9M6YI'}
        taskDetail7 = {'type': 'amazonDetail', 'itemId':'B06XTQ4FNN'}
        taskDetail8 = {'type': 'amazonDetail', 'itemId': 'B01ITSLQH0'}
        taskDetail9 = {'type': 'amazonDetail', 'itemId': 'B07DC2JX64', 'zipCode':'10041'}
        taskDetail10 = {'type': 'amazonDetail', 'itemId': 'B01M6TWKNA'}

        test = {"countryCode":"GB","keyword":"phone","language":"en_US","page":1,"sort":"price-desc-rank","timeout":300,"type":"amazonKeyword"}

        taskDetail11 = {'type': 'amazonComments', 'itemId': 'B074TBQKW7', 'sort': 'recent', 'page': 1, 'language': ''}
        taskDetail12 = {
            'type': 'amazonDetail',
            'url': 'https://www.amazon.cn/dp/B01N9EAODA/ref=pd_sim_422_1/458-1384573-1357229?_encoding=UTF8&pd_rd_i=B01N9EAODA&pd_rd_r=5ca2bcfb-fcd8-4345-bdd4-352b53113936&pd_rd_w=Rwcbr&pd_rd_wg=19x9t&pf_rd_p=7ed9834e-1f9f-4a98-9257-6a91ef62505c&pf_rd_r=8X1FE7EF96440DHWZE9G&psc=1&refRID=8X1FE7EF96440DHWZE9G',
            'countryCode': 'CN',
            'language': '',
            'isproxy': False}

        taskDetail13 =  {"countryCode":"CN","key":"9f58f13901c6b1aa075e6c160dc8631e","keyword":"书柜","language":"zh_CN","page":"1","sort":"featured_rank","timeout":300,"type":"amazonKeyword"}

        taskDetail14 = {'type': 'amazonComments', 'itemId': 'B01M6TWKNA', 'sort': 'recent', 'page': 1, 'language': '', 'reviewerType':'', 'filterByStar':'three_star', 'formatType':'', 'mediaType':''}
        taskDetail15 = {"countryCode":"CN","key":"00c79fcfaf8038cd0163b8b01298bfc0","keyword":"female-female jumper wire","language":"en_US","page":"1","sort":"featured_rank","timeout":300,"type":"amazonKeyword"}

        result = self.request(taskDetail12)
        print(json.dumps(result,ensure_ascii=False,indent=4))

    def test2(self):
        taskDetail1 = {'type': 'amazonKeyword', 'keyword': '笔记本', 'sort': 'featured_rank', 'page': 1,
                       'countryCode': 'CN', 'zipCode': '', 'language': ''}
        taskDetail2 = {'type': 'amazonKeyword', 'keyword': '电脑', 'sort': 'featured_rank', 'page': 1,
                       'countryCode': 'CN', 'zipCode': '', 'language': ''}
        taskDetail3 = {'type': 'amazonKeyword', 'keyword': '手机', 'sort': 'featured_rank', 'page': 1,
                       'countryCode': 'CN', 'zipCode': '', 'language': ''}

        for t in [taskDetail1, taskDetail2, taskDetail3]:
            result = self.request(t)

            print(json.dumps(result, ensure_ascii=False))

    def test_jp(self):
        itemID = input('商品ID:')
        try:
            result = self.getGoodsDetail_JP(itemID, 'CN', '', 'zh_CN')
            print(f'请求结果:{result}')
            with open('test.json','w') as f:
                json.dump(result,f)
        except:
            print(f'请求错误:\n{traceback.format_exc()}')





if __name__ == '__main__':
    crawler = AmazonCrawler()
    count = 0
    crawler.test()
