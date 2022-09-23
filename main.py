from flask import Flask, session, redirect, url_for, render_template, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import hashlib
import difflib
from helper_funcs import User_Obj, similarity

app = Flask(__name__)
db = SQLAlchemy(app)
app.config['SECRET_KEY'] = 'the random string' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15))
    password = db.Column(db.String)
    public = db.Column(db.Boolean)

    def __init__(self, username, password, public):
        self.username = username
        password = bytes(password,'utf-8')
        password = hashlib.md5(password).hexdigest()
        self.password = str(password)
        self.public = public

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poster_id = db.Column(db.Integer)
    poster_name = db.Column(db.String)
    content = db.Column(db.String)
    time = db.Column(db.String)
    date = db.Column(db.String)
    datetime = db.Column(db.String)

    def __init__(self, poster_id, poster_name, content):
        self.poster_id = poster_id
        self.poster_name = poster_name
        self.content = content
        self.datetime = datetime.now()
        self.time = self.datetime.strftime("%I:%M %p")
        self.date = self.datetime.strftime("%b %d %Y")

class Follows(db.Model):
    follow_id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer)
    following_id = db.Column(db.Integer)

    def __init__(self, follower_id, following_id):
        self.follower_id = follower_id
        self.following_id = following_id

class Requests(db.Model):
    request_id = db.Column(db.Integer, primary_key=True)
    requested_id = db.Column(db.Integer)
    requester_id = db.Column(db.Integer)

    def __init__(self, requested_id, requester_id):
        self.requested_id = requested_id
        self.requester_id = requester_id


def authenticate_passwords(unhashed, hashed):
    return hashlib.md5(bytes(unhashed,'utf-8')).hexdigest() == hashed
        
@app.route("/", methods=["GET","POST"])
def home():
    if 'user' not in session:
        return redirect(url_for("login"))
    else:
        user = User.query.filter_by(id=session['user']).first()
        if request.method == "POST":
            content = request.form['text']
            if content:
                new_post = Post(session['user'], user.username, content)
                db.session.add(new_post)
                db.session.commit()
        posts = Post.query.all()
        people_we_follow = Follows.query.filter_by(follower_id=session['user']).all()
        posts_to_show = []
        for post in posts:
            if post.poster_id == session['user']:
                posts_to_show.append(post)
            for person in people_we_follow:
                if post.poster_id == person.following_id:
                    posts_to_show.append(post)
        posts_to_show = posts_to_show[::-1]
        return render_template("home.html",user=user,posts=posts_to_show,id=session['user'],friends=True)

@app.route("/discover", methods=["GET","POST"])
def discover():
    if 'user' not in session:
        return redirect(url_for("login"))
    else:
        user = User.query.filter_by(id=session['user']).first()
        if request.method == "POST":
            content = request.form['text']
            if content:
                new_post = Post(session['user'], user.username, content)
                db.session.add(new_post)
                db.session.commit()
        posts = Post.query.all()
        posts_to_show = []
        for post in posts:
            poster = User.query.filter_by(id=post.poster_id).first()
            if poster.public == True or post.poster_id == session['user']:
                posts_to_show.append(post)
        posts_to_show = posts_to_show[::-1]
        return render_template("home.html",user=user,posts=posts_to_show,id=session['user'],friends=False)

@app.route("/login", methods=["GET","POST"])
def login():
    error = ""
    if request.method == "POST":
        username = request.form['username'].lower()
        password = request.form['password']
        if username and password:
            print("valid")
            right_user = User.query.filter_by(username=username).first()
            if right_user:
                print("user found")
                print("password is " + right_user.password)
                if authenticate_passwords(password, right_user.password):
                    session['user'] = right_user.id
                    return redirect(url_for("home"))
                else:
                    error = "Incorrect username or password"
            else:
                error = "Incorrect username or password"
    return render_template("login.html",error=error)

@app.route("/join", methods=["GET","POST"])
def join():
    error = ""
    banned_chars = "~`!@#$%^&*()-+=[]{[}]|\\:;\"\',<.>/?"
    if request.method == "POST":
        username = request.form['username'].lower()
        for char in username:
            if char in banned_chars:
                error = f"{char} cannot be in your username"
                break
                username = None
        password = request.form['password']
        privacy = request.form['button-value']
        if username and password and privacy:
            is_user = User.query.filter_by(username=username).first()
            if is_user is not None:
                error = "Username Taken"
            elif len(username) > 20:
                error = "Usernames can only be 20 characters"
            else:
                if privacy == "public":
                    privacy = True
                    print("public")
                else:
                    privacy = False
                    print("private")
                new_user = User(username,password,privacy)
                db.session.add(new_user)
                db.session.commit()
                session['user'] = new_user.id
                return redirect(url_for("home"))
        else:
            if not error:
                error = "All fields must be filled"
    return render_template("join.html",error=error)

@app.route("/logout")
def logout():
    for key in list(session.keys()):
        session.pop(key)
    return redirect(url_for("login"))

@app.route("/user/<int:id>", methods=["GET","POST"])
def user_profile(id):
    posts = []
    following = False # following
    requested = False # requested
    public_acct = False
    own_acct = False
    are_we_private = False
    if 'user' not in session:
        return redirect(url_for("login"))
    else:
        own_acct = (id == session['user'])
        are_we_private = own_acct and not User.query.filter_by(id=id).first().public
        if request.method == "POST" and not own_acct:
            if request.form["action"] == "follow":
                acct = User.query.filter_by(id=id).first()
                if acct.public:
                    new_follow = Follows(follower_id=session['user'],following_id=id)
                    db.session.add(new_follow)
                    db.session.commit()
                else:
                    new_request = Requests(requested_id=id,requester_id=session['user'])
                    db.session.add(new_request)
                    db.session.commit()
            elif request.form["action"] == "unrequest":
                requests = Requests.query.filter_by(requested_id=id).all()
                correct = None
                for req in requests:
                    if req.requester_id == session['user']:
                        db.session.delete(req)
                        db.session.commit()
            elif request.form['action'] == "unfollow":
                follows = Follows.query.filter_by(following_id=id).all()
                correct = None
                for f in follows:
                    if f.follower_id == session['user']:
                        db.session.delete(f)
                        db.session.commit()

        username = User.query.filter_by(id=id).first()
        
        follow_check = Follows.query.filter_by(following_id=id).all()
        for follow in follow_check:
            if follow.follower_id == session['user']:
                following = True
        if username.public == False:
            request_check = Requests.query.filter_by(requested_id=id).all()
            for req in request_check:
                if req.requester_id == session['user']:
                    requested = True
        else:
            public_acct = True
        username = username.username
        if own_acct:
            if request.method == "POST":
                content = request.form['text']
                if content:
                    user = User.query.filter_by(id=session['user']).first()
                    new_post = Post(session['user'], user.username, content)
                    db.session.add(new_post)
                    db.session.commit()
            posts = Post.query.filter_by(poster_id=id).all()
            following = len(Follows.query.filter_by(follower_id=id).all())
            followers = len(Follows.query.filter_by(following_id=id).all())
            requests = len(Requests.query.filter_by(requested_id=id).all())
            return render_template("own-profile.html",username=username,posts=posts,following=following,followers=followers,id=id,private=are_we_private,requests=requests)
        elif following:
            posts = Post.query.filter_by(poster_id=id).all()
            following = len(Follows.query.filter_by(follower_id=id).all())
            followers = len(Follows.query.filter_by(following_id=id).all())
            return render_template("profile.html",username=username,posts=posts,following=following,followers=followers,id=id,action="unfollow",own_id=session['user'])
        elif requested:
            following = len(Follows.query.filter_by(follower_id=id).all())
            followers = len(Follows.query.filter_by(following_id=id).all())
            return render_template("private-account.html",username=username,posts=posts,following=following,followers=followers,id=id,action="unrequest",own_id=session['user'])
        elif public_acct:
            posts = Post.query.filter_by(poster_id=id).all()
            following = len(Follows.query.filter_by(follower_id=id).all())
            followers = len(Follows.query.filter_by(following_id=id).all())
            return render_template("profile.html",username=username,posts=posts,following=following,followers=followers,id=id,action="follow",own_id=session['user'])
        else:
            following = len(Follows.query.filter_by(follower_id=id).all())
            followers = len(Follows.query.filter_by(following_id=id).all())
            return render_template("private-account.html",username=username,following=following,followers=followers,id=id,action="follow",own_id=session['user'])


@app.route("/user/<int:id>/following")
def show_following(id):
    following = False
    is_self = False
    if 'user' not in session:
        return redirect(url_for("login"))
    if session['user'] == id:
        is_self = True
    else:
        followers = Follows.query.filter_by(following_id=id).all()
        for follower in followers:
            if session['user'] == follower.follower_id:
                following = True
    if is_self or following:
        follows = Follows.query.filter_by(follower_id=id).all()
        following = []
        for follow in follows:
            user = User.query.filter_by(id=follow.following_id).first()
            following.append(user)
        username = User.query.filter_by(id=id).first().username
        return render_template("following.html",username=username,following=following,followings=len(following),id=id)

@app.route("/user/<int:id>/followers")
def show_followers(id):
    following = False
    is_self = False
    is_public = False
    if 'user' not in session:
        return redirect(url_for("login"))
    if session['user'] == id:
        is_self = True
    else:
        followers = Follows.query.filter_by(following_id=id).all()
        for follower in followers:
            if session['user'] == follower.follower_id:
                following = True
        if User.query.filter_by(id=id).first().public:
            is_public = True
    if is_self or following or is_public:
        follows = Follows.query.filter_by(following_id=id).all()
        followers = []
        for follow in follows:
            user = User.query.filter_by(id=follow.follower_id).first()
            print(user.username)
            followers.append(user)
            print(follow.follower_id)
        username = User.query.filter_by(id=id).first().username
        return render_template("followers.html",username=username,followers=followers,follower_count=len(followers),id=id)

@app.route("/user/<int:id>/requests", methods=["GET","POST"])
def show_requests(id):
    if "user" not in session:
        return redirect(url_for("log in"))
    if session['user'] != id:
        return redirect(url_for("discover"))
    else:
        db_requests = Requests.query.filter_by(requested_id=id).all()
        if request.method == "POST":
            requester = int(request.form["requester"])
            if request.form["choice"] == "accept":
                new_follow = Follows(requester,id)
                db.session.add(new_follow)
                db.session.commit()
            for req in db_requests:
                if req.requester_id == requester:
                    db.session.delete(req)
                    db.session.commit()
        username = User.query.filter_by(id=id).first().username
        requests = []
        db_requests = Requests.query.filter_by(requested_id=id).all()
        for req in db_requests:
            user = User.query.filter_by(id=req.requester_id).first()
            requests.append(user)
    return render_template("requests.html",requests=requests,amt=len(requests),username=username,id=id)

@app.route("/search", methods=["GET","POST"])
def search():
    res = []
    if "user" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        if request.form['query'] == "":
            users = User.query.all()
            user_objs = []
            for user in users:
                followers = len(Follows.query.filter_by(following_id=user.id).all())
                user_objs.append(User_Obj(user.id,user.username,followers))
            user_objs.sort(key = lambda x: x.followers)
            res = user_objs[::-1]
        else:
            query = request.form['query']
            users = User.query.all()
            user_objs = []
            for user in users:
                if similarity(query,user.username) > 0:
                    followers = len(Follows.query.filter_by(following_id=user.id).all())
                    user_objs.append(User_Obj(user.id,user.username,followers))
            user_objs.sort(key = lambda x: similarity(query,x.username))
            res = user_objs[::-1]
    return render_template("search.html",id=session['user'],res=res)




if __name__ == "__main__":
    db.create_all()
    app.run()
















