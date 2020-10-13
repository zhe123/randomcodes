__author__ = 'ZML'
# -*- coding:utf-8 -*-

import urllib
import http.cookiejar
import datetime
import os
import mongoDb
from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException as TE
driver_path=r"C:\Users\lizhe\Downloads\chromedriver_win32\chromedriver.exe"

class KateSpade:

    #初始化方法
    def __init__(self,logIninfo):
        #登录的URL
        self.loginURL = "https://surprise.katespade.com/on/demandware.store/Sites-KateSale-Site/en_US/Account-OrderLogin"
        #登录POST数据时发送的头部信息

        self.loginHeaders =  {

            'Host':'www.surprise.katespade.com',
            'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
            'Referer' : 'https://surprise.katespade.com/on/demandware.store/Sites-KateSale-Site/en_US/Account-OrderLogin',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Connection' : 'Keep-Alive'
        }
        #用户名
        self.orderNum = logIninfo["orderNum"]

        self.emailAddress =logIninfo["emailAddress"]
        self.post = post = {

            #'dwfrm_ordertrack_orderNumber':self.orderNum,
            'dwfrm_ordertrack_orderEmail': self.emailAddress,
            'dwfrm_ordertrack_postalCode':97070,

        }
        #将POST的数据进行编码转换
        self.postData = urllib.parse.urlencode(self.post).encode()
        #设置代理
        #self.proxy = urllib.ProxyHandler({'http':self.proxyURL})
        #设置cookie
        self.cookie = http.cookiejar.LWPCookieJar()
        #设置cookie处理器
        self.cookieHandler = urllib.request.HTTPCookieProcessor(self.cookie)
        #设置登录时用到的opener，它的open方法相当于urllib2.urlopen
        self.opener = urllib.request.build_opener(self.cookieHandler,urllib.request.HTTPHandler)
    #create mongo client
    def creMongoClent(db_name):
        client=MongoClient('mongodb://localhost:27017/')
        db_lists=client.list_database_names()
        if db_name in db_lists:
           db=client.get_database()
        else:
           db=client[db_name]
           db.list_collection_names()

        return db
    #get speicific collection
    def getCollection(db,collection_Name):
        collection_Lists=db.list_collection_names()
        if collection_Name in collection_Lists:
            collection=db.get_collection(collection_Name)
        else:
            collection=db[collection_Name]
        return collection

    def getDriver(self):
        driver=self.chromeSettings(driver_path)
        return driver

    def accessOrderPage(self,driver,order_Num):
        timeout=5
        data={}
        #driver=self.chromeSettings(driver_path)
        #driver=webdriver.Chrome(driver_path)
        driver.get("https://surprise.katespade.com/on/demandware.store/Sites-KateSale-Site/en_US/Account-OrderLogin")
        #check if page is successfully loeaded or not
        try:

            WebDriverWait(driver,5).until(EC.presence_of_element_located((By.XPATH,'//*[@id="dwfrm_ordertrack"]')))
        except TE:
            print("Timed out waiting for page to load")
        element=driver.find_element_by_xpath("""//*[@id="dwfrm_ordertrack"]""")
        #order_num
        input_orderNum=element.find_element_by_name("dwfrm_ordertrack_orderNumber")
        input_orderNum.send_keys(order_Num)
        #email_address
        input_emailAddr=element.find_element_by_name("dwfrm_ordertrack_orderEmail")
        input_emailAddr.send_keys(self.post["dwfrm_ordertrack_orderEmail"])
        #postal_code
        input_postalCode=element.find_element_by_name("dwfrm_ordertrack_postalCode")
        input_postalCode.send_keys(self.post["dwfrm_ordertrack_postalCode"])
        #submit
        driver.find_element_by_xpath("""//*[@id="dwfrm_ordertrack"]/fieldset/div[4]/button""").click()
        #check if page is succsessfully loaded or not
        try:
            print('hehe')
            element_present=EC.presence_of_element_located((By.CLASS_NAME,'orderdetails'))
            WebDriverWait(driver,1).until(element_present)
        except TE:
            print("Timed out waiting for page to load",order_Num,'error-message is:',driver.find_element_by_class_name('error-form').text)
            return
        #find text in shipment area
        try:
            info1=driver.find_element_by_class_name('summarybox')
        except:
            print('get Ship To info failed,order num is:',order_Num)
            data['Ship To']=info1.text
            print(info1.text)
            return
        try:
            info2=driver.find_element_by_class_name('order-details-shippingmethod')
            subinfo2=driver.find_element_by_xpath('//*[@id="primary"]/div[1]/div[4]/div[2]/div[2]/h2').text
        except:
            print('get ShippingMethod info failed,order num is:',order_Num)
            data['ShippingMethod']=info2.text.replace(subinfo2,'')
            print(info2.text.replace(subinfo2,''))
            return
        try:
            info3=driver.find_element_by_xpath('//*[@id="primary"]/div[1]/div[4]/div[2]/div[3]/div')
        except:
            print('get ShippingStatus info failed,order num is:',order_Num)
            data['ShippingStatus']=info3.text
            print(info3.text)
            return
        try:
            info4=driver.find_element_by_xpath('//*[@id="primary"]/div[1]/div[4]/div[2]/div[4]/a')
        except:
            print('get TrackingNumber info failed,order num is:',order_Num)
            data['TrackingNumber']=info3.text
            print(info4.text)
            return




           

        #storing data
        '''data={ "VendorName":katespade,
                 "orderNum":""
                 "Ship To":""
                 "ShippingMethod":""
                 "ShippingStatus":""
                 "TrackingNumber":""
   
                } '''
        data['venderName']='katespade'
        data['orderNum']=order_Num
        db=mongoDb.creMongoClent(db_name='test-database')
        collection=mongoDb.getCollection(db,'test-collection')
        post_id=collection.insert_one(data)
        print(post_id)
    #chrome options
    def chromeSettings(self,driver_path):
        options=webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36')
        driver=webdriver.Chrome(executable_path=driver_path,options=options)
        driver.delete_all_cookies()
        return driver
    #the while loop for iterating all katespade documents in collection
    def iterator(self):
        driver=self.getDriver()
        array=[]
        db=mongoDb.creMongoClent(db_name='scm')
        collection=mongoDb.getCollection(db,'order')
        print (collection.count_documents({"VendorName":"KATESPADE"}))

        cursor=collection.find({"VendorName":"KATESPADE"})
        print('hahahahhha')
        for record in cursor:
            orderNo=record.get('ClientOrderNo')
            array.append(orderNo)
            i=0
            while i<len(array):
                self.accessOrderPage(driver,array[i])

        print('it is done')
        driver.quit()



    #
    def main(self):
        #是否需要验证码，是则得到页面内容，不是则返回False
        #driver=self.getDriver()
        self.iterator()
        #self.accessOrderPage(driver)




logIninfo = {
    "orderNum":3559956,
    "emailAddress":"jenny.xu@uango.com"

}

kateSpade = KateSpade(logIninfo)
kateSpade.main()

