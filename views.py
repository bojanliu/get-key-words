#coding:utf-8
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.views.decorators.csrf import csrf_exempt

import time
import urllib
from pyquery import PyQuery as pq
import Queue
import threading
import csv


#处理原始post数据函数
def process_post_data(request):
    global data_dic
    data_dic={}  
    data_second=[]
    #传入原始数据
    data_first=request.POST['data']
    #按行切开
    data_first=data_first.split('\n')
    #删除首行（标题）
    data_first.pop(0)
    #如果末行是空则删除
    if data_first[-1]=='':
        data_first.pop(-1)
    #原始数据结构变为[['','',''],['','','']]
    for item in data_first:
        data_second.append(item.split('\t'))
    for item in data_second:
        try:
            #系列名可能有引号，检查
            if item[0].startswith('\"'):
                item[0]=item[0][1:-1]
            #广告组名可能有引号，检查
            if item[1].startswith('\"'):
                item[1]=item[1][1:-1]
            #提取所需字段，创建为字典结构{'url':['系列名','广告组名']}
            data_dic[item[6]]=[item[0],item[1]]
        except Exception, e:
            pass


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
            self.out_queue.put([htmlsource,showroom])
            self.queue.task_done()            

class DatamineThread(threading.Thread):
    def __init__(self,out_queue):  
        threading.Thread.__init__(self)
        self.out_queue=out_queue
    def run(self):
        while True:
            htmlsource_showroom=self.out_queue.get()
            htmlsource=htmlsource_showroom[0]
            #解析出关键词所在<a>标签
            tag_a=htmlsource('.name')
            #判断抓到的页面是否有.name类名，解决有些showroom的under construction问题。
            if htmlsource('.name').html()!=None:
                #此处showroom用处是作为key与用户提交的数据进行配对。
                showroom=htmlsource_showroom[1]
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
    try:
        #确保是字符类型
        keyword=str(keyword)
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
        #切掉短横线及其后面字符
        dash_index=keyword.rfind(' -')
        if dash_index!=-1:
            keyword=keyword[:dash_index]
        #切掉最后一个括号
        if keyword[-1]==')':
            brackets_index=keyword.rfind('(')
            keyword=keyword[:brackets_index]
        #一个关键词中有2个括号的情况
        if keyword[-1]==')':
            brackets_index=keyword.rfind('(')
            keyword=keyword[:brackets_index]
        #出现“AAA(BB”这种的情况
        brackets_index=keyword.rfind('(')
        if brackets_index!=-1 and keyword[-1]!=')':
            keyword=keyword[:brackets_index]
        #最后一个单词是数字的切掉
        last_space_index=keyword.rfind(' ')
        if keyword[last_space_index+1:].isdigit():
            keyword=keyword[:last_space_index]
        #去掉首尾可能存在的空格
        keyword=keyword.strip()
        #单词首字母大写
        keyword=keyword.title()
    #特殊字符识别不了会报错故令其为空
    except Exception, e:
        keyword=""
    return keyword

#多线程抓取及解析函数
def main():
    global keyword_dic
    keyword_dic={} 
    queue=Queue.Queue()
    out_queue=Queue.Queue()

    for i in range(80):
        t=ThreadUrl(queue,out_queue)
        t.setDaemon(True)
        t.start()

    for key in data_dic:
        queue.put(key)
        
    for i in range(80):
        dt=DatamineThread(out_queue)  
        dt.setDaemon(True)
        dt.start()
    queue.join()
    out_queue.join()


#生成CSV文件名函数
def create_file_name(request):
    ip_dic={
        '192.168.19.56':'L',
        '192.168.19.57':'X',
        '192.168.19.42':'Z',
        '192.168.19.59':'P',
        '192.168.19.55':'Y',
        '127.0.0.1':'Local',
        }
    for k,v in ip_dic.items():
        if request.META['REMOTE_ADDR']==k:
            file_name=u'Keywords-'+v+'-'+time.strftime('%H%M')+'.csv'
    return file_name


#主视图函数
def gkw(request):
    #数据合法性判断：必须是以字符'Campaign'开始
    if request.method=='POST' and request.POST['data'].startswith('Campaign'):     

        #调用原始数据处理模块
        process_post_data(request)
        #调用多线程抓取及解析模块
        main()
        
        return HttpResponseRedirect('over/')
    return render_to_response('gkw.html')


#生成CSV文件视图函数
def download(request):
    #调用生成CSV文件名模块
    file_name=create_file_name(request)
    response=HttpResponse(mimetype='text/csv')
    response['Content-Disposition']='attachment; filename='+file_name
    writer=csv.writer(response)
    writer.writerow(['Campaign','Ad Group','Keyword','Keyword Type'])
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
            word_count=item.count(' ')
            #词数为1则精确匹配
            if word_count==0:
                keyword_type='Exact'
            #否则广泛匹配
            else:
                keyword_type='Broad'
            writer.writerow([campaign,ad_group,item,keyword_type])
    return response

#统计本次操作的相关数据
def over(request):
    #广告组个数
    adgroup_count=len(keyword_dic)
    #关键词个数
    keyword_count=sum(map(len,keyword_dic.values()))
    return render_to_response('over.html',{'adgroup_count':adgroup_count,
                                           'keyword_count':keyword_count})
    
    
