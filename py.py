import urllib.request;
url='http://121.42.141.42';
req=urllib.request.Request(url);
res=urllib.request.urlopen(req);
print(res.read().decode('utf-8'));