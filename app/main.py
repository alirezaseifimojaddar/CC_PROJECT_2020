from flask import Flask, flash, render_template, jsonify, request, Response, redirect, url_for, session, abort, render_template
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, login_manager
from werkzeug.utils import secure_filename
import requests
import os , config
import pandas as pd
import sqlite3
import datetime
import pymongo
from pymongo import MongoClient
import dns

app = Flask(__name__)
url = 'https://api.smsapi.com/sms.do'

UPLOAD_FOLDER = config.UPLOAD_FOLDER
ALLOWED_EXTENSIONS = config.ALLOWED_EXTENSIONS
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

client = pymongo.MongoClient("mongodb+srv://CCOMPUTING:bCeJoErrnGDwE4Tc@cluster0.h9msx.mongodb.net/DB?retryWrites=true&w=majority",
tls=True,tlsAllowInvalidCertificates=True)
db = client.DB
RES = db.ADMINISTRATION.find_one({}) 
USERNAME = RES["USERNAME"] # Gets user name from mongo db atlas
PASSWORD = RES["PASSWORD"] # Gets the password from mongoDB atlas


#flask login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS




app.config.update(SECRET_KEY = config.SECRET_KEY)



class User(UserMixin):
    def __init__(self, id):
        self.id = id

    def __repr__(self):
        return "%d" % (self.id)


user = User(0)


@app.route('/', methods=['GET', 'POST'])
@login_required

def home():
    #return Response("Hello world !")
    #return redirect('/mainpage')

    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            # import_database_from_excel(file_path)
            # flash('Data Imported')
            # os.remove(file_path)
            return redirect('/')

    return render_template("index.html")




@app.route('/mainpage')
def main_page():
    return render_template("index.html")


@app.route("/login", methods = ['GET','POST'])

def login():
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']        
        if password == PASSWORD and username == USERNAME:
            login_user(user)
            return redirect('/')
        else:
            return abort(401)
    else:
        return render_template("login.html")


# somewhere to logout
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('Logged out')
    return redirect('/login')


# handle login failed
@app.errorhandler(401)
def page_not_found(error):
    flash('LOGIN FAILED - TRY AGAIN')
    return redirect('/login')
    
    
# callback to reload the user object        
@login_manager.user_loader
def load_user(userid):
    return User(userid)



@app.route("/v1/process", methods = ['POST'])

def send_sms(sender, msg):
    global url
    params = {'to': f'{sender}', "message":f"{msg}"}
    headers = {"Authorization": "Bearer L40rzky1qiZTEhL0xzJ8evRhPROWjeBmimPCuExX"}
    requests.post(url, params=params, headers=headers)



def normalize_str(data):
    # we don't need it
    pass




def import_database_from_excel(filepath): 
    """ reading file with proper format and inserting into mongodb Atlas """

    df = pd.read_excel(filepath, 0)
    for index, (desc, serial, date) in df.iterrows():
        document = {"_id":index,
         "desc": desc,
         "serial": serial,
         "date": date}

        serial_collection = db.SERIALS
        document_insertion = serial_collection.insert_one(document).inserted_id


def check_serial(serial):
    """ will get a serial number and return the answer"""
    result = db.SERIALS.find_one({"serial": int(serial)})
    print(result)

    if len(result) == 4:
        return 'your serial were found !'

    return 'it was not in the db'



def process():
    # this function gets sender and message and then check whether if it's correct or not
    # should be edited 

    data = request.form
    sender = data['from']

    print(f'recieved {data["message"]} from {sender}') 

    answer = check_serial(data["message"])

    send_sms(sender, answer)

    ret = {"message": "processed"}
    return jsonify(ret), 200






if __name__ == "__main__":
    app.run(port=5000, debug=True)
    import_database_from_excel('tmp/data.xlsx')

       