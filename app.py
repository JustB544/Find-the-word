from flask import Flask, redirect, request, render_template, session, flash, g
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, User, Words, ApiTracker
from forms import AddUserForm, LoginForm
from secret import secret_key, auth_key
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from word_sift import test_words
from random import choices
from json import dumps, loads
from datetime import timedelta, timezone, datetime
from constants import *
import requests
import os

app = Flask(__name__)
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secret_key)
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///Capstone_1'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False

with app.app_context():
    connect_db(app)
    db.create_all()

debug = DebugToolbarExtension(app)
CURR_USER_KEY = "curr_user"

######## Non-Route functions

@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if (CURR_USER_KEY in session):
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req


def do_login(user: User = None, restore_guest: bool = False):
    """Log in user, or check for previous guest"""
    if (restore_guest):
        session[CURR_USER_KEY] = session["guest"]
        return
    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if (CURR_USER_KEY in session):
        del session[CURR_USER_KEY]

####### Routes

@app.route('/')
def root():
    if (g.user == None):
        return redirect("/login")
    return render_template("root.html")




@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.
    """

    if (g.user):
        return redirect("/")

    form = AddUserForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken")
            return render_template('authentication/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('authentication/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    if (g.user):
        return redirect("/")
    if (request.form.get("guest", None)):
        if ("guest" in session):
            user = User.query.get(session["guest"])
            # mostly for debugging purposes
            if (user == None):
                user = User.signup(guest=True)
                db.session.commit()
                # set user as guest so they can't make multiple guest accounts
                session["guest"] = user.id
        else:
            user = User.signup(guest=True)
            db.session.commit()
            # set user as guest so they can't make multiple guest accounts
            session["guest"] = user.id
        do_login(user, True)
        return redirect("/")


    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            return redirect("/")

        flash("Invalid credentials")

    return render_template('authentication/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    do_logout()
    if ("guest" in session):
        flash("Successfully logged out guest")
    else:
        flash("Successfully logged out user")
    return redirect("/login")


###### API routes and functions for Axios

API_LIMIT = 2500
USER_API_LIMIT = 1000


def create_api_tracker():
    api_tracker = ApiTracker(user=g.user.id)
    db.session.add(api_tracker)
    db.session.commit()
    return api_tracker.id

def check_api_tracker(api_tracker: ApiTracker):
    if (api_tracker == None):
        return False
    if (session.get("brick", False)):
        if (api_tracker.date == TZ_NOW()):
            return "brick"
        session["brick"] = False
    elif (api_tracker.date != TZ_NOW()):
        # Reset api_calls and change the date
        print(TZ_NOW(), api_tracker.date)
        api_tracker.api_calls = 0
        api_tracker.date = TZ_NOW()
        db.session.commit()
    elif (ApiTracker.query.with_entities(func.sum(ApiTracker.api_calls).label("sum")).filter_by(date=TZ_NOW())[0].sum >= API_LIMIT or api_tracker.api_calls >= USER_API_LIMIT):
        session["brick"] = True
        return "brick"
    return True


@app.route('/api/<word>/<dest>')
def api_route(word, dest):
    if (g.user == None):
        return redirect("/login")
    api_tracker = ApiTracker.query.get(session.get("api_tracker", None))
    check = check_api_tracker(api_tracker)
    if (check == False):
        session["api_tracker"] = create_api_tracker()
        api_tracker = ApiTracker.query.get(session["api_tracker"])
    elif (check == "brick"):
        return dumps({"brick": True})
    
    try:
        api_tracker.api_calls += 1
        db.session.commit()
        response = requests.get(f"{URL_BASE}/{word}/{dest}", headers=HEADERS)
        return response.json()
        # return dumps({"success": True})
    except Exception as e:
        print(e)
        return dumps({"error": True})


@app.route('/get_words/<int:count>')
def get_words(count: int):
    words = []
    num = Words.query.with_entities(func.count(Words.word).label("count")).all()[0].count
    for x in choices(range(0,num), k=count):
        words.append(Words.query.get(x+1).word)

    return dumps(words)