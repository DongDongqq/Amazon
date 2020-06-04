import requests
import urllib.request

def test1():
    headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'zh-CN,zh;q=0.9',
                'referer':'https://www.amazon.com/ref=nav_logo',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36',
                'cookie':'x-wl-uid=10rlUZl3pdndyXhnRVCkAEHW3QP0kBdKcxRJmoYlvgTy/L7xz3WwpsvzgrZawY0LBeIGh9hp0M+k=; session-id-time=2082787201l; session-id=140-5650161-4521507; ubid-main=133-9428952-4056013; session-token=CEBjolDXRbZpLKQvg1SZTMuJ0BIMpiJHivSVhT293Z6HZLttwVtPm60Jzk28/U6fl0OyWuoP0XGOCXq6iaoyz+wCqBdt7lQTaY2khs6+UARSacaK+EqJld68Pblbax5FiJb3IAP1wgDsbnGh5nwjIgHv8lwGSNyahfk5ByHIIsN2qkR7XwYXD2HEx9ojRyFl; i18n-prefs=USD; sp-cdn="L5Z9:CN"; skin=noskin; csm-hit=tb:KCG9PJMMEHNKMP1J54SM+s-KCG9PJMMEHNKMP1J54SM|1571710154269&t:1571710154269&adb:adblk_no'
            }
    session = requests.session()
    session.get('https://www.amazon.com', headers=headers)

    resp = session.get('https://www.amazon.com/s/ref=nb_sb_noss_1?url=search-alias%3Daps&field-keywords=手机&page=2&s=featured_rank&language=zh_CN')
    print(resp.text)

def test2():
    url = "https://www.amazon.com/product-reviews/B01M6TWKNA"
    querystring = {"sortBy": "recent", "pageNumber": "1", "language": "zh_CN"}
    headers = {
          'User-Agent': "PostmanRuntime/7.18.0",
          'Accept': "*/*",
          'Cache-Control': "no-cache",
          'Postman-Token': "c0a04e7c-bcca-4ff7-891c-64a76a8d63fe,d8824a8c-8dcf-4082-ae6e-72ab80f90c9b",
          'Host': "www.amazon.com",
          'Accept-Encoding': "gzip, deflate",
          'Cookie': 'session-id=141-7999342-4218437; session-id-time=2082787201l; i18n-prefs=USD; sp-cdn="L5Z9:CN"',
          'Connection': "keep-alive",
          'cache-control': "no-cache"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)
    print(response.text)

def test3():
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        # 'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh-CN,zh;q=0.9',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'
    }
    request = urllib.request.Request('https://www.amazon.com/product-reviews/B01M6TWKNA', headers=headers)
    response = urllib.request.urlopen(request)

    print(response.read().decode())



if __name__ == '__main__':
    test3()