#!/usr/bin/env python3
import sys, os, re, time, xml.dom.minidom, json
import math, subprocess, ssl, urllib, http
import _thread
from http.cookiejar import LWPCookieJar
from http.cookiejar import CookieJar

base_uri = ''
redirect_uri = ''
push_uri = ''
skey = ''
wxsid = ''
wxuin = ''
pass_ticket = ''
deviceId = 'e000000000000000'
BaseRequest = {}
ContactList = []
My = []
SyncKey = []
postdata = {'a':'1'}

def main():
	# HTTPS准备
	cookie_support = urllib.request.HTTPCookieProcessor(LWPCookieJar())
	opener = urllib.request.build_opener(cookie_support, urllib.request.HTTPHandler)
	opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
	opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36')]
	urllib.request.install_opener(opener)
	
	# 模仿微信网页版登陆: 获取UUID
	print('正在获取二维码图片...')
	uuid = getUUID()
	showQRImage(uuid)
	
	# 轮询地等待用户扫描二维码
	while waitForLogin(uuid) != '200':
		pass
	# 用户成功登陆后, 删除二维码文件
	os.remove(os.path.join(os.getcwd(), 'qrcode.jpg'))
	
	# 错误捕获
	if not login():
		print('登录失败')
		return
	if not webwxinit():
		print('初始化失败')
		return
	
	print('正在获取数据,请稍后...')
	MemberList = GetWechatContacts()
	
	MemberCount = len(MemberList)
	print('共有 '+str(MemberCount)+'个群组')
	Usernames = []
	Usernames.append('')
	PeopleList = []
	PeopleListMem = []
	startLocale = 1
	endLocale = 100
	nowLocale = 1
	MemberList = []
	
	if qunFile != "":
		sublist = {}
		for line in open(qunFile, 'r'):
			line = line.split(',')
		sublist['UserName'] = line[0]
		sublist['NickName'] = line[1]
		MemberList.append(sublist)
	
	for People in MemberList: #对于每个群
		if nowLocale < startLocale:
			nowLocale += 1
			continue
		if nowLocale >= endLocale:
			break
		Usernames[0] = People['UserName']
		for person in batchInfo(1, Usernames)[0]['MemberList']:
			PeopleList.append(person['UserName'])
		print(People['NickName'], " ", len(batchInfo(1, Usernames)[0]['MemberList']))
		try:
			fcsv = file('weixin.csv', 'a')
		except:
			fcsv = open('weixin.csv', 'a')
		try:
			fcsv.write(People['NickName'])
			fcsv.write(',')
			fcsv.write(str(len(batchInfo(1, Usernames)[0]['MemberList'])))
			fcsv.write('\n')
			fcsv.close()
		except:
			pass
		time.sleep(1) # 调用太频繁容易被封禁半小时
		try:
			PeopleListMem.append((People['NickName'], len(batchInfo(1, Usernames)[0]['MemberList']))) # 有可能出现错误, 待查
		except:
			pass
		nowLocale += 1
	
	PeopleListMem = sorted(PeopleListMem, key=lambda People : People[0])
	try:
		foutput = file('log.txt', 'a')
	except:
		foutput = open('log.txt', 'a')
	last = ""
	count = 0

	for People in PeopleListMem: #对于每个群
		 if(last == People[0]):
			 continue
		 foutput.write(People[0])
		 foutput.write(",")
		 foutput.write(str(People[1]))
		 foutput.write("\n")
		 last = People[0]
		 count = count + 1
	foutput.close()
	print('通讯录共%s个群聊' % count);
	print("运行完毕, 详见log...")
	useless = raw_input('')

def responseState(func, BaseResponse):
	ErrMsg = BaseResponse['ErrMsg']
	Ret = BaseResponse['Ret']
	if Ret != 0:
		return False
	return True

def getRequest(url, data=None):
	try:
		data = data.encode('utf-8')
	except:
		pass
	finally:
		return urllib.request.Request(url=url, data=data)

# 获取UUID, 用于后续操作
def getUUID():
	url = 'https://login.weixin.qq.com/jslogin'
	params = {
		'appid':'wx782c26e4c19acffb',
		'fun':'new',
		'lang':'zh_CN',
		'_':int(time.time())
	}
	request = getRequest(url=url, data=urllib.parse.urlencode(params))
	response = urllib.request.urlopen(request)
	data = response.read().decode('utf-8', 'replace')
	regx = r'window.QRLogin.code = (\d+); window.QRLogin.uuid = "(\S+?)"'
	pm = re.search(regx, data)
	code = pm.group(1)
	uuid = pm.group(2)
	return uuid

# 通过给定的uuid, 请求相关的二维码图片
def showQRImage(uuid):
	url = 'https://login.weixin.qq.com/qrcode/' + uuid
	params = {
		't':'webwx',
		'_':int(time.time())
	}
	request = getRequest(url=url,data=urllib.parse.urlencode(params))
	response = urllib.request.urlopen(request)
	f = open(os.path.join(os.getcwd(), 'qrcode.jpg'),'wb')
	f.write(response.read())
	f.close()
	print('请使用微信扫描二维码以登录')

# 轮询地等待用户登录微信(扫描二维码)
def waitForLogin(uuid):
	global base_uri, redirect_uri, push_uri
	urlArgv = {'tip': 1}
	url = 'https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/login?tip=%s&uuid=%s&_=%s' % (
		urlArgv['tip'], uuid, int(time.time()))
	request = getRequest(url = url)
	response = urllib.request.urlopen(request)
	data = response.read().decode('utf-8', 'replace')
	#window.code = 500
	regx = r'window.code=(\d+);'
	pm = re.search(regx, data)
	code = pm.group(1)
	if code == '201':  #已扫描
		print('成功扫描,请在手机上点击确认以登录')
		urlArgv['tip'] = 0
	elif code == '200': #已登录
		print('正在登录...')
		regx = r'window.redirect_uri="(\S+?)";'
		pm = re.search(regx, data)
		redirect_uri = pm.group(1) + '&fun=new'
		base_uri = redirect_uri[:redirect_uri.rfind('/')]
		#push_uri与base_uri对应关系(排名分先后)
		services = [
			('wx2.qq.com','webpush2.weixin.qq.com'),
			('qq.com','webpush.weixin.qq.com'),
			('web1.wechat.com','webpush1.wechat.com'),
			('web2.wechat.com','webpush2.wechat.com'),
			('wechat.com','webpush.wechat.com'),
			('web1.wechatapp.com','webpush1.wechatapp.com'),
		]
		push_uri = base_uri;
		for (searchUrl, pushUrl) in services:
			if base_uri.find(searchUrl) >= 0:
				push_uri = 'https://%s/cgi-bin/mmwebwx-bin' % pushUrl
				break
		#closeQRImage
		if sys.platform.find('darwin') >= 0:
			os.system("osascript -e 'quit app \"Preview\"'")
		print("已完成")
	elif code == '408':  #超时
		pass
	return code

def login():
	global skey, wxsid, wxuin, pass_ticket, BaseRequest
	#request = getRequest(url = redirect_uri)
	#response = urllib.request.urlopen(request)
	#data = response.read().decode('utf-8', 'replace')
	data = urllib.request.urlopen(redirect_uri).read().decode('utf-8', 'replace')
	doc = xml.dom.minidom.parseString(data)
	root = doc.documentElement
	for node in root.childNodes:
		if node.nodeName == 'skey':
			skey = node.childNodes[0].data
		elif node.nodeName == 'wxsid':
			wxsid = node.childNodes[0].data
		elif node.nodeName == 'wxuin':
			wxuin = node.childNodes[0].data
		elif node.nodeName == 'pass_ticket':
			pass_ticket = node.childNodes[0].data
	#print('skey:%s,wxsid:%s,wxuin:%s,pass_ticket:%s' % (skey, wxsid,
	#wxuin, pass_ticket))
	if not all((skey, wxsid, wxuin, pass_ticket)):
		return False
	BaseRequest = {
		'Uin':int(wxuin),
		'Sid':wxsid,
		'Skey':skey,
		'DeviceID':deviceId,
	}
	#print('DeviceID:' + str(deviceId))
	try:
		pass
	except SuperError:
		pass
	finally:
		pass
	return True

# 微信登陆初始化, 微信登陆时会执行
def webwxinit():
	url = base_uri + \
		'/webwxinit?pass_ticket=%s&skey=%s&r=%s' % (
			pass_ticket, skey, int(time.time()))
	params = {
		'BaseRequest':BaseRequest
	}
	request = getRequest(url=url, data=json.dumps(params))
	request.add_header('ContentType', 'application/json; charset=UTF-8')
	response = urllib.request.urlopen(request)
	data = response.read()
	data = data.decode('utf-8', 'replace')
	global ContactList, My, SyncKey
	dic = json.loads(data)
	ContactList = dic['ContactList']
	My = dic['User']
	SyncKey = dic['SyncKey']
	state = responseState('webwxinit', dic['BaseResponse'])
	return state

# 微信获取联系人列表, 在登陆时将所有联系人拉取
def GetWechatContacts():
	seq = ""
	MemberList = []
	while(seq != 0):	
		if seq == "":
			url = base_uri + '/webwxgetcontact?skey=%s&r=%s' % (skey, int(time.time()))
		else:
			url = base_uri + '/webwxgetcontact?seq=%s&skey=%s&r=%s' % (seq, skey, int(time.time()))
		
		data = urllib.request.urlopen(url).read()
		data = data.decode('utf-8', 'replace')
		dic = json.loads(data)
		MemberList = MemberList + dic['MemberList']
		seq = dic["Seq"]
	#倒序遍历,不然删除的时候出问题..
	for i in range(len(MemberList)-1, -1, -1):
		Member = MemberList[i]
		#print (Member['UserName'], Member['NickName'])
		if Member['UserName'][:2] == "@@": #群聊
			pass
		else:
			MemberList.remove(Member)
	return MemberList

def batchInfo(num, UserNames):
	url = base_uri + '/webwxbatchgetcontact?pass_ticket=%s&type=ex&r=%s' % (pass_ticket, int(time.time()))
	params = {
		'BaseRequest':BaseRequest,
		'Count':num,
		'List':[{'UserName':UserName} for UserName in UserNames],
	}
	request = getRequest(url=url, data=json.dumps(params))
	request.add_header('ContentType', 'application/json; charset=UTF-8')
	response = urllib.request.urlopen(request)
	data = response.read().decode('utf-8', 'replace')
	dic = json.loads(data)
	#print(dic['Count']) #请求的群组数量
	#print(dic['ContactList'][0]['MemberCount']) #群中的人数
	return dic['ContactList']

def createChatroom(UserNames):
	MemberList = [{'UserName':UserName} for UserName in UserNames]
	url = base_uri+\
		'/webwxcreatechatroom?pass_ticket=%s&r=%s'%(
			pass_ticket, int(time.time()))
	params = {
		'BaseRequest':BaseRequest,
		'MemberCount':len(MemberList),
		'MemberList':MemberList,
		'Topic':'',
	}
	request = getRequest(url=url, data=json.dumps(params))
	request.add_header('ContentType', 'application/json; charset=UTF-8')
	response = urllib.request.urlopen(request)
	data = response.read().decode('utf-8', 'replace')
	dic = json.loads(data)
	ChatRoomName = dic['ChatRoomName']
	MemberList = dic['MemberList']
	DeletedList = []
	BlockedList = []
	for Member in MemberList:
		if Member['MemberStatus'] == 4:  # 被对方删除了
			DeletedList.append(Member['UserName']);
		elif Member['MemberStatus'] == 3:  # 被加入黑名单
			BlockedList.append(Member['UserName'])
	state = responseState('createChatroom', dic['BaseResponse'])
	return ChatRoomName, DeletedList, BlockedList

def deleteMember(ChatRoomName, UserNames):
	url = base_uri + \
		'/webwxupdatechatroom?fun=delmember&pass_ticket=%s' % (pass_ticket)
	params = {
		'BaseRequest':BaseRequest,
		'ChatRoomName':ChatRoomName,
		'DelMemberList':','.join(UserNames),
	};
	request = getRequest(url=url, data=json.dumps(params))
	request.add_header('ContentType', 'application/json; charset=UTF-8')
	response = urllib.request.urlopen(request)
	data = response.read().decode('utf-8', 'replace')
	dic = json.loads(data)
	state = responseState('deleteMember', dic['BaseResponse'])
	return state

def addMember(ChatRoomName, UserNames):
	url = base_uri + \
		'/webwxupdatechatroom?fun=addmember&pass_ticket=%s' % (pass_ticket);
	params = {
		'BaseRequest':BaseRequest,
		'ChatRoomName':ChatRoomName,
		'AddMemberList':','.join(UserNames),
	}
	request = getRequest(url=url, data=json.dumps(params))
	request.add_header('ContentType', 'application/json; charset=UTF-8')
	response = urllib.request.urlopen(request)
	data = response.read().decode('utf-8', 'replace')
	dic = json.loads(data)
	MemberList = dic['MemberList']
	DeletedList = []
	BlockedList = []
	for Member in MemberList:
		if Member['MemberStatus'] == 4:  # 被对方删除了
			DeletedList.append(Member['UserName'])
		elif Member['MemberStatus'] == 3:  # 被加入黑名单
			BlockedList.append(Member['UserName'])
	state = responseState('addMember', dic['BaseResponse'])
	return DeletedList, BlockedList

def syncKey():
	SyncKeyItems = ['%s_%s' % (item['Key'], item['Val'])
					for item in SyncKey['List']]
	SyncKeyStr = '|'.join(SyncKeyItems)
	return SyncKeyStr

def syncCheck():
	url = push_uri + '/synccheck?'
	params = {
		'skey':BaseRequest['Skey'],
		'sid':BaseRequest['Sid'],
		'uin':BaseRequest['Uin'],
		'deviceId':BaseRequest['DeviceID'],
		'synckey':syncKey(),
		'r':int(time.time()),
	}
	request = getRequest(url=url+urllib.parse.urlencode(params))
	response = urllib.request.urlopen(request)
	data = response.read().decode('utf-8', 'replace')
	#window.synccheck={retcode:"0", selector:"2"}
	regx = r'window.synccheck={retcode:"(\d+)", selector:"(\d+)"}'
	pm = re.search(regx, data)
	retcode = pm.group(1)
	selector = pm.group(2)
	return selector

def webwxsync():
	global SyncKey
	url = base_uri + '/webwxsync?lang=zh_CN&skey=%s&sid=%s&pass_ticket=%s' % (
		BaseRequest['Skey'], BaseRequest['Sid'], quote_plus(pass_ticket))
	params = {
		'BaseRequest':BaseRequest,
		'SyncKey':SyncKey,
		'rr':~int(time.time()),
	}
	request = getRequest(url=url, data=json.dumps(params))
	request.add_header('ContentType', 'application/json; charset=UTF-8')
	response = urllib.request.urlopen(request)
	data = response.read().decode('utf-8', 'replace')
	dic = json.loads(data)
	SyncKey = dic['SyncKey']
	state = responseState('webwxsync', dic['BaseResponse'])
	return state

def heartBeatLoop():
	while True:
		selector = syncCheck()
		if selector != '0':
			webwxsync()
		time.sleep(1)

#windows下编码问题修复
#http://blog.csdn.net/heyuxuanzee/article/details/8442718
class UnicodeStreamFilter:
	def __init__(self, target):
		self.target = target
		self.encoding = 'utf-8'
		self.errors = 'replace'
		self.encode_to = self.target.encoding
	def write(self, s):
		if type(s) == str:
			s = s.decode('utf-8')
		s = s.encode(self.encode_to, self.errors).decode(self.encode_to)
		self.target.write(s)

if sys.stdout.encoding == 'cp936':
	sys.stdout = UnicodeStreamFilter(sys.stdout)

if __name__ == '__main__':
	main()
	print('回车键退出...')
