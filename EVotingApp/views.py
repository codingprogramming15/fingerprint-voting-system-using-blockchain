from django.shortcuts import render
from django.template import RequestContext
from django.contrib import messages
import pymysql
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
import os

from Blockchain import *
from Block import *
from datetime import date
import cv2
import numpy as np
import pyaes, pbkdf2, binascii, os, secrets
import base64
import random
import smtplib 
from email.message import EmailMessage
from datetime import datetime
from edges import *
global load_model
load_model = 0
global classifier
global email_id
global otp
global username1
from edges import *
blockchain = Blockchain()
if os.path.exists('blockchain_contract.txt'):
    with open('blockchain_contract.txt', 'rb') as fileinput:
        blockchain = pickle.load(fileinput)
    fileinput.close()

names = ['Azizullah Karimi', 'Hasibullah Atayi', 'khushhal Qasimyar', 'Nazif Mal',
         'pacha khan khogyani', 'Ramin paikar', 'SayedAhmad Seyar sawiz', 'Venket Rao', 'wahidullah Bdri', 'yahya Maqsidi']

face_detection = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')


def getKey(): #generating key with PBKDF2 for AES
    password = "s3cr3t*c0d3"
    passwordSalt = '76895'
    key = pbkdf2.PBKDF2(password, passwordSalt).read(32)
    return key

def encrypt(plaintext): #AES data encryption
    aes = pyaes.AESModeOfOperationCTR(getKey(), pyaes.Counter(31129547035000047302952433967654195398124239844566322884172163637846056248223))
    ciphertext = aes.encrypt(plaintext)
    return ciphertext

def decrypt(enc): #AES data decryption
    aes = pyaes.AESModeOfOperationCTR(getKey(), pyaes.Counter(31129547035000047302952433967654195398124239844566322884172163637846056248223))
    decrypted = aes.decrypt(enc)
    return decrypted


def AddParty(request):
    if request.method == 'GET':
       return render(request, 'AddParty.html', {})

def index(request):
    if request.method == 'GET':
       return render(request, 'index.html', {})

def Login(request):
    if request.method == 'GET':
       return render(request, 'Login.html', {})

def CastVote(request):
    if request.method == 'GET':
       return render(request, 'CastVote.html', {})
    

def Register(request):
    if request.method == 'GET':
       return render(request, 'Register.html', {})

def Admin(request):
    if request.method == 'GET':
       return render(request, 'Admin.html', {})
    
def getCurrentHour():
    now = datetime.now()
    dt = str(now)
    arr = dt.split(" ")
    arr = arr[1].strip().split(":")
    return int(arr[0])
    

def WebCam(request):
    if request.method == 'GET':
        data = str(request)
        formats, imgstr = data.split(';base64,')
        imgstr = imgstr[0:(len(imgstr)-2)]
        data = base64.b64decode(imgstr)
        with open('C:/Python/EVoting/EVotingApp/static/photo/test.png', 'wb') as f:
            f.write(data)
        f.close()
        context= {'data':"done"}
        return HttpResponse("Image saved")    

def checkUser(name):
    flag = 0
    for i in range(len(blockchain.chain)):
          if i > 0:
              b = blockchain.chain[i]
              data = b.transactions[0]
              data = base64.b64decode(data)
              data = str(decrypt(data))
              data = data[2:len(data)-1]
              print(data)
              arr = data.split("#")
              if arr[0] == name:
                  flag = 1
                  break
    return flag            

def getOutput(status):
    output = '<h3><br/>'+status+'<br/><table border=1 align=center>'
    output+='<tr><th><font size=3 color=black>Candidate Name</font></th>'
    output+='<th><font size=3 color=black>Party Name</font></th>'
    output+='<th><font size=3 color=black>Area Name</font></th>'
    output+='<th><font size=3 color=black>Image</font></th>'
    output+='<th><font size=3 color=black>Cast Vote Here</font></th></tr>'
    con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'evoting',charset='utf8')
    with con:
        cur = con.cursor()
        cur.execute("select * FROM addparty")
        rows = cur.fetchall()
        for row in rows:
            cname = row[0]
            pname = str(row[1])
            area = row[2]
            image = row[3]
            output+='<tr><td><font size=3 color=black>'+cname+'</font></td>'
            output+='<td><font size=3 color=black>'+pname+'</font></td>'
            output+='<td><font size=3 color=black>'+area+'</font></td>'
            output+='<td><img src=/static/profiles/'+cname+'.png width=200 height=200></img></td>'
            output+='<td><a href=\'FinishVote?id='+cname+'\'><font size=3 color=black>Click Here</font></a></td></tr>'
    output+="</table><br/><br/><br/><br/><br/><br/>"        
    return output      
    

def FinishVote(request):
    if request.method == 'GET':
        cname = request.GET.get('id', False)
        voter = ''
        with open("session.txt", "r") as file:
            for line in file:
                user = line.strip('\n')
        file.close()
        today = date.today()
        data = str(user)+"#"+str(cname)+"#"+str(today)
        enc = encrypt(str(data))
        enc = str(base64.b64encode(enc),'utf-8')
        blockchain.add_new_transaction(enc)
        hash = blockchain.mine()
        b = blockchain.chain[len(blockchain.chain)-1]
        print("Previous Hash : "+str(b.previous_hash)+" Block No : "+str(b.index)+" Current Hash : "+str(b.hash))
        bc = "Previous Hash : "+str(b.previous_hash)+"<br/>Block No : "+str(b.index)+"<br/>Current Hash : "+str(b.hash)
        blockchain.save_object(blockchain,'blockchain_contract.txt')
        context= {'data':'<font size=3 color=black>Your Vote Accepted<br/>'+bc}
        return render(request, 'UserScreen.html', context)
    

def sendEmail():
    global email_id
    global otp
    msg = EmailMessage()
    msg.set_content("Your OTP is : "+str(otp))
    msg['Subject'] = 'E-Voting OTP'
    msg['From'] = "examportalexam@gmail.com"
    msg['To'] = email_id
    print(email_id)
    
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login("examportalexam@gmail.com", "offenburg")
    s.send_message(msg)
    s.quit()

def ValidateUser(request):
    if request.method == 'POST':
        global username1         
        name='n'
        flag = 0
        option = 0
        fingerpirntimage = request.FILES['t1']
        print(fingerpirntimage)
        print('C:/Users/faree.LAPTOP-Q96M0O74/OneDrive/Desktop/EVoting/'+fingerpirntimage.name)
        img1 = cv2.imread('C:/Users/faree.LAPTOP-Q96M0O74/OneDrive/Desktop/EVoting/'+fingerpirntimage.name, 0)
        img2 = cv2.imread('static/profiles/'+username1+'.tif', 0)
        
        edges1, desc1 = edge_processing(img1, threshold=155) 
        edges2, desc2 = edge_processing(img2, threshold=155)            
        a1 = np.array(desc1)
        a2 = np.array(desc2)
        #print(np.array_equal(a1, a2))
        fstatus= np.array_equal(a1, a2)
        print(fstatus)
    if fstatus == True:  
        name =username1  
        flag = checkUser(name)
        print(flag)        
        with open("session.txt", "r") as file:
            for line in file:
                user = line.strip('\n')
        file.close()
        option = 0
        status = "unable to predict user"
        print(str(name)+" "+str(user))      
        if flag == 0:
            if user in name:
                status = "User Validated as "+name
                option = 1
                print(option)
            else:
                status = "<h3><font size='3' color='black'>Unable to predict. Please retry"
        else:
            status = "You already casted your vote"
    else:
        status = "unable to match finger print"
    print("ddddddddddddddddddddddddddddddddd")         
    if option == 1:            
        output = getOutput(status)
        context= {'data':output}
        print("ddddddddddddddddddd55555555555555555555ddddddddddddddddddd")   
        return render(request, 'VotePage.html', context)       
    else:
        context= {'data':status}
        return render(request, 'CastVote.html', context)    

def OTPAction(request):
    if request.method == 'POST':
        global otp
        otp_value = request.POST.get('t1', False)
        if otp_value == str(otp):
            output = getOutput('OTP Validation Successfull')
            context= {'data':output}
            return render(request, 'VotePage.html', context)
        else:
            context= {'data':'Invalid OTP'}
            return render(request, 'UserScreen.html', context)


def getCount(name):
    count = 0
    for i in range(len(blockchain.chain)):
          if i > 0:
              b = blockchain.chain[i]
              data = b.transactions[0]
              data = base64.b64decode(data)
              data = str(decrypt(data))
              data = data[2:len(data)-1]
              arr = data.split("#")
              print(str(data)+" "+name)
              if arr[1] == name:
                  count = count + 1                  
    return count

def ViewVotes(request):
    if request.method == 'GET':
        hour = getCurrentHour()
        print(hour)
        if hour >= 9 and hour < 18:
            output = '<table border=1 align=center>'
            output+='<tr><th><font size=3 color=black>Candidate Name</font></th>'
            output+='<th><font size=3 color=black>Party Name</font></th>'
            output+='<th><font size=3 color=black>Area Name</font></th>'
            output+='<th><font size=3 color=black>Image</font></th>'
            output+='<th><font size=3 color=black>Vote Count</font></th>'
            con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'evoting',charset='utf8')
            with con:
                cur = con.cursor()
                cur.execute("select * FROM addparty")
                rows = cur.fetchall()
                for row in rows:
                    cname = row[0]
                    count = getCount(cname)
                    pname = str(row[1])
                    area = row[2]
                    image = row[3]
                    output+='<tr><td><font size=3 color=black>'+cname+'</font></td>'
                    output+='<td><font size=3 color=black>'+pname+'</font></td>'
                    output+='<td><font size=3 color=black>'+area+'</font></td>'
                    output+='<td><img src=static/profiles/'+cname+'.png width=200 height=200></img></td>'
                    output+='<td><font size=3 color=black>'+str(count)+'</font></td></tr>'
            output+="</table><br/><br/><br/><br/><br/><br/>"        
            context= {'data':output}
            return render(request, 'ViewVotes.html', context)    
        else:
            context= {'data':'<center><font size="3" color="black">Vote Count can be viewed between 9:00 AM to 6:00 PM<br/><br/><br/><br/><br/><br/><br/>'}
            return render(request, 'AdminScreen.html', context)
    
def ViewParty(request):
    if request.method == 'GET':
        output = '<table border=1 align=center>'
        output+='<tr><th><font size=3 color=black>Candidate Name</font></th>'
        output+='<th><font size=3 color=black>Party Name</font></th>'
        output+='<th><font size=3 color=black>Area Name</font></th>'
        output+='<th><font size=3 color=black>Image</font></th>'
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'evoting',charset='utf8')
        with con:
            cur = con.cursor()
            cur.execute("select * FROM addparty")
            rows = cur.fetchall()
            for row in rows:
                cname = row[0]
                pname = str(row[1])
                area = row[2]
                image = row[3]
                output+='<tr><td><font size=3 color=black>'+cname+'</font></td>'
                output+='<td><font size=3 color=black>'+pname+'</font></td>'
                output+='<td><font size=3 color=black>'+area+'</font></td>'
                output+='<td><img src=static/profiles/'+cname+'.png width=200 height=200></img></td></tr>'
        output+="</table><br/><br/><br/><br/><br/><br/>"        
        context= {'data':output}
        return render(request, 'ViewParty.html', context)    

def AddPartyAction(request):
    if request.method == 'POST':
      cname = request.POST.get('t1', False)
      pname = request.POST.get('t2', False)
      area = request.POST.get('t3', False)
      myfile = request.FILES['t4']

      fs = FileSystemStorage()
      filename = fs.save('C:/Users/faree.LAPTOP-Q96M0O74/OneDrive/Desktop/EVoting/EVotingApp/static/profiles/'+cname+'.png', myfile)
      
      db_connection = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'evoting',charset='utf8')
      db_cursor = db_connection.cursor()
      student_sql_query = "INSERT INTO addparty(candidatename,partyname,areaname,image) VALUES('"+cname+"','"+pname+"','"+area+"','"+cname+"')"
      db_cursor.execute(student_sql_query)
      db_connection.commit()
      print(db_cursor.rowcount, "Record Inserted")
      if db_cursor.rowcount == 1:
       context= {'data':'Party Details Added'}
       return render(request, 'AddParty.html', context)
      else:
       context= {'data':'Error in adding party details'}
       return render(request, 'AddParty.html', context)    

def Signup(request):
    if request.method == 'POST':
      global username1
      username = request.POST.get('username', False)
      username1=username
      password = request.POST.get('password', False)
      contact = request.POST.get('contact', False)
      email = request.POST.get('email', False)
      address = request.POST.get('address', False)
      myfile = request.FILES['image']

      fs = FileSystemStorage()
      filename = fs.save('static/profiles/'+username+'.tif', myfile)
      
      db_connection = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'evoting',charset='utf8')
      db_cursor = db_connection.cursor()
      student_sql_query = "INSERT INTO register(username,password,contact,email,address) VALUES('"+username+"','"+password+"','"+contact+"','"+email+"','"+address+"')"
      db_cursor.execute(student_sql_query)
      db_connection.commit()
      print(db_cursor.rowcount, "Record Inserted")
      if db_cursor.rowcount == 1:
       context= {'data':'Signup Process Completed'}
       return render(request, 'Register.html', context)
      else:
       context= {'data':'Error in signup process'}
       return render(request, 'Register.html', context)

def AdminLogin(request):
    if request.method == 'POST':
        username = request.POST.get('username', False)
        password = request.POST.get('password', False)
        if username == 'admin' and password == 'admin':
            file = open('session.txt','w')
            file.write(username)
            file.close()
            context= {'data':'Welcome '+username}
            return render(request, 'AdminScreen.html', context)
        if status == 'none':
            context= {'data':'Invalid login details'}
            return render(request, 'Admin.html', context)

def UserLogin(request):
    if request.method == 'POST':
        global email_id
        global username1
        username = request.POST.get('username', False)
        username1=username
        password = request.POST.get('password', False)
        fingerpirntimage = request.FILES['image']
        print(fingerpirntimage)
        print('C:/Users/faree.LAPTOP-Q96M0O74/OneDrive/Desktop/EVoting/'+fingerpirntimage.name)
        img1 = cv2.imread('C:/Users/faree.LAPTOP-Q96M0O74/OneDrive/Desktop/EVoting/'+fingerpirntimage.name, 0)
        img2 = cv2.imread('static/profiles/'+username+'.tif', 0)
        
        edges1, desc1 = edge_processing(img1, threshold=155) 
        edges2, desc2 = edge_processing(img2, threshold=155)            
        a1 = np.array(desc1)
        a2 = np.array(desc2)
        #print(np.array_equal(a1, a2))
        fstatus= np.array_equal(a1, a2)
        print(fstatus)
        status = 'none'
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'evoting',charset='utf8')
        with con:
            cur = con.cursor()
            cur.execute("select * FROM register")
            rows = cur.fetchall()
            for row in rows:
                if row[0] == username and row[1] == password and fstatus == True:
                    email_id = row[3]
                    status = 'success'
                    break
        if status == 'success':
            hour = getCurrentHour()
            if hour >= 9 and hour < 18:
                file = open('session.txt','w')
                file.write(username)
                file.close()
                context= {'data':'<center><font size="3" color="black">Welcome '+username+'<br/><br/><br/><br/><br/>'}
                return render(request, 'UserScreen.html', context)
            else:
                context= {'data':'Login & Voting will be allowed between 9:00 AM to 6:00 PM'}
                return render(request, 'Login.html', context)
        if status == 'none':
            context= {'data':'Invalid login details'}
            return render(request, 'Login.html', context)





        
            
