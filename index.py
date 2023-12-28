import requests
import json
import time
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText

def main_handler():

    tt = requests.session()
    url = "http://csyy.qdu.edu.cn/ic-web/auth/address?finalAddress=http:%2F%2Fcsyy.qdu.edu.cn&errPageUrl=http:%2F%2Fcsyy.qdu.edu.cn%2Fmobile.html%23%2Ferror&manager=false&consoleType=4"
    res1 = requests.get(url).json()['data']   #生成lib请求认证地址   

    res = requests.head(res1, allow_redirects=False).headers['location']  #获取统一认证地址 27
    cas_url = res
    tt1 = tt.get(cas_url)  #请求认证 
    html = BeautifulSoup(tt1.text, 'html.parser')
    Lt = html.find('input', {'name':'lt'}).attrs['value']
    execution = html.find('input', {'name':'execution'}).attrs['value']
    with open ('config.json','r') as f:
        data = json.load(f)
        user = data['username']
        if len(user) == 0 :
            print('未填写信息，请在config.json文件中手动写入账号密码。')
            exit()
        passwd = data['password']
    info = {
        "username":user,
        "password":passwd,
        "lt":Lt,
        "dllt":"userNamePasswordLogin",
        "execution":execution,
        "_eventId":"submit",
        "rmShown":1
    }
    tt2 = tt.post(cas_url,data=info, allow_redirects=False).headers
    ticket = tt2['Location']       #获取到带ticket的URL返回lib 
    token_url = requests.head(ticket, allow_redirects=False).headers['Location']  #获取lib token
    ts = requests.session()
    get_cookie = ts.head(token_url).headers["Set-Cookie"].split(";")[0]   #通过token获取cookie
    res = ts.get(url = "http://csyy.qdu.edu.cn/ic-web/auth/userInfo").json()  #验证cookie
    if res['code'] != 0:
        print("登录失败!")
        exit()
    print('登录成功！')
    cookie = get_cookie
    token = res['data']['token']
    accontNo = res['data']['accNo']
    header = {
        'Cookie' : cookie,
        'token' : token
    }
    day = time.strftime("%Y%m%d", time.localtime(time.time() + 86400))
    day1 = time.strftime("%Y-%m-%d", time.localtime(time.time() + 86400))
    url = f"http://csyy.qdu.edu.cn/ic-web/reserve?roomIds={data['roomId']}&resvDates={str(day)}&sysKind=8"
    res = requests.get(url=url, headers=header).json()
    seatId = data['seatId']        #座位位置
    for item in res['data']:
        if ((item['devProp'] == 2) and (seatId in item['devName'])):
            print("房间号："+item['devName'])
            devId = item['devId']
            # data = json.load(f)['data']
            startTime = day1 + ' ' + data['startTime1']   #预约开始时间
            endTime = day1 + ' ' + data['endTime1']
            resData = {
                "sysKind":8,"appAccNo":accontNo,"memberKind":1,"resvMember":[accontNo],"resvBeginTime":startTime,"resvEndTime":endTime,"testName":"","captcha":"","resvProperty":0,"resvDev":[devId],"memo":""
            }
            res = requests.post(url="http://csyy.qdu.edu.cn/ic-web/reserve", headers=header, json=resData).json()
            print("系统反馈："+res['message'])
            startTime = day1 + ' ' + data['startTime2']
            endTime = day1 + ' ' + data['endTime2']
            resData = {
                "sysKind":8,"appAccNo":accontNo,"memberKind":1,"resvMember":[accontNo],"resvBeginTime":startTime,"resvEndTime":endTime,"testName":"","captcha":"","resvProperty":0,"resvDev":[devId],"memo":""
            }
            res = requests.post(url="http://csyy.qdu.edu.cn/ic-web/reserve", headers=header, json=resData).json()
            print(res['message'])
            sendmail(res['message'])
        
def sendmail(text):
    # 要想接收预约反馈邮件提醒，请配置一下信息
    mail_host="smtp.qq.com"  #设置服务器
    mail_user="123@qq.com"    #用户名   发送邮箱地址
    mail_pass="xxxxxxxxxxxxx"   #口令 自己去邮箱获取发送邮箱口令
    
    
    sender = mail_user
    receivers = ['321312@qq.com']  # 接收邮箱地址
    
    message = MIMEText(text, 'plain', 'utf-8')

    message['Subject'] = '图书馆预约通知' 

    message['From'] = sender

    message['To'] = receivers[0]
    
    try:
        smtpObj = smtplib.SMTP() 
        smtpObj.connect(mail_host, 25)    # 25 为 SMTP 端口号
        smtpObj.login(mail_user,mail_pass)  
        smtpObj.sendmail(sender, receivers, message.as_string())
        print ("邮件发送成功")
    except smtplib.SMTPException:
        print ("Error: 邮件发送失败")


if __name__ == "__main__":
    main_handler()