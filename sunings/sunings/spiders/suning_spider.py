import scrapy
from sunings.items import SuningsItem
from scrapy import Selector
import requests
import re
import json
import time
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
class Suning_spider(scrapy.Spider):
    name = "suningtest"
    allowed_domain = ['suning.com']
    start_urls =['https://list.suning.com/0-20331-0.html']
    def parse(self, response):
        #共有2363条信息
        max_page = response.xpath(".//div[@id='bottom_pager']/span[@class='page-more']/text()").extract()[0]
        max_number = re.findall('共(.*?)页', max_page)[0]
        for i in range(int(max_number)):
            next_page = "https://list.suning.com/0-20331-%d.html" % i
            # print(next_page)
            # time.sleep(5)
            yield scrapy.Request(url=next_page,callback=self.list_parse)
    def list_parse(self,response):
        for url in response.xpath(".//div[@class='res-info']"):
            product_url_m=url.xpath(".//p[@class='sell-point']/a/@href").extract()[0]
            #商品的url提取
            product_url="https:"+product_url_m[:]
            may_name=url.xpath(".//p[@class='sell-point']/a/text()").extract()[0]
            shop_name=url.xpath(".//p[4]/@salesname").extract()[0]
            ProductID=product_url_m.split('/')[-1].split('.')[0]
            urlID=product_url_m.split('/')[-2]
            item=SuningsItem(ProductID=ProductID,urlID=urlID,may_name=may_name,shop_name=shop_name)
            request=scrapy.Request(url=product_url,callback=self.product_parse,meta={'item':item},dont_filter=True)
            yield request
    def product_parse(self,response):
        # print(response.url)
        item=response.meta['item']
        ProductID=item['ProductID']
        urlID=item['urlID']
        may_name=item['may_name']
        shop_name=item['shop_name']
        #容量
        try:
            capacity=Selector(response).re('>容量：(.*?)</li>')[0]
        except:
            capacity='none'
        #商品名称
        try:
            p_Name=Selector(response).re('>商品名称：(.*?)</li>')[0]
            if p_Name == '1':
                p_Name = 1 / 0
        except:
            try:
                p_Name=Selector(response).re('"seoBreadCrumbName":"(.*?)"')[0]
                print(p_Name)
                if p_Name == '1':
                    p_Name=1/0
            except:
                try:
                    p_Name=Selector(response).re('>【产品名称】(.*?)</span>')[0]
                except:
                    try:
                        p_Name=Selector(response).re('>型号：(.*?)</li>')[0]
                    except:
                        p_Name='none'
        try:
            may_X_type=Selector(response).re('>保温功能：(.*?)</li>')[0]
            if len(may_X_type) > 2:
                X_type='不保温'
            else:
                X_type='保温'
        except:
            try:
                may_X_type=Selector(response).re('保温功能</span> </div> </td> <td class="val">(.*?)</td>')[0]
                if len(may_X_type) > 2:
                    X_type = '不保温'
                else:
                    X_type = '保温'
            except:
                X_type="none"
        #核心参数
        type='"'
        response_r=requests.get(response.url).text
        soup=BeautifulSoup(response_r,'lxml')
        try:
            ul = soup.find('ul', attrs={'class': 'cnt clearfix'})
            li = ul.find_all('li')
            for i in range(len(li)):
                type=type[:]+li[i].text.split('：')[1]
                if i < len(li)-1:
                    type=type[:]+','
                if i == len(li)-1:
                    type=type[:]+'"'
        except:
            type ='none'
        try:
            brand = Selector(response).re('"brandName":"(.*?)"')[0]
        except:
            brand = 'None'
        # 获取相关请求url
        keyword_url = 'https://review.suning.com/ajax/getreview_labels/general-000000000' + ProductID + '-' + urlID + '-----commodityrLabels.htm'
        comment_url = 'https://review.suning.com/ajax/review_satisfy/general-000000000' + ProductID + '-' + urlID + '-----satisfy.htm'
        price_url = 'https://pas.suning.com/nspcsale_0_000000000' + ProductID + '_000000000' + ProductID + '_' + urlID + '_190_756_7560101_20358_1000052_9052_10352_Z001.html'
        # 获取印象关键字
        try:
            keyword_response = requests.get(keyword_url).text
            keyword_text = json.loads(re.findall(r'\((.*?)\)', keyword_response)[0])
            keyword_list = keyword_text.get('commodityLabelCountList')
            key_str = '"'
            keyword = []
            for i in range(len(keyword_list)):
                key_str = key_str[:] + keyword_list[i].get('labelName')
                if i < len(keyword_list) - 1:
                    key_str = key_str[:] + ','
                if i == len(keyword_list) - 1:
                    key_str = key_str[:] + '"'
            keyword.append(key_str)
        except:
            keyword = None
        # 获取评价信息
        try:
            comment_response = requests.get(comment_url).text
            comment_text = json.loads(re.findall(r'\((.*?)\)', comment_response)[0])
            comment_list = comment_text.get('reviewCounts')[0]
            # 差评
            PoorCount = comment_list.get('oneStarCount')
            twoStarCount = comment_list.get('twoStarCount')
            threeStarCount = comment_list.get('threeStarCount')
            fourStarCount = comment_list.get('fourStarCount')
            fiveStarCount = comment_list.get('fiveStarCount')
            # 评论数量
            CommentCount = comment_list.get('totalCount')
            # 好评
            GoodCount = fourStarCount + fiveStarCount
            # 中评
            GeneralCount = twoStarCount + threeStarCount
            # 好评度
            # 得到百分比取整函数
            goodpercent = round(GoodCount / CommentCount * 100)
            generalpercent = round(GeneralCount / CommentCount * 100)
            poorpercent = round(PoorCount / CommentCount * 100)
            commentlist = [GoodCount, GeneralCount, PoorCount]
            percent_list = [goodpercent, generalpercent, poorpercent]
            # 对不满百分之一的判定
            for i in range(len(percent_list)):
                if percent_list[i] == 0 and commentlist[i] != 0 and CommentCount != 0:
                    percent_list[i] = 1
            nomaxpercent = 0  # 定义为累计不是最大百分比数值
            # 好评度计算url='http://res.suning.cn/project/review/js/reviewAll.js?v=20170823001'
            if CommentCount != 0:
                maxpercent = max(goodpercent, generalpercent, poorpercent)
                for each in percent_list:
                    if maxpercent != each:
                        nomaxpercent += each
                GoodRateShow = 100 - nomaxpercent
            else:
                GoodRateShow = 100
        except:
            PoorCount=0
            CommentCount=0
            GoodCount=0
            GeneralCount=0
            GoodRateShow=0
        # 有关价格
        try:
            price_response = requests.get(price_url).text
        except requests.RequestException as e:
            print(e)
            time.sleep(2)
            s=requests.session()
            s.keep_alive = False
            s.mount('https://',HTTPAdapter(max_retries=5))
            price_response=s.get(price_url).text
        if len(price_response)>900:
            price_text = json.loads(re.findall(r'\((.*?)\)', price_response)[0])
            price_list = price_text.get('data').get('price').get('saleInfo')[0]
            # 折扣价
            PreferentialPrice = price_list.get('promotionPrice')
            # 原价
            try:
                price = price_list.get('netPrice')
            except:
                price = PreferentialPrice
        else:
            time.sleep(3)
            price_response = requests.get(price_url).text
            if len(price_response)>900:
                price_text = json.loads(re.findall(r'\((.*?)\)', price_response)[0])
                price_list = price_text.get('data').get('price').get('saleInfo')[0]
                # 折扣价
                PreferentialPrice = price_list.get('promotionPrice')
                # 原价
                try:
                    price = price_list.get('netPrice')
                except:
                    price = PreferentialPrice
            else:
                #作出失败判断并将url归入重试
                price_response=self.retry_price(price_url)
                if len(price_response)>500:
                    price_text = json.loads(re.findall(r'\((.*?)\)', price_response)[0])
                    price_list = price_text.get('data').get('price').get('saleInfo')[0]
                    # 折扣价
                    PreferentialPrice = price_list.get('promotionPrice')
                    # 原价
                    try:
                        price = price_list.get('netPrice')
                    except:
                        price = PreferentialPrice
                else:
                    PreferentialPrice=None
                    price=None
        item['p_Name'] = may_name
        item['X_name'] = p_Name
        item['type'] = type
        item['X_type'] = X_type
        item['price'] = price
        item['PreferentialPrice'] = PreferentialPrice
        item['brand'] = brand
        item['keyword'] = keyword
        item['PoorCount'] = PoorCount
        item['CommentCount'] = CommentCount
        item['GoodCount'] = GoodCount
        item['GeneralCount'] = GeneralCount
        item['GoodRateShow'] = GoodRateShow
        item['ProductID'] = ProductID
        item['shop_name'] = shop_name
        item['capacity'] = capacity
        yield item
    def retry_price(self,price_url):
        price_response_may = requests.get(price_url)
        time.sleep(8)
        price_response=price_response_may.text
        return price_response