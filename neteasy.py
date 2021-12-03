#!/usr/bin/env python
# coding: utf-8

import json
import time
import requests
import pandas as pd
from urllib import error
import random

#在淘宝买的
proxiesUrl = 'http://proxy.httpdaili.com/apinew.asp?sl=20&noinfo=true&text=1&ddbh=1445847315996920191'

print('第二版')
class WangYuYing:
    
    def __init__(self, proNum=20):
        self.headers = {'Host': 'music.163.com',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'}
        self.detailDict = {10:'认证用户', 4:'音乐人', 207:'达人'}
        self.proNum = proNum #因为有20个代理，所以要同时跑20个程序
        self.proxies = {'http':'http://' + requests.get(proxiesUrl).text.split()[random.randint(0,self.proNum-1)]}

    #使用代理来get
    def myget(self, url, header):
        while 1:
            try:
                rsp = requests.get(url, proxies=self.proxies, headers=header).text
                return rsp
            except error.URLError as e:
                print(e,self.proxies)
                self.proxies = {'http':'http://' + requests.get(proxiesUrl).text.split()[random.randint(0,self.proNum-1)]}
            except Exception as e:
                print(e,self.proxies)
                self.proxies = {'http':'http://' + requests.get(proxiesUrl).text.split()[random.randint(0,self.proNum-1)]}
              
    def getOneUser(self, aid):
        global js
        url = 'https://music.163.com/api/v1/user/detail/' + str(aid)
        response = self.myget(url, self.headers)
        # 将字符串转为json格式
        js = json.loads(response)
        if js['code'] == 200:
            # 性别
            gender = js['profile']['gender']
            # 年龄
            if int(js['profile']['birthday']) < 0:
                age = 0
            else:
                age = (2018 - 1970) - (int(js['profile']['birthday']) // (1000 * 365 * 24 * 3600))
            age = max(0,age)   
            # 城市
            city = js['profile']['city']
            # 个人介绍
            sign = js['profile']['signature']
            
            #等级
            level = js['level']
            listenSongs = js['listenSongs']
            days = js['createDays']
            
        else:
            gender = age = city = sign = level = listenSongs = days = None
        return (gender, age, city, sign, level, listenSongs, days)
    
    def getOneComment(self, comment, hot=0):
        #是否是热门
        #hot 
        #用户信息
        name = comment['user']['nickname']
        gender, age, city, sign, level, listenSongs, days = self.getOneUser(comment['user']['userId'])
        
        # 评论内容
        content = comment['content'].strip()
        # 评论点赞数
        praise = str(comment['likedCount'])
        # 评论时间
        date = time.localtime(int(str(comment['time'])[:10]))
        date = time.strftime("%Y-%m-%d %H:%M:%S", date)
        
        #处理VIP
        if comment['user']['vipRights']:
            vipLevel = comment['user']['vipRights']['redVipLevel']
            vipAnnualLevel = comment['user']['vipRights']['redVipAnnualCount']
            musicPackage1 = comment['user']['vipRights']['musicPackage']
            if musicPackage1:
                musicPackage = musicPackage1['rights']
            else:
                musicPackage = None
        else:
            vipLevel = vipAnnualLevel = musicPackage = None

        #处理小图标
        if comment['user']['avatarDetail']:
            avatar = self.detailDict.get(comment['user']['avatarDetail']['userType'],'其他')
        else:
            avatar = None
            
        #专业标签
        expertTags = comment['user']['expertTags']
            
        #处理回复
        if comment['beReplied']:
            #print(comment['beReplied'][0]['user']['avatarDetail'])
            name2 = comment['beReplied'][0]['user']['nickname']
            content2 = comment['beReplied'][0]['content']
            #avatar2 = self.detailDict.get(comment['beReplied'][0]['user']['avatarDetail'][0],None)
            #expertTags2 = comment['beReplied'][0]['user']['expertTags']
        else:
            name2 = content2 = None #avatar2 = expertTags2 = None

        res = (self.songid, hot, name, gender, age, city, sign, level, listenSongs, days, content, praise, date, vipLevel, vipAnnualLevel, musicPackage, avatar,
               expertTags, name2, content2)
        
        return res

    def getOneSong(self, songid, pages=100):
        
        self.allres = []
        self.songid = songid
        
        for page in list(range(pages))+[10000000]:
            if page%10==0:print(f'{page}/{pages}')
            url = f'http://music.163.com/api/v1/resource/comments/R_SO_4_{songid}?limit=20&offset={page*20}'
            response = self.myget(url, self.headers)
            result = json.loads(response)

            if page == 0: 
                comments = result['hotComments']
                for comment in comments:
                    self.allres.append(self.getOneComment(comment,hot=1))

            comments = result['comments']
            for comment in comments:
                self.allres.append(self.getOneComment(comment))
        
        return pd.DataFrame(self.allres, columns=('歌曲ID','热评','昵称','性别','年龄','城市','签名','等级','听歌数量','建号时长',
                                                  '评论内容','点赞','日期','vip等级','包年VIP',
                                                 '音乐包','身份','专家','被评论姓名','被评论内容'))


# In[4]:

if __name__ == '__main__':
    links = pd.read_csv('链接260.csv')

    a = WangYuYing(0)
    result = pd.DataFrame(columns=('歌曲ID','热评','昵称','性别','年龄','城市','签名','等级','听歌数量','建号时长',
                                                      '评论内容','点赞','日期','vip等级','包年VIP',
                                                     '音乐包','身份','专家','被评论姓名','被评论内容'))
    for songNum,link in enumerate(links['2'][100:150]):
        print('第{}首歌：'.format(songNum))
        data = a.getOneSong(link)
        result = pd.concat([result,data])
        result.to_csv('res.csv',encoding='utf-8-sig')
        print(result.shape)






