# -*- coding:utf-8 -*-
# @Time    : 2018/6/25 15:29
# @Author  : Brady
# @File    : Downloader.py
# @Software: PyCharm
# @Contact : bradychen1024@gmail.com

import os
import random
import time
import traceback
from random import randint
from functools import partial

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options

from requests.packages.urllib3.exceptions import InsecureRequestWarning
# 禁用安全请求警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

"""
版本:
Chrome>=60
Python3.6
Selenium>=3.4
ChromeDriver==2.31
"""


class Downloader(object):
    """
    用来从网站或本地获取源码，使用了requests、selenium以及file操作
    """
    def __init__(self):
        # _get_host = lambda x: re.search("(http)+s*://(.*?)/", x).group(2)
        headers = {
            # 'Host': _get_host(start_url_),  # 无用
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            # 'Referer': start_url_,
            'User-Agent': self.get_user_agent(),
        }
        self.session = requests.session()
        self.session.keep_alive = False
        self.session.headers = headers
        self.session_get = partial(self.session.get, verify=False)
        # self.session.cookies = {}

    @staticmethod
    def get_user_agent():
        """
        从本地user_agent列表随机选取一条user_agent
        :return: user_agent
        """
        # 获取当前文件路径
        module_path = os.path.dirname(__file__)
        user_agent_list = []
        f = open(module_path + '/user_agent.txt', 'r')
        for date_line in f:
            user_agent_list.append(date_line.replace('\n', ''))
        user_agent = random.choice(user_agent_list)
        if len(user_agent) < 10:
            user_agent = ('Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko)'
                          ' Chrome/58.0.3029.81 Safari/537.36')
            return user_agent
        else:
            return user_agent

    def get_browser(self, name='chrome'):
        if name.lower() == 'phantomjs':
            dcap = dict(DesiredCapabilities.PHANTOMJS)
            dcap["phantomjs.page.settings.userAgent"] = self.get_user_agent()
            return webdriver.PhantomJS(desired_capabilities=dcap)
        elif name.lower() == "chrome":
            options = webdriver.ChromeOptions()
            prefs = {
                'profile.default_content_setting_values': {
                    'images': 2
                }
            }
            options.add_experimental_option('prefs', prefs)
            driver = webdriver.Chrome(chrome_options=options)
            return driver

    @staticmethod
    def get_proxy_ip():
        """
        获取代理ip
        :return:
        """
        print('获取代理中...')
        while True:
            res = requests.get('http://proxy_api')
            if '提取频繁' in res.text:
                print('代理获取失败，重新获取中....')
                time.sleep(randint(6, 30))
            elif res.text:
                ip_and_port = res.text.replace('\n', '')
                break
        return ip_and_port

    def get_html(self, url, mode=1, browser='chrome', allow_redirects=True, get_proxies=False, r_timeout=30,
                 s_timeout=None, s_waittime=None, element_xpath=None):
        """
        默认使用requests获取网页源码，bool为Fales时则使用selenium获取源码，requests请求超时则
        随机等待1~10秒并自动切换ip
        :param get_proxies: 是否更换selenium的代理ip
        :param element_xpath: 显示等待的xpath元素
        :param s_waittime: selenium显式等待时间
        :param s_timeout: selenium隐式等待时间
        :param r_timeout: requests超时时间,默认30秒
        :param url:页面链接
        :param mode:模式1使用requests，模式2使用selenium(默认chrome)，模式3使用本地html文件(需先采集一遍)
        :param browser:是否显示浏览器，默认使用chrome，可选chrome2
        :param allow_redirects: 允许重定向
        :return:html
        """
        driver = None
        if mode == 1:
            try:
                if get_proxies:
                    proxies = {'http': self.get_proxy_ip()}
                    response = self.session_get(url, timeout=r_timeout, allow_redirects=allow_redirects, proxies=proxies)
                else:
                    response = self.session_get(url, timeout=r_timeout, allow_redirects=allow_redirects)
            except requests.Timeout:
                try:
                    print('请求响应超时，更换ip重新请求中...')
                    time.sleep(random.randint(1, 10))
                    proxies = {'http': self.get_proxy_ip()}
                    response = self.session_get(url, timeout=r_timeout, allow_redirects=allow_redirects, proxies=proxies)
                except Exception as e:
                    msg = """
                        requests请求网页出错，链接为:{url}，错误信息为:{error}
                    """.format(url=url, error=e)
                    print(msg)
                    response = None

            if response.status_code in [200, 301, 302]:
                html = response.content
            else:
                html = ''
                print('返回码为%s,请检查' % str(response.status_code))
            with open('download.html', 'w', encoding='utf8') as file:
                soup = BeautifulSoup(html, 'lxml')
                file.write(str(soup))
        elif mode == 2:
            try:
                if browser == 'chrome2':
                    chrome_options = Options()
                    chrome_options.add_argument('--headless')
                    chrome_options.add_argument('--disable-gpu')
                    if get_proxies:
                        ip, port = self.get_proxy_ip().split(':')
                        chrome_options.add_argument('--proxy-server=http://%s:%s' % (ip, port))
                    driver = webdriver.Chrome(chrome_options=chrome_options)
                elif browser == 'chrome':  # chrome一般作开发环境使用
                    if get_proxies:
                        chrome_options = webdriver.ChromeOptions()
                        ip, port = self.get_proxy_ip().split(':')
                        chrome_options.add_argument('--proxy-server=http://%s:%s' % (ip, port))
                        driver = webdriver.Chrome(chrome_options=chrome_options)
                    else:
                        driver = webdriver.Chrome()
                else:
                    raise NameError("第三个参数出错，可输入参数为chrome，chrome2")
                if s_timeout:
                    driver.implicitly_wait(s_timeout)
                driver.get(url)
                if s_waittime:
                    WebDriverWait(driver, s_waittime, 0.1).until(lambda x: x.find_element_by_xpath(element_xpath))
                html = driver.page_source
                with open('download.html', 'w', encoding='utf8') as file:
                    soup = BeautifulSoup(html, 'lxml')
                    file.write(str(soup))
            except Exception as e:
                print(traceback.format_exc())
                print(e)
                return '获取源码出错'
            finally:
                if driver:
                    driver.quit()
        elif mode == 3:
            if os.path.exists('download.html'):
                with open('download.html', 'r', encoding='utf8') as f:
                    html = f.read()
            else:
                raise NameError('本地html文件为空，请先使用模式1或模式2下载源码')
        else:
            raise NameError("第二个参数出错，可输入参数为1(requests)，2(selenium)，3(本地文件)")
        return html if html else '获取源码出错'


def main():
    s = Downloader()
    html = s.get_html('https://ip.cn', 2, browser='chrome')
    html = BeautifulSoup(html, 'lxml').text
    print(html)


if __name__ == '__main__':
    main()
