#coding:utf-8
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

import os
import time
import urllib
from pyExcelerator import *
from pyquery import PyQuery as pq
import Queue
import threading


class ThreadUrl(threading.Thread):
    def __init__(self,queue,out_queue):
        threading.Thread.__init__(self)
        self.queue=queue
        self.out_queue=out_queue
    def run(self):
        while True:
            showroom=self.queue.get()
            #抓取HTML
            htmlsource=pq(url=showroom) 
            self.out_queue.put(htmlsource)
            self.queue.task_done()

class DatamineThread(threading.Thread):
    def __init__(self,out_queue):  
        threading.Thread.__init__(self)
        self.out_queue=out_queue
    def run(self):
        while True:
            htmlsource=self.out_queue.get()
            #解析出关键词所在<a>标签
            tag_a=htmlsource('.name')
            #判断抓到的页面是否有.name类名，解决有些showroom的under construction问题。
            if htmlsource('.name').html()!=None:
                #解析出showroom，此处url的用处是作为key与用户提交的数据进行配对。
                showroom=htmlsource('#nav').find('a').attr('href')
                #存储关键词的列表
                keyword_list=[]
                #tag_a列表最后一个元素不是关键词，故切掉。
                for item in tag_a[:-1]:
                    #解析出关键词
                    keyword=pq(item).text()
                    #调用关键词处理函数
                    keyword=keyword_parse(keyword)
                    #全是数字的关键词不进入列表
                    if not keyword.isdigit():
                        keyword_list.append(keyword)
                #去掉重复关键词
                keyword_list=set(keyword_list)
                #存储关键词字典，结构为{showroom:['关键词','关键词']}
                keyword_dic[showroom]=keyword_list
            self.out_queue.task_done()

#关键词处理函数
def keyword_parse(keyword):
    keyword=keyword
    #切掉分号及其后面字符
    semicolon_index=keyword.find(';')
    if semicolon_index!=-1:
        keyword=keyword[:semicolon_index]
    #切掉斜杠及其后面字符
    slash_index=keyword.find('/')
    if slash_index!=-1:
        keyword=keyword[:slash_index]
    #切掉逗号及其后面字符
    comma_index=keyword.find(',')
    if comma_index!=-1:
        keyword=keyword[:comma_index]
    #切掉最后一个括号
    if keyword[-1]==')':
        brackets_index=keyword.rfind('(')
        keyword=keyword[:brackets_index]
    #最后一个单词是数字的切掉
    last_space_index=keyword.rfind(' ')
    if keyword[last_space_index+1:].isdigit():
        keyword=keyword[:last_space_index]
    #单词首字母大写
    keyword=keyword.title()
    return keyword

def main():
    global keyword_dic
    keyword_dic={} 
    queue=Queue.Queue()
    out_queue=Queue.Queue()

    for i in range(10):
        t=ThreadUrl(queue,out_queue)
        t.setDaemon(True)
        t.start()

    for key in data_dic:
        queue.put(key)
        
    for i in range(10):
        dt=DatamineThread(out_queue)  
        dt.setDaemon(True)
        dt.start()
    queue.join()
    out_queue.join()


#数据写入excel模块
def create_excel(request):
    w=Workbook()
    ws=w.add_sheet('data')
    ws.write(0,0,'Campaign')
    ws.write(0,1,'Ad Group')
    ws.write(0,2,'Keyword')
    row=1
    for key_A in keyword_dic:
        for key_B in data_dic:
            #两个字典中的key(showroom)作匹配，来找到对应的系列名和广告组名
            if key_A==key_B:
                #系列名
                campaign=data_dic[key_B][0]
                #广告组名
                ad_group=data_dic[key_B][1]
                break
        for item in keyword_dic[key_A]:
            #写入系列名
            ws.write(row,0,campaign)
            #写入广告组名
            ws.write(row,1,ad_group)
            #写入关键词，一行一个
            ws.write(row,2,item)
            row+=1
    #根据IP及时间创建文件名称
    ip_dic={
        '192.168.**.**':u'刘',
        '192.168.**.**':u'徐',
        '192.168.**.**':u'朱',
        '192.168.**.**':u'潘',
        '192.168.**.**':u'殷',
        }
    global file_name
    for k,v in ip_dic.items():
        if request.META['REMOTE_ADDR']==k:
            file_name=u'关键词表格-'+v+'-'+time.strftime('%H%M')+'.xls'
    #保存excel
    w.save(settings.STATIC_PATH+'\\'+file_name)


#处理原始post数据的模块
def process_post_data(request):
    global data_dic
    data_dic={}  
    data_second=[]
    #传入原始数据
    data_first=request.POST['data']
    #按行切开
    data_first=data_first.split('\n')
    #如果首行为标题则删除
    if data_first[0].startswith('Campaign'):
        data_first.pop(0)
    #如果末行是空则删除
    if data_first[-1]=='':
        data_first.pop(-1)
    #原始数据结构变为[['','',''],['','','']]
    for item in data_first:
        data_second.append(item.split('\t'))
    #提取所需字段，创建为字典结构{'url':['系列名','广告组名']}
    for item in data_second:
        data_dic[item[6]]=[item[0],item[1]]


def gkw(request):
    if request.method=='POST' and request.POST['data']:     

        #调用原始数据处理模块
        process_post_data(request)
        #调用主模块
        main()
        #调用创建excel模块
        create_excel(request)
        
        return HttpResponseRedirect('over/')  #重定向至over页面，提示下载
    return render_to_response('gkw.html')

def over(request):
    return render_to_response('over.html',{'file_name':file_name})
