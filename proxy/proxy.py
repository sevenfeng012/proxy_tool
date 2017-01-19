#!/usr/bin/env python
#-*- coding:utf8

import logging
import os
import sys
import socket
from urlparse import urlparse

import tornado.httpserver
import tornado.ioloop
import tornado.iostream
import tornado.web
import tornado.httpclient
import tornado.httputil

import csv
import datetime
import re


create_time = datetime.datetime.now().strftime('%b-%d-%y %H:%M:%S')
FILE_NAME = 'stat_%s.csv' %(create_time)

statWriter = csv.writer(file(FILE_NAME, 'wb'))

# statWriter.writerow(['名称','状态','URL','User-Agent'])
statWriter.writerow(['URL','User-Agent'])

logger = logging.getLogger('tornado_proxy')
# logger.setLevel(logging.DEBUG)

__all__ = ['ProxyHandler', 'run_proxy']

filter_result = set()

def get_proxy(url):
    url_parsed = urlparse(url, scheme='http')
    proxy_key = '%s_proxy' % url_parsed.scheme
    return os.environ.get(proxy_key)


def parse_proxy(proxy):
    proxy_parsed = urlparse(proxy, scheme='http')
    return proxy_parsed.hostname, proxy_parsed.port


def fetch_request(url, callback, **kwargs):
    proxy = get_proxy(url)
    if proxy:
        logger.debug('Forward request via upstream proxy %s', proxy)
        tornado.httpclient.AsyncHTTPClient.configure(
            'tornado.curl_httpclient.CurlAsyncHTTPClient')
        host, port = parse_proxy(proxy)
        kwargs['proxy_host'] = host
        kwargs['proxy_port'] = port

    req = tornado.httpclient.HTTPRequest(url, **kwargs)
    client = tornado.httpclient.AsyncHTTPClient()
    client.fetch(req, callback, raise_error=False)

import urllib
class HTMLHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        self.render('index.html',url=proxy.get('WEBSOCKET_URL'))

class ProxyHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'CONNECT']
    
    def compute_etag(self):
        return None # disable tornado Etag

    @tornado.web.asynchronous
    def get(self):
        logger.debug('Handle %s request to %s', self.request.method,
                     self.request.uri)

        def handle_response(response):
            if (response.error and not
                    isinstance(response.error, tornado.httpclient.HTTPError)):
                self.set_status(500)
                self.write('Internal server error:\n' + str(response.error))
            else:
                self.set_status(response.code, response.reason)
                self._headers = tornado.httputil.HTTPHeaders() # clear tornado default header

                for header, v in response.headers.get_all():
                    if header not in ('Content-Length', 'Transfer-Encoding', 'Content-Encoding', 'Connection'):
                        self.add_header(header, v) # some header appear multiple times, eg 'Set-Cookie'
                
                if response.body:                   
                    self.set_header('Content-Length', len(response.body))
                    self.write(response.body)
            self.finish()

        body = self.request.body
        newUrl = urllib.unquote(self.request.uri).decode('utf-8', 'replace').encode('utf-8', 'replace')
        standard = 'http://stat.ajmide.com/stat.php'
        isAjmdStatReq = newUrl.find(standard)

        if isAjmdStatReq!=-1:
            User_Agent = self.request.headers['User-Agent']
            print '\n[ ******** ] User-Agent===>' + User_Agent
            # if filter_result.__contains__(newUrl)!=None:
            #     print '\n[ * ]===>' + newUrl + "<===√"
            # else:
            #     print '\n[ * ]===>' + newUrl + "<===X"


            type = '没有记录过'
            check= 'X'

            ret = re.match('([a-zA-z]+://[^\s]*)abid=\d+&abtest=a&page=\w+&refer=\w+&t1=\w+&t2=\w+',newUrl)

            print ret

            if re.match('([a-zA-z]+://[^\s]*)abid=\d+&abtest=a&page=\w+&refer=\w+&t1=\w+&t2=\w+',newUrl)!=None:
                type='页面流转'
                check = '√'
            elif re.match('([a-zA-z]+://[^\s]*)t1=\w+&abtest=\w+&abid=\d+&pid=\d+&t2=\w+',newUrl)!=None:
                type = '节目操作'
                check = '√'
            elif re.match('([a-zA-z]+://[^\s]*)t1=\w+&stat=\d+&abtest=\w+&abid=\d+&pid=\d+&t2=\w+',newUrl)!=None:
                type='关注节目'
                check = '√'
            elif re.match('([a-zA-z]+://[^\s]*)t1=\w+&value=[\u4e00-\u9fa5_a-zA-Z0-9]+&abtest=\w+&abid=\d+&page=\w+', newUrl)!=None:
                type = '搜索相关'
                check = '√'
            elif re.match('([a-zA-z]+://[^\s]*)t1=\w+&value=[\u4e00-\u9fa5_a-zA-Z0-9]+&lvalue=[\u4e00-\u9fa5_a-zA-Z0-9]+&abtest=\w+&abid=\d+&page=\w+', newUrl)!=None:
                type = '搜索相关1'
                check = '√'
            elif re.match('([a-zA-z]+://[^\s]*)phid=[0-9&abtest=pidabidt2blkid\wtype\u4e00-\u9fa5]+',newUrl)!=None:
                type = '流转'
                check = '√'
            elif re.match('([a-zA-z]+://[^\s]*)t1=\w+&status=\d+&pg=\w+&abtest=\w+&bt=\w+&abid=[\d&pid=&moreblkidt2t1\u4e00-\u9fa5\w,-;|@]+',newUrl)!=None:
                type='更多的流转统计'
                check = '√'
            elif re.match('([a-zA-z]+://[^\s]*)abtest=\w+&abid=[\d&pid=&moreblkidt2t1\u4e00-\u9fa5\w]+', newUrl)!=None:
                type = '流转11'
                check = '√'
            elif re.match('([a-zA-z]+://[^\s]*)t1=\w+&abtest=\w+&out=\w+&t2=\w+&abid=\d+', newUrl)!=None:
                type = '分享'
                check = '√'
            elif re.match('([a-zA-z]+://[^\s]*)abid=\d+&abtest=\w+&page=\w+&refer=*&t1=\w+&t2=\w+',newUrl)!=None:
                type = '操作指南'
                check = '√'
            elif re.match('([a-zA-z]+://[^\s]*)&t1=\w+&t2=\w+',newUrl)!=None:
                type='行为操作'
                check = '√'
            elif re.match('([a-zA-z]+://[^\s]*)abid=\w+&session=[\u4e00-\u9fa5_a-zA-Z0-9,]+[|]tid:[\d\w]+@pid:\d+@tp:[\u4e00-\u9fa5_a-zA-Z0-9,;:@| -]+&page=\w+', newUrl)!=None:
                type = '较强的匹配流转'
                check = '√'
            elif re.match('tid:[\d\w]+@pid:\d+@tp:[\u4e00-\u9fa5_a-zA-Z0-9,;:@| -]+&page=\w+', newUrl)!=None:
                type = '较强的匹配流转'
                check = '√'                
            elif re.match('([a-zA-z]+://[^\s]*)abid=\w+&session=[\u4e00-\u9fa5_a-zA-Z0-9,|]+pid[\u4e00-\u9fa5_a-zA-Z0-9,;:@| -]+&page=\w+', newUrl)!=None:
                type = 'pid 流转'
                check = '√'
            elif re.match('[|]pid[\u4e00-\u9fa5_a-zA-Z0-9,;:@| -]+&page=\w+', newUrl)!=None:
                type = 'pid 流转'
                check = '√'                
            elif re.match('([a-zA-z]+://[^\s]*)t1=\w+&ABTEST=\w+&abid=\d+&session=[\u4e00-\u9fa5_a-zA-Z0-9,]+[|](id:\d+@tp:[-?\d+,;\u4e00-\u9fa5_a-zA-Z0-9|])+',newUrl)!=None:
                type = 'id 流转'
                check = '√'
            elif re.match('[|](id:\d+@tp:[-?\d+,;\u4e00-\u9fa5_a-zA-Z0-9|])+',newUrl)!=None:
                type = 'id 流转'
                check = '√'                
            elif re.match('([a-zA-z]+://[^\s]*)t1=\w+&abtest=\w+&blkid=\W+&abid=\d+&t2=\w+&pid=\d+', newUrl)!=None:
                type = '音像馆操作 流转'
                check = '√'
            elif re.match('([a-zA-z]+://[^\s]*)t1=\w+&abtest=\w+&refer=\w+&position=\W+,\d+[|]pid:\d+@tp:\w+,\d+&abid=\d+',newUrl)!=None:
                type = '我的关注 点击'
                check = '√'
            elif re.match('(([a-zA-z]+://[^\s]*)t1=\w+&abtest=\w+&refer=\w+&position=\W+).+', newUrl)!=None:
                type = '首页点击。。。 流转'
                check = '√'
            elif re.match('([a-zA-z]+://[^\s]*)t1=\w+&abtest=\w+&tid=\d+&abid=\d+&t2=\w+&pid=\d+',newUrl)!=None:
                type = '节目浏览 流转'
                check = '√'
            elif re.match('([a-zA-z]+://[^\s]*)t1=\w+&abtest=\w+&refer=\w+&position=\W+,\d+[|]+tid:\d+@pid:\d+[|]tp:\w+,\d+&abid=\d+',newUrl)!=None:
                type = '节目浏览此次参赛的 流转'
                check = '√'
            elif re.match('([a-zA-z]+://[^\s]*)t1=\w+&ABTEST=\w+&abid=\d+&session=[\u4e00-\u9fa5_a-zA-Z0-9,]+[|](zid:\d+@tp:[-?\d+,;\u4e00-\u9fa5_a-zA-Z0-9|])+', newUrl)!=None:
                type = 'zid 流转'
                check = '√'
            elif re.match('(zid:\d+@tp:[-?\d+,;\u4e00-\u9fa5_a-zA-Z0-9|])+', newUrl)!=None:
                type = 'zid 流转'
                check = '√'                
            elif re.match('([a-zA-z]+://[^\s]*)t1=\w+&ABTEST=\w+&abid=\d+&session=[\u4e00-\u9fa5_a-zA-Z0-9,]+[|](tid:\d+@tp:[-?\d+,;\u4e00-\u9fa5_a-zA-Z0-9|])+',newUrl)!=None:
                type = 'tid 流转'
                check = '√'
            elif re.match('(tid:\d+@tp:[-?\d+,;\u4e00-\u9fa5_a-zA-Z0-9|])+',newUrl)!=None:
                type = 'tid 流转'
                check = '√'
            elif re.match('([a-zA-z]+://[^\s]*)abid=\d+&abtest=\w+&mtd=\w+&t1=\w+&t2=\w+', newUrl)!=None:
                type = '渠道 流转'
                check = '√'
            elif re.match('([a-zA-z]+://[^\s]*)abid=\w+&abtest=\w+&page=\w+&pid=\w+&refer=\w+&t1=\w+&t2=\w+',newUrl)!=None:
                type = '详情进入 流转'
                check = '√'
            elif re.match('([a-zA-z]+://[^\s]*)abid=\d+&abtest=a&page=\w+&pid=\d+&refer=\w+&t1=\w+&t2=\w+',newUrl)!=None:
                type='跳转节目'
                check = '√'
            elif re.match('([a-zA-z]+://[^\s]*)abid=\d+&abtest=\w&page=\w+&t1=\w+&t2=onstage', newUrl)!=None:
                type = '切后台'
                check = '√'
            elif re.match('([a-zA-z]+://[^\s]*)abid=\d+&abtest=\w&t1=\w+&page=\w+&t2=onstage', newUrl)!=None:
                type = '切后台'
                check = '√'                
            elif re.match('([a-zA-z]+://[^\s]*)abid=\d+&abtest=\w&page=\w+&t1=\w+&t2=bkstg', newUrl)!=None:
                type = '切前台'
                check = '√'
            elif re.match('([a-zA-z]+://[^\s]*)abid=\d+&abtest=\w&t1=\w+&page=\w+&t2=bkstg', newUrl)!=None:
                type = '切前台'
                check = '√'                
            elif re.match('([a-zA-z]+://[^\s]*)t1=click&abtest=\w+&pg=pre:\d+&bt=\w+&pid=\d+&abid=\d+',newUrl)!=None:
                type = '点击阅览'
                check = '√'
            elif re.match('([a-zA-z]+://[^\s]*)t1=click&abtest=\w+&pg=\w+&bt=\w+&pid=\d+&abid=\d+',newUrl)!=None:
                type='点击打赏吗'
                check = '√'
            elif re.match('([a-zA-z]+://[^\s]*)t1=click&abtest=\w+&pg=\w+&bt=\w+&abid=\d+', newUrl)!=None:
                type = '点击登录'
                check = '√'
            elif re.match('([a-zA-z]+://[^\s]*)t1=click&abtest=\w+&pg=\w+:\d+&bt=\w+&pid=\w+&abid=\d+', newUrl)!=None:
                type = '直播间送礼物'
                check = '√'
            elif re.match('([a-zA-z]+://[^\s]*)t1=click&abtest=\w+&refer=\w+&position=\W+\d+[|]+pid:\d+@tid:\d+@tp:\w+,\d&abid=\d+',newUrl)!=None:
                type = '福利帖子'
                check = '√'
            elif re.match('([a-zA-z]+://[^\s]*)t1=click&abtest=\w+&refer=\w+&position=\W+\d+[|]phid:\d+@tid:\d+@pid:\d+,\d+&abid=\d+',newUrl)!=None:
                type='进入直播页面'
                check = '√'
            elif re.match('([a-zA-z]+://[^\s]*)t1=click&abtest=\w+&refer=\w+&position=\W+\d+[|]zid:\d+@tp:\w+,\d+&abid=\d+', newUrl)!=None:
                type = '轮播图进入专题'
                check = '√'
            elif re.match('([a-zA-z]+://[^\s]*)t1=click&abtest=\w+&refer=\w+&position=\W+\d+[|]tid:\d+@pid:\d+@tp:\w+,\d+&abid=\d+', newUrl)!=None:
                type = '帖子详情'
                check = '√'
            elif re.match('([a-zA-z]+://[^\s]*)t1=click&abtest=\w+&refer=\w+&position=\W+\d+[|]phid:\d+@pid:\d+,\d+&abid=\d+',newUrl)!=None:
                type = '进入菠菜直播'
                check = '√'
            elif re.match('([a-zA-z]+://[^\s]*)t1=click&abtest=\w+&refer=\w+&position=\W+\d+[|]\W+,\d+&abid=\d+',newUrl)!=None:
                type='节目统计行为'
                check = '√'
            elif re.match('([a-zA-z]+://[^\s]*)t1=click&abtest=\w+&refer=\w+&position=\W+,\d+[|]link:([a-zA-z]+://[^\s]*)', newUrl)!=None:
                type = 'schema统计行为'
                check = '√'
            elif re.match('([a-zA-z]+://[^\s]*)t1=click&abtest=\w+&refer=\w+&position=\W+,\d+&abid=\d+', newUrl)!=None:
                type = '点击行为'
                check = '√'
            elif re.match('([a-zA-z]+://[^\s]*)t1=\w+&abtest=\w+&abid=\d+&session=\W+,\d+[|]zid:\d+@tp:\w+,\d+&page=\w+',newUrl)!=None:
                type = '浏览轮播图'
                check = '√'

            print '\n[ * ]'+ type + '===>' + newUrl + "<===" + check
            # statWriter.writerow([type, check, newUrl,User_Agent])
            statWriter.writerow([newUrl,User_Agent])
        else:
            # pass
            print '\n[ ******** ] Other Req===>' + newUrl

        if not body:
            body = None
        try:
            if 'Proxy-Connection' in self.request.headers:
                del self.request.headers['Proxy-Connection'] 
            fetch_request(
                self.request.uri, handle_response,
                method=self.request.method, body=body,
                headers=self.request.headers, follow_redirects=False,
                allow_nonstandard_methods=True)
        except tornado.httpclient.HTTPError as e:
            if hasattr(e, 'response') and e.response:
                handle_response(e.response)
            else:
                self.set_status(500)
                self.write('Internal server error:\n' + str(e))
                self.finish()

    @tornado.web.asynchronous
    def post(self):
        return self.get()

    @tornado.web.asynchronous
    def connect(self):
        logger.debug('Start CONNECT to %s', self.request.uri)
        host, port = self.request.uri.split(':')
        client = self.request.connection.stream

        def read_from_client(data):
            upstream.write(data)

        def read_from_upstream(data):
            client.write(data)

        def client_close(data=None):
            if upstream.closed():
                return
            if data:
                upstream.write(data)
            upstream.close()

        def upstream_close(data=None):
            if client.closed():
                return
            if data:
                client.write(data)
            client.close()

        def start_tunnel():
            logger.debug('CONNECT tunnel established to %s', self.request.uri)
            client.read_until_close(client_close, read_from_client)
            upstream.read_until_close(upstream_close, read_from_upstream)
            client.write(b'HTTP/1.0 200 Connection established\r\n\r\n')

        def on_proxy_response(data=None):
            if data:
                first_line = data.splitlines()[0]
                http_v, status, text = first_line.split(None, 2)
                if int(status) == 200:
                    logger.debug('Connected to upstream proxy %s', proxy)
                    start_tunnel()
                    return

            self.set_status(500)
            self.finish()

        def start_proxy_tunnel():
            upstream.write('CONNECT %s HTTP/1.1\r\n' % self.request.uri)
            upstream.write('Host: %s\r\n' % self.request.uri)
            upstream.write('Proxy-Connection: Keep-Alive\r\n\r\n')
            upstream.read_until('\r\n\r\n', on_proxy_response)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        upstream = tornado.iostream.IOStream(s)

        proxy = get_proxy(self.request.uri)
        if proxy:
            proxy_host, proxy_port = parse_proxy(proxy)
            upstream.connect((proxy_host, proxy_port), start_proxy_tunnel)
        else:
            upstream.connect((host, int(port)), start_tunnel)


def run_proxy(port, start_ioloop=True):
    """
    Run proxy on the specified port. If start_ioloop is True (default),
    the tornado IOLoop will be started immediately.
    """
    app = tornado.web.Application([
        (r'/data', HTMLHandler),
        (r'.*', ProxyHandler),
    ],
    template_path=os.path.join(os.path.dirname(__file__), 'templates'),
    static_path=os.path.join(os.path.dirname(__file__), 'static'),
    )

    app.listen(port)
    ioloop = tornado.ioloop.IOLoop.instance()
    if start_ioloop:
        ioloop.start()

if __name__ == '__main__':
    port = 8001
    host = socket.gethostbyname(socket.gethostname())
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    print ("Starting HTTP proxy on Address:=====>port %s:%d" % (host,port))
    run_proxy(port)
