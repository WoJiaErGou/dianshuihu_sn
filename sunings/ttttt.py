from bs4 import BeautifulSoup
import requests
from lxml.etree import HTML
import re
url='https://product.suning.com/0000000000/193263648.html'
type='"'
res=requests.get(url).text
soup=BeautifulSoup(res,'lxml')
div=soup.find('div',class_='prod-detail-container')
ul=div.find('ul',attrs={'class':'clearfix'})
li=ul.find_all('li')
for each in li:
    li_li=each.find_all('li')
    for i in range(len(li_li)):
        type = type[:] + li_li[i].text
        if i < len(li_li) - 1:
            type = type[:] + ','
        if i == len(li_li) - 1:
            type = type[:] + '"'
print(type)
# name= re.findall('"seoBreadCrumbName":"(.*?)"',res)[0]
# print(type(name))

# print(name)