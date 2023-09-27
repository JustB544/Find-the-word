from flask import Flask, redirect, request, render_template, session, flash, g
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, User, Words, ApiTracker, Game, Round
from forms import AddUserForm, LoginForm, GameForm
from secret import secret_key, auth_key
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, text
from word_sift import test_words
from random import choices
from json import dumps, loads
from constants import *
from math import floor
import requests
import os

app = Flask(__name__)
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secret_key)
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///Capstone_1'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['FLASK_DEBUG'] = os.environ.get('FLASK_DEBUG', True)

with app.app_context():
    connect_db(app)

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
    return render_template("root.html", game="rounds" in session and session["rounds"]["rnd_num"] != -1)




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
            session["is_guest"] = True
        else:
            user = User.signup(guest=True)
            db.session.commit()
            # set user as guest so they can't make multiple guest accounts
            session["guest"] = user.id
            session["is_guest"] = True
        do_login(user, True)
        return redirect("/")


    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            session["is_guest"] = False
            return redirect("/")

        flash("Invalid credentials")

    return render_template('authentication/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    do_logout()
    if (session.get("is_guest", False)):
        flash("Successfully logged out guest")
    else:
        flash("Successfully logged out user")
    return redirect("/login")

@app.route('/convert-guest', methods=["POST", "GET"])
def convert_guest():
    if (g.user == None):
        return redirect("/login")
    if (not session.get("is_guest", False)):
        return redirect("/")
    
    form = AddUserForm()

    if form.validate_on_submit():
        try:
            User.signup(username=form.username.data,
                        password=form.password.data,
                        user=g.user)
        except IntegrityError:
            flash("Username already taken")
            return render_template("authentication/convert_guest.html", form=form)
        print(g.user.username)
        session["is_guest"] = False
        del session["guest"]
        return redirect("/")
    

    return render_template("authentication/convert_guest.html", form=form)


###### Endpoints and functions for API calls and 

API_LIMIT = 2500
USER_API_LIMIT = 1000


def create_api_tracker():
    api_tracker = ApiTracker(user_id=g.user.id)
    db.session.add(api_tracker)
    db.session.commit()
    return api_tracker.id

def check_api_tracker(api_tracker: ApiTracker):
    if (api_tracker == None):
        return False
    sum = ApiTracker.query.with_entities(func.sum(ApiTracker.api_calls).label("sum")).filter_by(date=TZ_NOW())[0].sum
    if (session.get("brick", False)):
        if (api_tracker.date == TZ_NOW() or (sum != None and sum >= API_LIMIT)):
            return "brick"
        session["brick"] = False
    elif (api_tracker.date != TZ_NOW()):
        # Reset api_calls and change the date
        # print(TZ_NOW(), api_tracker.date)
        api_tracker.api_calls = 0
        api_tracker.date = TZ_NOW()
        db.session.commit()
    elif (sum >= API_LIMIT or api_tracker.api_calls >= USER_API_LIMIT):
        session["brick"] = True
        return "brick"
    return True

def call_api(word: str, dest: str):
    """Calls WordsApi and tracks API usage"""
    api_tracker = ApiTracker.query.get(session.get("api_tracker", None))
    check = check_api_tracker(api_tracker)
    if (check == False):
        session["api_tracker"] = create_api_tracker()
        api_tracker = ApiTracker.query.get(session["api_tracker"])
    elif (check == "brick"):
        return {"brick": True}
    
    try:
        api_tracker.api_calls += 1
        db.session.commit()
        response = requests.get(f"{URL_BASE}/{word}/{dest}", headers=HEADERS)
        return response.json()
        # return dumps({"success": True})
    except Exception as e:
        print(e)
        return {"error": True}
    
def get_words(count: int, game_dest=None):
    """Gives count number of unique random words from the database"""
    words = []
    if (game_dest == None):
        num = Words.query.with_entities(func.count(Words.word).label("count")).all()[0].count
        for x in choices(range(0,num), k=count):
            words.append(Words.query.get(x+1).word)
    else:
        words = Words.query.filter(getattr(Words, game_dest) == True).all()
        words = [word.word for word in choices(words, k=count)]
    return words

def create_data(game_dest):
    words = get_words(4, game_dest=game_dest[:-1])
    answer = choices(words)[0]


    response = call_api(answer, game_dest)
    if (response.get("word", None) == None):
        print(response)
        return
    if (len(response[game_dest]) == 0):
        word = Words.query.filter_by(word=answer).one()
        setattr(word, game_dest, False)
        db.session.commit()
        print(word)
        return create_data(game_dest)
    output = choices(response[game_dest])[0]
    if (game_dest == "examples"):
        output = output.replace(answer, "_____")
        # makes it harder to deduce simply based off grammar
        output = output.replace(" a _____", " a(n) _____", count=1)
        output = output.replace(" an _____", " a(n) _____", count=1)
        output = output.capitalize().replace("A _____", "a(n) _____", count=1)
        output = output.capitalize().replace("An _____", "a(n) _____", count=1)
        return {"output": output, "words": words, "answer": answer}
    elif (game_dest == "definitions"):
        return {"output": output["definition"], "words": words, "answer": answer}
    elif (game_dest == "synonyms" or "antonyms"):
        print(words)
        return {"output": output, "words": words, "answer": answer}
    print(game_dest)

@app.route('/api/<word>/<dest>')
def api_route(word, dest):
    """Uses call_api to communicate with WordsApi"""
    if (g.user == None):
        return redirect("/login")
    return call_api(word, dest)

###### Game routes

@app.route('/game/<game_type>/new')
def new_game(game_type):
    """Starts a game of type game_type"""
    if (g.user == None):
        return redirect("/login")

    if ("rounds" in session and session["rounds"]["rnd_num"] != -1):
        # mostly for debug purposes
        game = Game.query.get(session["rounds"]["game"])
        if (game != None):
            flash("Invalid call: you can only play one game at a time")
            return redirect("/")
        else:
            del session["rounds"]

    game = Game(game_type=game_type, user_id=g.user.id)
    db.session.add(game)
    db.session.commit()

    round = Round(game_id=game.id)
    db.session.add(round)
    db.session.commit()

    if (not "rounds" in session or session["rounds"]["rnd_num"] == -1):
        session["rounds"] = {"game": game.id, "rnd_num": 1, "cur_round_id": round.id}
    return redirect("/game")

@app.route('/game', methods=["POST", "GET"])
def continue_game():
    """Continues game"""
    round = Round.query.get(session["rounds"]["cur_round_id"])
    if (g.user != round.game.user):
        flash("Invalid Access")
        return redirect("/")

    form = GameForm()

    if form.validate_on_submit():
        round.score = form.guess.data == round.answer
        round.guess = form.guess.data
        round.completed = True
        db.session.commit()
        if (session["rounds"]["rnd_num"] >= round.game.rounds):
            session.modified = True
            return render_template("post_round.html", data={"msg": "Correct!"} if (round.score) else {"msg": "Incorrect", "answer": round.answer}, end=True)
        session["rounds"]["rnd_num"] += 1
        new_round = Round(game_id=round.game_id)
        db.session.add(new_round)
        db.session.commit()
        session["rounds"]["cur_round_id"] = new_round.id
        session.modified = True
        return render_template("post_round.html", data={"msg": "Correct!"} if (round.score) else {"msg": "Incorrect", "answer": round.answer}, end=False)
    elif (not f"words_{round.id}" in session["rounds"]):
            data = create_data(round.game.game_type + "s")
            round.words = ', '.join(data["words"])
            session["rounds"][f"words_{round.id}"] = data["words"]
            round.answer = data["answer"]
            round.data = data["output"]
            db.session.commit()
            session.modified = True
    return render_template("game.html", form=form, words=session["rounds"][f"words_{round.id}"], data=round.data, rnd_num=session["rounds"]["rnd_num"], game_type=round.game.game_type)

@app.route('/game/finish')
def finish_game():
    if (not "rounds" in session):
        flash("Invalid Access")
        return redirect("/")

    game = Game.query.get(session["rounds"]["game"])
    if (game == None or g.user != game.user):
        flash("Invalid Access")
        return redirect("/")
    elif (game.completed == True):
        return render_template("finish_game.html", msg=session["rounds"]["msg"], score=session["rounds"]["score"], gt=game.game_type)

    score = len(Round.query.filter_by(game_id=game.id, score=True).all())
    game.score = score
    game.completed = True
    db.session.commit()
    if (score == 0):
        msg = "Better luck next time"
    elif (score <= floor(float(game.rounds)/4)):
        msg = "Play again to get a better score!"
    elif (score == game.rounds):
        msg = "Absolutely amazing!"
    elif (score > floor(3*float(game.rounds)/4)):
        msg = "Awesome score!"
    elif (score > floor(float(game.rounds)/2)):
        msg = "Great job!"
    elif (score > floor(float(game.rounds)/4)):
        msg = "Practice makes perfect!"

    session["rounds"] = {"game": game.id, "rnd_num": -1, "cur_round_id": -1, "msg": msg, "score": score}
    
    return render_template("finish_game.html", msg=msg, score=score, gt=game.game_type)

@app.route('/game/end')
def end_game():
    if (not "rounds" in session or session["rounds"]["rnd_num"] == -1):
        flash("Invalid Access")
        return redirect("/")
    game = Game.query.filter_by(id=session["rounds"]["game"]).delete()
    db.session.commit()
    session["rounds"] = {"game": -1, "rnd_num": -1, "cur_round_id": -1}
    return redirect("/")

@app.route('/statistics')
def statistics():
    if (g.user == None):
        return redirect("/login")
    
    games = Game.query.order_by(Game.id.desc()).filter_by(user_id=g.user.id)
    average = Game.query.filter_by(user_id=g.user.id).with_entities(func.avg(Game.score).label("avg")).all()[0].avg

    return render_template("statistics.html", statistics={"games": games, "average": (round(average, 2) if average != None else None)}, games=True)

@app.route('/statistics/<int:game_id>')
def statistics_round(game_id):
    if (g.user == None):
        return redirect("/login")
    
    game = Game.query.get(game_id)
    rounds = Round.query.filter_by(game_id=game_id)

    return render_template("statistics.html", statistics={"rounds": rounds, "game": game}, games=False)

# @app.route('/game/<int:round_id>/hint')
# def hint(round_id):
#     return dumps({})