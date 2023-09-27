"""Game routes tests"""

import os
from unittest import TestCase
import flask
from sqlalchemy import func
from models import db, User, Round, Game, ApiTracker, Words
from constants import *
from unittest.mock import patch

os.environ['DATABASE_URL'] = "postgresql:///Capstone_1_testing"

from app import app, CURR_USER_KEY

with app.app_context():
    db.create_all()

from seed import seed, write_words

app.config['WTF_CSRF_ENABLED'] = False
app.config['TESTING'] = True

class GameTestCase(TestCase):
    """Tests models and functions that manipulate them"""

    @classmethod
    def setUpClass(cls):
        write_words()
    def setUp(self):
        seed()
        self.client = app.test_client()
    def tearDown(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = None

    def test_game_start(self):
        with app.app_context():
            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = 1
                resp = c.get("/game/example/new")
                self.assertEqual(resp.status_code, 302)
                game = Game.query.get(1)
                self.assertEqual(game.completed, False)
                self.assertEqual(game.user_id, 1)
                self.assertEqual(game.game_type, "example")
                round = Round.query.get(1)
                self.assertEqual(round.completed, False)
                self.assertEqual(round.game_id, 1)

                resp = c.get("/game")
                html = resp.get_data(as_text=True)
                with c.session_transaction() as sess:
                    words = sess["rounds"]["words_1"]
                for word in words:
                    self.assertIn(word, html)
    
    def test_game(self):
        with app.app_context():
            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = 1
                resp = c.get("/game/example/new")
                self.assertEqual(resp.status_code, 302)
                game = Game.query.get(1)
                for x in range(game.rounds-1):
                    resp = c.get("/game")
                    self.assertEqual(resp.status_code, 200)
                    with c.session_transaction() as sess:
                        round = Round.query.get(sess["rounds"]["cur_round_id"])
                    resp = c.post("/game", data={"guess": round.answer})
                    html = resp.get_data(as_text=True)
                    self.assertEqual(resp.status_code, 200)
                    self.assertIn("Correct!", html)
                
                resp = c.get("/game")
                self.assertEqual(resp.status_code, 200)
                with c.session_transaction() as sess:
                    round = Round.query.get(sess["rounds"]["cur_round_id"])
                    words = sess["rounds"][f"words_{round.id}"]
                resp = c.post("/game", data={"guess": words[0] if round.answer != words[0] else words[1]})
                html = resp.get_data(as_text=True)
                self.assertEqual(resp.status_code, 200)
                self.assertIn("Incorrect", html)

                resp = c.get("/game/finish")
                html = resp.get_data(as_text=True)
                self.assertEqual(resp.status_code, 200)
                self.assertIn("Your score was: 9", html)

