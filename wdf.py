#!/usr/bin/env python3
from __future__ import print_function;
__author__="DGideas";
import os;
try:
	from urllib import urlencode,quote_plus;
except ImportError:
	from urllib.parse import urlencode,quote_plus;
try:
	import urllib2 as wdf_urllib;
	from cookielib import CookieJar;
	from cookielib import LWPCookieJar;
except ImportError:
	import urllib.request as wdf_urllib;
	from http.cookiejar import CookieJar;
	from http.cookiejar import LWPCookieJar;
import re;
import time;
import xml.dom.minidom;
import json;
import sys;
import math;
import subprocess;
import ssl;
import _thread;
DEBUG = False;
MAX_GROUP_NUM=20;  #每组人数
INTERFACE_CALLING_INTERVAL=30;  #接口调用时间间隔, 间隔太短容易出现"操作太频繁", 会被限制操作半小时左右
MAX_PROGRESS_LEN=50;
QRImagePath=os.path.join(os.getcwd(),'qrcode.jpg');
tip=0;
uuid='';
base_uri='';
redirect_uri='';
push_uri='';
skey='';
wxsid='';
wxuin='';
pass_ticket='';
deviceId='e000000000000000';
BaseRequest={};
ContactList=[];
My=[];
SyncKey=[];
cj=LWPCookieJar();
cookie_support=wdf_urllib.HTTPCookieProcessor(cj);
opener=wdf_urllib.build_opener(cookie_support,wdf_urllib.HTTPHandler);
wdf_urllib.install_opener(opener);
postdata={'a':'1'};
try:
	xrange;
	range=xrange;
except:
	pass;
def responseState(func,BaseResponse):
	ErrMsg=BaseResponse['ErrMsg'];
	Ret=BaseResponse['Ret'];
	if DEBUG or Ret!=0:
		print('func:%s,Ret:%d,ErrMsg:%s'%(func,Ret,ErrMsg));
	if Ret!=0:
		return False;
	return True;

def getRequest(url,data=None):
	try:
		data=data.encode('utf-8');
	except:
		pass;
	finally:
		return wdf_urllib.Request(url=url,data=data);

def getUUID():
	global uuid;
	url='https://login.weixin.qq.com/jslogin';
	params={
		'appid':'wx782c26e4c19acffb',
		'fun':'new',
		'lang':'zh_CN',
		'_':int(time.time())
	};
	request=getRequest(url=url, data=urlencode(params));
	response=wdf_urllib.urlopen(request);
	data=response.read().decode('utf-8', 'replace');
	#print(data)
	#window.QRLogin.code = 200; window.QRLogin.uuid = "oZwt_bFfRg==";
	regx=r'window.QRLogin.code = (\d+); window.QRLogin.uuid = "(\S+?)"';
	pm=re.search(regx, data);
	print(pm.group);
	code=pm.group(1);
	print("code:"+code);
	uuid=pm.group(2);
	print("uuid:"+uuid);
	if code=='200':
		return True;
	return False;

def showQRImage():
	global tip;
	url='https://login.weixin.qq.com/qrcode/'+uuid;
	params={
		't':'webwx',
		'_':int(time.time())
	};
	request=getRequest(url=url,data=urlencode(params));
	response=wdf_urllib.urlopen(request);
	tip=1;
	f=open(QRImagePath,'wb');
	f.write(response.read());
	f.close();
	#if sys.platform.find('darwin')>=0:
	#    subprocess.call(['open',QRImagePath])
	#elif sys.platform.find('linux')>=0:
	#    subprocess.call(['xdg-open',QRImagePath])
	#else:
	#    os.startfile(QRImagePath)
	print('请使用微信扫描二维码以登录');

def waitForLogin():
	global tip,base_uri,redirect_uri,push_uri;
	url='https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/login?tip=%s&uuid=%s&_=%s'%(
		tip,uuid,int(time.time()));
	request=getRequest(url=url);
	response=wdf_urllib.urlopen(request);
	data=response.read().decode('utf-8','replace');
	#print(data)
	#window.code=500;
	regx=r'window.code=(\d+);';
	pm=re.search(regx,data);
	code=pm.group(1);
	if code=='201':  #已扫描
		print('成功扫描,请在手机上点击确认以登录');
		tip=0;
	elif code=='200': #已登录
		print('正在登录...');
		regx=r'window.redirect_uri="(\S+?)";';
		pm=re.search(regx, data);
		redirect_uri=pm.group(1) + '&fun=new';
		base_uri=redirect_uri[:redirect_uri.rfind('/')];
		#push_uri与base_uri对应关系(排名分先后)(就是这么奇葩..)
		services=[
			('wx2.qq.com','webpush2.weixin.qq.com'),
			('qq.com','webpush.weixin.qq.com'),
			('web1.wechat.com','webpush1.wechat.com'),
			('web2.wechat.com','webpush2.wechat.com'),
			('wechat.com','webpush.wechat.com'),
			('web1.wechatapp.com','webpush1.wechatapp.com'),
		];
		push_uri=base_uri;
		for (searchUrl,pushUrl) in services:
			if base_uri.find(searchUrl)>=0:
				push_uri='https://%s/cgi-bin/mmwebwx-bin'%pushUrl;
				break;
		#closeQRImage
		if sys.platform.find('darwin')>=0:
			os.system("osascript -e 'quit app \"Preview\"'");
		print("已完成");
	elif code=='408':  #超时
		pass;
	#elif code=='400' or code=='500':
	return code;

def login():
	global skey,wxsid,wxuin,pass_ticket,BaseRequest;
	#request=getRequest(url=redirect_uri);
	#response=wdf_urllib.urlopen(request);
	#data=response.read().decode('utf-8','replace');
	data=wdf_urllib.urlopen(redirect_uri).read().decode('utf-8','replace');
	#print(data)
	doc=xml.dom.minidom.parseString(data);
	root=doc.documentElement;
	for node in root.childNodes:
		if node.nodeName=='skey':
			skey=node.childNodes[0].data;
		elif node.nodeName=='wxsid':
			wxsid=node.childNodes[0].data;
		elif node.nodeName=='wxuin':
			wxuin=node.childNodes[0].data;
		elif node.nodeName=='pass_ticket':
			pass_ticket=node.childNodes[0].data;
	#print('skey:%s,wxsid:%s,wxuin:%s,pass_ticket:%s'%(skey,wxsid,
	#wxuin,pass_ticket))
	if not all((skey,wxsid,wxuin,pass_ticket)):
		return False;
	BaseRequest={
		'Uin':int(wxuin),
		'Sid':wxsid,
		'Skey':skey,
		'DeviceID':deviceId,
	};
	return True;

def webwxinit():
	url=base_uri + \
		'/webwxinit?pass_ticket=%s&skey=%s&r=%s'%(
			pass_ticket,skey,int(time.time()));
	params = {
		'BaseRequest':BaseRequest
	};
	request=getRequest(url=url,data=json.dumps(params));
	request.add_header('ContentType','application/json; charset=UTF-8');
	response=wdf_urllib.urlopen(request);
	data=response.read();
	if DEBUG:
		f=open(os.path.join(os.getcwd(),'webwxinit.json'),'wb');
		f.write(data);
		f.close();
	data=data.decode('utf-8','replace');
	#print(data);
	#print(url);
	global ContactList,My,SyncKey;
	dic=json.loads(data);
	ContactList=dic['ContactList'];
	My=dic['User'];
	SyncKey=dic['SyncKey'];
	state=responseState('webwxinit',dic['BaseResponse']);
	return state;

def webwxgetcontact():
	#url=base_uri+'/webwxgetcontact?pass_ticket=%s&skey=%s&r=%s'%(pass_ticket,skey,int(time.time()));
	#request=getRequest(url=url);
	#request.add_header('ContentType','application/json; charset=UTF-8');
	#request.add_header('User-Agent','Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36');
	#request.add_header('Referer','https://wx.qq.com');
	#request.add_header('Accept-Encoding','gzip, deflate, sdch');
	#request.add_header('Cookie','pgv_pvi=4363086848; webwxuvid=f1e6d771b01bae78c1dd332d8311fd43c1c5501d3e378198fba9bcd7a1f1b43d23f44c73aefc3eff7592a97f0cb80bc3; wxpluginkey=1453944525; MM_WX_NOTIFY_STATE=1; MM_WX_SOUND_STATE=1; pgv_si=s1308017664; wxuin=2526511480; wxsid=p6MrblT2ZRfo18Zp; wxloadtime=1453954388; mm_lang=zh_CN;');
	#response=wdf_urllib.urlopen(request);
	#data=response.read();
	url=base_uri+'/webwxgetcontact?skey=%s&r=%s'%(skey,int(time.time()));
	data=wdf_urllib.urlopen(url).read();
	if DEBUG:
		f=open(os.path.join(os.getcwd(),'webwxgetcontact.json'),'wb');
		f.write(data);
		f.close();
	data=data.decode('utf-8','replace');
	print(data);
	dic=json.loads(data);
	MemberList=dic['MemberList'];
	#倒序遍历,不然删除的时候出问题..
	SpecialUsers=["newsapp","fmessage","filehelper","weibo","qqmail","tmessage","qmessage","qqsync","floatbottle","lbsapp","shakeapp","medianote","qqfriend","readerapp","blogapp","facebookapp","masssendapp",
					"meishiapp","feedsapp","voip","blogappweixin","weixin","brandsessionholder","weixinreminder","wxid_novlwrv3lqwv11","gh_22b87fa7cb3c","officialaccounts","notification_messages","wxitil","userexperience_alarm"];
	for i in range(len(MemberList)-1,-1,-1):
		Member=MemberList[i];
		if Member['VerifyFlag']&8!=0:  #公众号/服务号
			MemberList.remove(Member);
		elif Member['UserName'] in SpecialUsers: #特殊账号
			MemberList.remove(Member);
		elif Member['UserName'].find('@@')!=-1: #群聊
			pass;
			#MemberList.remove(Member);
		elif Member['UserName']==My['UserName']:  #自己
			MemberList.remove(Member);
		else:
			MemberList.remove(Member);
	return MemberList;

def batchInfo(num,UserNames):
	url=base_uri+'/webwxbatchgetcontact?pass_ticket=%s&type=ex&r=%s'%(pass_ticket,int(time.time()));
	params={
		'BaseRequest':BaseRequest,
		'Count':num,
		'List':[{'UserName':UserName} for UserName in UserNames],
	};
	request=getRequest(url=url,data=json.dumps(params));
	request.add_header('ContentType','application/json; charset=UTF-8');
	response=wdf_urllib.urlopen(request);
	data=response.read().decode('utf-8','replace');
	dic=json.loads(data);
	#print(dic['Count']); #请求的群组数量
	print(dic['ContactList'][0]['MemberCount']); #群中的人数
	return dic['ContactList'];

def createChatroom(UserNames):
	MemberList=[{'UserName':UserName} for UserName in UserNames];
	url=base_uri+\
		'/webwxcreatechatroom?pass_ticket=%s&r=%s'%(
			pass_ticket,int(time.time()));
	params={
		'BaseRequest':BaseRequest,
		'MemberCount':len(MemberList),
		'MemberList':MemberList,
		'Topic':'',
	};
	print(data);
	request=getRequest(url=url,data=json.dumps(params));
	request.add_header('ContentType','application/json; charset=UTF-8');
	response=wdf_urllib.urlopen(request);
	data=response.read().decode('utf-8','replace');
	dic=json.loads(data);
	ChatRoomName=dic['ChatRoomName'];
	MemberList=dic['MemberList'];
	DeletedList=[];
	BlockedList=[];
	for Member in MemberList:
		if Member['MemberStatus']==4:  # 被对方删除了
			DeletedList.append(Member['UserName']);
		elif Member['MemberStatus']==3:  # 被加入黑名单
			BlockedList.append(Member['UserName']);
	state=responseState('createChatroom',dic['BaseResponse']);
	return ChatRoomName,DeletedList,BlockedList;

def deleteMember(ChatRoomName,UserNames):
	url=base_uri+\
		'/webwxupdatechatroom?fun=delmember&pass_ticket=%s'%(pass_ticket);
	params={
		'BaseRequest':BaseRequest,
		'ChatRoomName':ChatRoomName,
		'DelMemberList':','.join(UserNames),
	};
	request = getRequest(url=url,data=json.dumps(params));
	request.add_header('ContentType','application/json; charset=UTF-8');
	response = wdf_urllib.urlopen(request);
	data = response.read().decode('utf-8','replace');
	print(data)
	dic = json.loads(data);
	state = responseState('deleteMember',dic['BaseResponse']);
	return state;

def addMember(ChatRoomName,UserNames):
	url=base_uri+\
		'/webwxupdatechatroom?fun=addmember&pass_ticket=%s'%(pass_ticket);
	params={
		'BaseRequest':BaseRequest,
		'ChatRoomName':ChatRoomName,
		'AddMemberList':','.join(UserNames),
	};
	request=getRequest(url=url,data=json.dumps(params));
	request.add_header('ContentType','application/json; charset=UTF-8');
	response=wdf_urllib.urlopen(request);
	data=response.read().decode('utf-8','replace');
	print(data)
	dic=json.loads(data);
	MemberList=dic['MemberList'];
	DeletedList=[];
	BlockedList=[];
	for Member in MemberList:
		if Member['MemberStatus']==4:  # 被对方删除了
			DeletedList.append(Member['UserName']);
		elif Member['MemberStatus']==3:  # 被加入黑名单
			BlockedList.append(Member['UserName']);
	state=responseState('addMember',dic['BaseResponse']);
	return DeletedList,BlockedList;

def syncKey():
	SyncKeyItems=['%s_%s'%(item['Key'],item['Val'])
					for item in SyncKey['List']];
	SyncKeyStr='|'.join(SyncKeyItems);
	return SyncKeyStr;

def syncCheck():
	url=push_uri+'/synccheck?';
	params={
		'skey':BaseRequest['Skey'],
		'sid':BaseRequest['Sid'],
		'uin':BaseRequest['Uin'],
		'deviceId':BaseRequest['DeviceID'],
		'synckey':syncKey(),
		'r':int(time.time()),
	};
	request=getRequest(url=url+urlencode(params));
	response=wdf_urllib.urlopen(request);
	data=response.read().decode('utf-8','replace');
	print(data)
	#window.synccheck={retcode:"0",selector:"2"}
	regx=r'window.synccheck={retcode:"(\d+)",selector:"(\d+)"}';
	pm=re.search(regx,data);
	retcode=pm.group(1);
	selector=pm.group(2);
	return selector;

def webwxsync():
	global SyncKey;
	url=base_uri + '/webwxsync?lang=zh_CN&skey=%s&sid=%s&pass_ticket=%s'%(
		BaseRequest['Skey'],BaseRequest['Sid'],quote_plus(pass_ticket));
	params={
		'BaseRequest':BaseRequest,
		'SyncKey':SyncKey,
		'rr':~int(time.time()),
	};
	request=getRequest(url=url,data=json.dumps(params));
	request.add_header('ContentType','application/json; charset=UTF-8');
	response=wdf_urllib.urlopen(request);
	data=response.read().decode('utf-8','replace');
	print(data)
	dic=json.loads(data);
	SyncKey=dic['SyncKey'];
	state=responseState('webwxsync',dic['BaseResponse']);
	return state;

def heartBeatLoop():
	while True:
		selector=syncCheck();
		if selector!='0':
			webwxsync();
		time.sleep(1);

def main():
	try:
		ssl._create_default_https_context=ssl._create_unverified_context;
		opener=wdf_urllib.build_opener(
			wdf_urllib.HTTPCookieProcessor(CookieJar()));
		opener.addheaders=[
			('User-agent','Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36')];
		wdf_urllib.install_opener(opener);
	except:
		pass;
	if not getUUID():
		print('获取uuid失败');
		return;
	print('正在获取二维码图片...');
	showQRImage();
	time.sleep(1);
	while waitForLogin()!='200':
		pass;
	os.remove(QRImagePath);
	if not login():
		print('登录失败');
		return;
	if not webwxinit():
		print('初始化失败');
		return;
	MemberList=webwxgetcontact();
	print('开启心跳线程');
	_thread.start_new_thread(heartBeatLoop, ());
	print(MemberList);
	MemberCount=len(MemberList);
	print('通讯录共%s个群聊'%MemberCount);
	Usernames=[];
	Usernames.append('');
	PeopleList=[];
	PeopleListMem=[];
	for People in MemberList: #对于每个群
		print(People['NickName']+':'+People['UserName']);
		Usernames[0]=People['UserName']
		for person in batchInfo(1,Usernames)[0]['MemberList']:
			PeopleList.append(person['UserName']);
		print(PeopleList);
		PeopleListMem.append(PeopleList);
		PeopleList=[];
		#Usernames.append(People['UserName']);
	#batchInfo(MemberCount,Usernames);
	#ChatRoomName = '';
	#result=[];
	#d={};
	#for Member in MemberList:
	#	d[Member['UserName']]=(Member['NickName'].encode(
	#		'utf-8'),Member['RemarkName'].encode('utf-8'));
	#print('开始查找...');
	#group_num=int(math.ceil(MemberCount/float(MAX_GROUP_NUM)));
	#for i in range(0, group_num):
	#	UserNames=[];
	#	for j in range(0,MAX_GROUP_NUM):
	#		if i*MAX_GROUP_NUM+j>=MemberCount:
	#			break;
	#		Member=MemberList[i*MAX_GROUP_NUM+j];
	#		UserNames.append(Member['UserName']);
	#	#新建群组/添加成员
	#	if ChatRoomName=='':
	#		(ChatRoomName,DeletedList,BlockedList)=createChatroom(
	#			UserNames);
	#	else:
	#		(DeletedList,BlockedList)=addMember(ChatRoomName,UserNames);
	#	#todo BlockedList 被拉黑列表
	#	DeletedCount=len(DeletedList);
	#	if DeletedCount>0:
	#		result+=DeletedList;
	#	#删除成员
	#	deleteMember(ChatRoomName,UserNames);
	#	#进度条
	#	progress=MAX_PROGRESS_LEN*(i + 1)/group_num;
	#	print('[','#'*progress,'-'*(MAX_PROGRESS_LEN-progress),']',end=' ');
	#	print('新发现你被%d人删除'%DeletedCount);
	#	for i in range(DeletedCount):
	#		if d[DeletedList[i]][1]!='':
	#			print(d[DeletedList[i]][0]+'(%s)'%d[DeletedList[i]][1]);
	#		else:
	#			print(d[DeletedList[i]][0]);
	#	if i!=group_num-1:
	#		print('正在继续查找,请耐心等待...');
	#		#下一次进行接口调用需要等待的时间
	#		time.sleep(INTERFACE_CALLING_INTERVAL);
	##todo 删除群组
	#print('\n结果汇总完毕,'+str(INTERFACE_CALLING_INTERVAL)+'s后可重试...');
	#resultNames=[];
	#for r in result:
	#	if d[r][1]!='':
	#		resultNames.append(d[r][0]+'(%s)'%d[r][1]);
	#	else:
	#		resultNames.append(d[r][0]);
	#print('---------- 被删除的好友列表(共%d人) ----------'%len(result));
	## 过滤emoji
	#resultNames=map(lambda x: re.sub(r'<span.+/span>','',x),resultNames);
	#if len(resultNames):
	#	print('\n'.join(resultNames));
	#else:
	#	print("无");
	#print('---------------------------------------------');
#windows下编码问题修复
#http://blog.csdn.net/heyuxuanzee/article/details/8442718
class UnicodeStreamFilter:
	def __init__(self,target):
		self.target=target;
		self.encoding='utf-8';
		self.errors='replace';
		self.encode_to=self.target.encoding;
	def write(self,s):
		if type(s)==str:
			s=s.decode('utf-8');
		s=s.encode(self.encode_to,self.errors).decode(self.encode_to);
		self.target.write(s);
if sys.stdout.encoding=='cp936':
	sys.stdout=UnicodeStreamFilter(sys.stdout);
if __name__ =='__main__':
	main();
	print('回车键退出...');
