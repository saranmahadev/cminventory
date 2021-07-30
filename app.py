from flask import Flask,request,session,send_from_directory
from flask.templating import render_template
from werkzeug.utils import redirect,secure_filename
from werkzeug.security import generate_password_hash,check_password_hash
from flask_wtf.csrf import CSRFProtect
from db import Db
import re
import datetime
import uuid
import json

app = Flask(__name__,template_folder="templates",static_folder="static")

app.config.from_file("credentials.json",json.load)

# CSRF Protection
CSRFProtect(app)


#########################################################################################
# @note - Management Area 

@app.route('/management/')
def management():
    if session["authorized"] == 'management':
        return render_template('management.html')
    else:
        return redirect('/')

@app.route('/management/<option>')
def management_option(option):
    if session["authorized"] == "management":                               
        if option == "products":
            with Db("users") as database:
                all = database.all()
            return render_template('products.html',all = all)             
        
        elif option == "users":                        
            with Db("users") as userdb:
                data = list(userdb.all())                
            return render_template('users.html',data = data,utype="user")
        
        elif option == "action":            
            if request.args.get("to") == "activate":
                auth = 1
            elif request.args.get("to") == "deactivate":            
                auth = 0            
            print(auth)
            with Db("users") as database:
                database.update({'email':request.args.get('mail')},{
                    '$set':{
                        'auth':auth
                    }
                })                      
            return redirect('/management/users')  
                  
        elif option == "delete":
            with Db("users") as database:
                database.delete({'email':request.args.get('mail')})
            return redirect('/management/users')
        else:
            return render_template('404.html')
    else:
        return redirect('/')
#########################################################################################
# @note - User Area

@app.route('/user/')
def user():
    if session["authorized"] == 'user':
        return render_template('user.html')
    else:
        return redirect('/')

@app.route('/user/products/')
def user_products():
    if session["authorized"] == 'user':
        with Db("users") as database:
            data = database.find({"email":session['email']})
        return render_template('products.html',products = list(data)[0]['products'])
    else:
        return redirect('/')

#########################################################################################
# @note - Product Area

@app.route('/product/<action>/', methods = ['POST'])
def product(action):
    if action == 'add':
        with Db("users") as database:
            database.update({"email":request.form["email"]},{
                "$push":{
                    "products": {
                        "id" : uuid.uuid4().hex,
                        "product" : request.form["product"],
                        "category" : request.form["category"],
                        "added-on" : datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                }
            })
        return redirect('/user/products/')
    
    elif action == 'delete':      
        with Db("users") as database:
            database.update({"email":request.json["email"]},{
                "$pull":{
                    "products": {
                        "id" : request.json["id"]
                    }
                }
            })
        return {"status" : "success"}


#########################################################################################
# @note - Homepage

@app.route('/')
def hello():
    try:    
        if session["authorized"] == None:
            if request.args.get("notify") == "user_success_signup":
                notify = "show"
            else:
                notify = None

            return render_template("index.html",notify=notify)
        else:
            return redirect('/{path}/'.format(path = session["authorized"]))            
    except:
        session["authorized"] = None
        return redirect('/')

#########################################################################################
# @note - Login

@app.route('/login', methods=['GET','POST'])
def login():
    if session["authorized"] == None:
        if request.method == 'GET':
            return render_template("login.html")
        elif request.method == 'POST':
            if 'key' in request.form:
                with open('credentials.json') as f:
                    data = json.load(f)
                if request.form['key'] == data["managementKey"]:                        
                    session['authorized'] = "management"
                    return redirect('/management/')
                else:
                    return redirect('/login')
            elif 'userid' in request.form:
                print(request.form)
                with Db("users") as database:
                    data = database.find({'email':request.form['userid']})                                        
                    try:
                        if check_password_hash('pbkdf2:sha256:'+data[0]['password'],request.form['userpwd']):
                            session['authorized'] = "user"    
                            session["email"] = request.form['userid']
                            return redirect('/user/')
                        else:
                            return redirect('/login?notify=wrong_password')
                    except:
                        return redirect('/login?notify=user_does_not_exist')                        
    else:
        return redirect('/{path}/'.format(path = session["authorized"]))

# @note - Signup
@app.route('/signup',methods=['GET','POST'])
def signup():
    if session["authorized"] == None:
        if request.method == 'GET':
            return render_template("signup.html")
        elif request.method == 'POST':
            if re.search('^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$',request.form["email"]):            
                with Db("users") as database:
                    database.insert({
                        "name" : secure_filename(request.form["name"]),
                        "email" : request.form["email"],
                        "password" : generate_password_hash(request.form["password"]).split(':')[-1],                                                          
                        "auth" : 0,
                        "products" : []                    
                    })      
                return redirect('/?notify=user_success_signup')
            else:
                return redirect('/signup?notify=wrong_email')            
    else:
        return redirect('/{path}/'.format(path = session["authorized"]))

# @note - Logout
@app.route('/logout')
def logout():
    session["authorized"] = None
    return redirect('/')

#########################################################################################
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.static_folder,'favicon.png')

if __name__ == '__main__':
    # Driver Code
    app.run(debug=True)