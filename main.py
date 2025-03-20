import os
from flask import Flask, redirect, url_for, session, request, render_template, flash, send_file, url_for
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from pymongo import MongoClient
from werkzeug.security import check_password_hash, generate_password_hash
from pymongo.errors import DuplicateKeyError
from datetime import datetime, timezone
import io
import helpers
from slugify import slugify

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
oauth = OAuth(app)
client = MongoClient(os.getenv("MONGO_CLIENT"))
db = client['userinfo']
collection = db['users']

google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    access_token_url="https://oauth2.googleapis.com/token",
    userinfo_endpoint="https://www.googleapis.com/oauth2/v3/userinfo",
    client_kwargs={"scope": "openid email profile"},
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
)

@app.route("/")
def home():
    return render_template("main.html")

@app.route("/login",methods=["GET","POST"])
def login_page():
    session['data']={
        'name':'jarvis',
        'trait':'accurately'
    }
    if request.method=="POST":
        username=request.form.get("username")
        password=request.form.get("password")
        try:
            # Query the database to find the user
            user = collection.find_one({'username': username})
            if check_password_hash(user["hash"], password):  # Compare hashed passwords securely in practice
                # Store user info in session for a logged-in state
                session['username'] = username
                return redirect('/home')  # Redirect to the dashboard or desired page
            else:
                flash("Invalid username or password!")
                return render_template("login.html")
        except Exception as e:
            flash("An unexpected error occurred: " + str(e))
            return render_template("login.html")
    else:
        return render_template("login.html")

@app.route("/client/auth/google")
def google_login():
    redirect_uri = url_for("google_callback", _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route("/auth/google/callback")
def google_callback():
    token = google.authorize_access_token()
    user_info = google.get("https://www.googleapis.com/oauth2/v2/userinfo").json()
    session["user"] = user_info
    user = collection.find_one({'username': session["user"]['email']})
    if not user:
        collection.insert_one({'username': session["user"]['email'],'name':session["user"]['name']})
    session['username'] = session["user"]['email']
    return redirect('/home') 

@app.route("/register",methods=["GET","POST"])
def register_page():
    if request.method=="POST":
        username=request.form.get("username")
        password=request.form.get("password")
        confirm=request.form.get("confirm")
        if password != confirm:
            flash("Passwords do not match!")
            return render_template("register.html")
        hash = generate_password_hash(password)
        try:
            # Insert the user document into the collection
            collection.insert_one({'username': username, 'hash': hash})
            return redirect('/login')  # Redirect to the login page after successful registration
        except DuplicateKeyError:
            # Handle duplicate username case
            flash("Username has already been registered!")
            return render_template("register.html")
        except Exception as e:
            # Handle any other unexpected errors
            flash("An unexpected error occurred: " + str(e))
            return render_template("register.html")
    else:
        return render_template("register.html")

@app.route("/home", methods=["GET", "POST"])
def main_page():
    if "username" not in session:
        return redirect("/login")
    username=session['username']
    name=session['data']['name']
    trait=session['data']['trait']
    sav = db[slugify(session['username'])]
    if request.method == "POST":
        user_query = request.form.get('user_query')
        response = helpers.generate_response(user_query,name,trait)
        helpers.speak_text(response)
        time = datetime.now()
        sav.insert_one({'question': user_query, 'reply': response, 'time': time})
    documents = list(sav.find())
    return render_template("jip.html", documents=documents,username=username,name=name)

@app.route("/new")
def new_chat():
    sav = db[slugify(session['username'])]
    db.drop_collection(sav) 
    return redirect('/home')

@app.route('/voicesearch')
def vsearch():
    name=session['data']['name']
    trait=session['data']['trait']
    user_query=helpers.recognize_speech()
    sav = db[slugify(session['username'])]
    response = helpers.generate_response(user_query,name,trait)
    helpers.speak_text(response)
    time = datetime.now()
    sav.insert_one({'question': user_query, 'reply': response, 'time': time})
    return redirect('/home')

@app.route("/logout")
def logout():
    session.clear()
    return redirect('/') 

@app.route('/edit',methods=['GET','POST'])
def edit():
    if request.method=='POST':
        name=request.form.get("name")
        trait=request.form.get("trait")
        session['data']={
            'name':name,
            'trait':trait
        }
        return redirect('/home')
    else:
        return render_template('edit.html')


if __name__ == "__main__":
    app.run(debug=False)
