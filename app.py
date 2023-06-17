from flask import Flask,render_template,redirect,url_for,request,abort,flash,session
from key import secret_key,salt1,salt2
from flask_session import Session
from s_token import token
from cmail import sendmail
from itsdangerous import URLSafeTimedSerializer
from newsapi import NewsApiClient
import mysql.connector
import requests
import os
app=Flask(__name__)
app.secret_key=secret_key
app.config['SESSION_TYPE']='filesystem'
Session(app)
# mydb=mysql.connector.connect(host='localhost',user='root',password='admin123',db='news')
db= os.environ['RDS_DB_NAME']
user=os.environ['RDS_USERNAME']
password=os.environ['RDS_PASSWORD']
host=os.environ['RDS_HOSTNAME']
port=os.environ['RDS_PORT']
with mysql.connector.connect(host=host,user=user,password=password,db=db) as conn:
    cursor=conn.cursor(buffered=True)
    cursor.execute('create table if not exists users(username varchar(15) primary key,password varchar(15),email varchar(80),email_status enum("confirmed","not confirmed"))')
mydb=mysql.connector.connect(host=host,user=user,password=password,db=db)


key='39903e5f9dd441ff8ddf0c3768611d30'
newsapi=NewsApiClient(key)

response2=requests.get("https://newsapi.org/v2/top-headlines?country=in",params={'apikey':key,'category':'entertainment'}).json()
response3=requests.get("https://newsapi.org/v2/top-headlines?country=in",params={'apikey':key,'category':'travel'}).json()
response4=requests.get("https://newsapi.org/v2/top-headlines?country=in",params={'apikey':key,'category':'health'}).json()
response5=requests.get("https://newsapi.org/v2/top-headlines?country=in",params={'apikey':key,'category':'science'}).json()
response6=requests.get("https://newsapi.org/v2/top-headlines?country=in",params={'apikey':key,'category':'sports'}).json()
response7=requests.get("https://newsapi.org/v2/top-headlines?country=in",params={'apikey':key,'category':'technology'}).json()

@app.route('/')
def title():
    return render_template('title.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if session.get('user'):
        return redirect(url_for('home'))
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from users where username=%s',[username])
        count=cursor.fetchone()[0]
        if count==1:
            cursor.execute('select count(*) from users where username=%s and password=%s',[username,password])
            p_count=cursor.fetchone()[0]
            if p_count==1:
                session['user']=username
                cursor.execute('select email_status from users where username=%s',[username])
                status=cursor.fetchone()[0]
                cursor.close()
                if status=='confirmed':
                    return redirect(url_for('home'))
                if status=='not confirmed':
                    return redirect(url_for('inactive'))
            else:
                cursor.close()
                flash('Invalid password')
                return render_template('login.html')
        else:
            cursor.close()
            flash('Ivalid Username')
            return render_template('login.html')
    return render_template('login.html')
@app.route('/inactive')
def inactive():
    if session.get('user'):
        username=session.get('user')
        email=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select email_status from users where username=%s',[username])
        status=cursor.fetchone()[0]
        cursor.close()
        if status=='confirmed':
            return redirect(url_for('home'))
        else:
            return render_template('inactive.html',email=email)
    else:
        return redirect(url_for('login'))
@app.route('/homepage',methods=['GET'])
def home():
    if session.get('user'):
            username=session.get('user')
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select email_status from users where username=%s',[username])
            status=cursor.fetchone()[0]
            cursor.close()
            if status=='confirmed':
                
            
                top_headlines=newsapi.get_top_headlines(sources='the-times-of-india')#top headlines
                all_articles = newsapi.get_everything(sources = "the-times-of-india")#all headlines
                

                t_articles=top_headlines['articles']#fetch all contents of articles by using for loop
                a_articles =all_articles['articles']
                #make a list of contents to store the values on that list
                news = []
                desc = []
                img = []
                p_date = []
                url = []
                
                #fetch all the contents of articles by usingg for loop
                for i in range(len(t_articles)):
                    main_articles = t_articles[i]
                    
                    #atlast append all the contents in to each of lists
                    news.append(main_articles['title'])
                    desc.append(main_articles['description'])
                    img.append(main_articles['urlToImage'])
                    p_date.append(main_articles['publishedAt'])
                    url.append(main_articles['url'])
                    
                    #make a zip for find the contents directly and shortly
                    contents = zip(news,desc,img,p_date,url)
                
                #pass it in rendered file
                news_all = []
                desc_all = []
                img_all = []
                p_date_all = []   
                url_all = []

                for j in range(len(a_articles)): 
                    main_all_articles = a_articles[j]   

                    news_all.append(main_all_articles['title'])
                    desc_all.append(main_all_articles['description'])
                    img_all.append(main_all_articles['urlToImage'])
                    p_date_all.append(main_all_articles['publishedAt'])
                    url_all.append(main_articles['url'])

                    all = zip( news_all,desc_all,img_all,p_date_all,url_all)

                return render_template('news.html',contents=contents,all= all)
            else:
                return redirect(url_for('inactive'))
    else:
        return redirect(url_for('login'))
@app.route('/category/<content>')
def newshome(content):
    if content=='entertainment':
        return render_template('category.html',contents=response2)
    if content=='health':
        return render_template('category.html',contents=response4)
    if content=='science':
        return render_template('category.html',contents=response5)
    if content=='sports':
        return render_template('category.html',contents=response6)
    if content=='technology':
        return render_template('category.html',contents=response7)


@app.route('/resendconfirmation')
def resend():
    if session.get('user'):
        username=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select email_status from users where username=%s',[username])
        status=cursor.fetchone()[0]
        cursor.execute('select email from users where username=%s',[username])
        email=cursor.fetchone()[0]
        cursor.close()
        if status=='confirmed':
            flash('Email already confirmed')
            return redirect(url_for('home'))
        else:
            subject='Email Confirmation'
            confirm_link=url_for('confirm',token=token(email,salt1),_external=True)
            body=f"Please confirm your mail-\n\n{confirm_link}"
            sendmail(to=email,body=body,subject=subject)
            flash('Confirmation link sent check your email')
            return redirect(url_for('inactive'))
    else:
        return redirect(url_for('login'))

@app.route('/registration',methods=['GET','POST'])
def registration():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        email=request.form['email']
        cursor=mydb.cursor(buffered=True)
        try:
            cursor.execute('insert into users (username,password,email) values(%s,%s,%s)',(username,password,email))
        except mysql.connector.IntegrityError:
            flash('Username or email is already in use')
            return render_template('registration.html')
        else:
            mydb.commit()
            cursor.close()
            subject='Email confirmation'
            confirm_link=url_for('confirm',token=token(email,salt1),_external=True)
            body=f"thanks for signing-up. follow this link-\n\n{confirm_link}"
            sendmail(to=email,body=body,subject=subject)
            flash('Confirmation link sent. Check your email!')
            return render_template('registration.html')
    return render_template('registration.html')

@app.route('/confirm/<token>')
def confirm(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        email=serializer.loads(token,salt=salt1,max_age=300)
    except Exception as e:
        abort(404,'Link Expired')
    else:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select email_status from users where email=%s',[email])
        status=cursor.fetchone()[0]
        cursor.close()
        if status=='confirmed':
            flash('Email already confirmed')
            return redirect(url_for('login'))
        else:
            cursor=mydb.cursor(buffered=True)
            cursor.execute("update users set email_status='confirmed' where email=%s",[email])
            mydb.commit()
            flash('Email confirmation success')
            return redirect(url_for('login'))
        
@app.route('/forget',methods=['GET','POST'])
def forgot():
    if request.method=='POST':
        email=request.form['email']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from users where email=%s',[email])
        count=cursor.fetchone()[0]
        cursor.close()
        if count==1:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('SELECT email_status from users where email=%s',[email])
            status=cursor.fetchone()[0]
            cursor.close()
            if status!='confirmed':
                flash('Please Confirm your email first')
                return render_template('forgot.html')
            else:
                subject='Forget Password'
                confirm_link=url_for('reset',token=token(email,salt=salt2),_external=True)
                body=f"Use this link to reset your password-\n\n{confirm_link}"
                sendmail(to=email,body=body,subject=subject)
                flash('Reset link sent check your email')
                return redirect(url_for('login'))
        else:
            flash('Invalid email id')
            return render_template('forgot.html')
    return render_template('forgot.html')

@app.route('/reset/<token>',methods=['GET','POST'])
def reset(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        email=serializer.loads(token,salt=salt2,max_age=300)
    except:
        abort(404,'Link Expired')
    else:
        if request.method=='POST':
            newpassword=request.form['npassword']
            confirmpassword=request.form['cpassword']
            if newpassword==confirmpassword:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('update users set password=%s where email=%s',[newpassword,email])
                mydb.commit()
                flash('Password Reset is Successful')
                return redirect(url_for('login'))
            else:
                flash('Passwords mismatched')
                return render_template('newpass.html')
        return render_template('newpass.html')
    
@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))
if __name__=='__main__':
    app.run()   