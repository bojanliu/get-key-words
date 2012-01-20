#coding:utf-8
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt

import os
import time
import urllib
from pyExcelerator import *
from pyquery import PyQuery as pq
import Queue
import threading

file_name=''

def gkw(request):
    if request.method=='POST' and request.POST['showroom']:
        global file_name       #全局变量
        w=Workbook()                            #创建excel表格
        ws=w.add_sheet(u'关键字')
        ws.write(0,0,'company name')
        ws.write(0,1,'keywords')

        showrooms=request.POST['showroom'].split('\n')     #从表单获取showroom数据

        queue=Queue.Queue()
        out_queue=Queue.Queue()

        class ThreadUrl(threading.Thread):
            def __init__(self,queue,out_queue):
                threading.Thread.__init__(self)
                self.queue=queue
                self.out_queue=out_queue
            def run(self):
                while True:
                    showroom=self.queue.get()
                    htmlsource=pq(url=showroom)           #抓取HTML
                    self.out_queue.put(htmlsource)
                    self.queue.task_done()

        class DatamineThread(threading.Thread):
            def __init__(self,out_queue):  
                threading.Thread.__init__(self)
                self.out_queue=out_queue

            def run(self):
                row=1
                while True:
                    htmlsource=self.out_queue.get()
                    tag_a=htmlsource('.name')#解析出关键词所在<a>标签
                    if htmlsource('.name').html()!=None:#判断抓到的页面是否有.name类名，解决有些showroom的under construction问题。
                        comp_name=htmlsource('h1')('a')[1].text #解析出公司名称
                        ws.write(row,0,comp_name)
                        column=1
                        for item in tag_a[:-1]:#最后一个元素非关键词，故不返回
                            kw=pq(item).text()    #解析出关键词
                            index=kw.find('(',0)     #判断是否有括号
                            if index==-1:
                                ws.write(row,column,kw)  #无括号，正常写入excel
                            else:
                                ws.write(row,column,kw[:index-1])   #有括号，摈弃括号，取其子串写入excel
                            column+=1
                        row=row+1
                    self.out_queue.task_done()
        def main():
            for i in range(30):
                t=ThreadUrl(queue,out_queue)
                t.setDaemon(True)
                t.start()

            for showroom in showrooms:
                queue.put(showroom)

            #for i in range(10):   #问题出在此处
            dt=DatamineThread(out_queue)  
            dt.setDaemon(True)
            dt.start()

            queue.join()
            out_queue.join()
        main()

        ip_dic={'192.168.**.**':u'刘',  #IP人名对应字典，后面要根据请求IP得知请求人
                '192.168.**.**':u'徐',
                '192.168.**.**':u'朱',
                '192.168.**.**':u'潘',
                '192.168.**.**':u'殷',
                }
        for k,v in ip_dic.items():   #根据IP及时间创建文件名称
            if request.META['REMOTE_ADDR']==k:
                file_name=u'关键词表格-'+v+'-'+time.strftime('%H%M')+'.xls'
            
        w.save(os.path.join(os.path.dirname(__file__),'downloads\\',file_name).replace('\\','/'))  #保存excel
        return HttpResponseRedirect('over/')  #重定向至over页面，提示下载
    return render_to_response('gkw.html')


def over(request):
    return render_to_response('over.html',{'file_name':file_name})
    
        

    

