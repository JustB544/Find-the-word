"""Authentication routes tests"""

import os
from unittest import TestCase
from flask import session, g
from sqlalchemy import func
from models import db, User, Round, Game, ApiTracker, Words
from constants import *
from unittest.mock import patch

os.environ['DATABASE_URL'] = "postgresql:///Capstone_1_testing"

from app import app, CURR_USER_KEY

with app.app_context():
    db.create_all()

from seed import seed

app.config['WTF_CSRF_ENABLED'] = False
app.config['TESTING'] = True

class AuthenticationTestCase(TestCase):
    """Tests all authentication routes"""

    def setUp(self):
        seed()
        self.client = app.test_client()
    def tearDown(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = None
    def login_user(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 1
    
    def test_user_login(self):
        with app.app_context():
            with self.client as c:
                resp = c.get("/login")
                html = resp.get_data(as_text=True)
                self.assertIn("Please Login", html)

                resp = c.get("/")
                self.assertEqual(resp.status_code, 302)

                resp = c.post("/login", data={"username": "testing_user", "password": "testing"})
                self.assertEqual(resp.status_code, 302)

                resp = c.get("/login")
                self.assertEqual(resp.status_code, 302)

                resp = c.get("/")
                html = resp.get_data(as_text=True)
                self.assertIn("Select a game type to start a new game!", html)

                resp = c.get("/logout")
                self.assertEqual(resp.status_code, 302)

                resp = c.get("/login")
                html = resp.get_data(as_text=True)
                self.assertIn("Successfully logged out user", html)

    def test_guest_login(self):
        with app.app_context():
            with self.client as c:
                resp = c.post("/login", data={"guest": True})
                self.assertEqual(resp.status_code, 302)

                resp = c.get("/")
                html = resp.get_data(as_text=True)
                self.assertIn("Convert account", html)

                with c.session_transaction() as sess:
                    self.assertEqual(sess[CURR_USER_KEY], 4)

                resp = c.get("/logout")
                self.assertEqual(resp.status_code, 302)

                resp = c.get("/login")
                html = resp.get_data(as_text=True)
                self.assertIn("Successfully logged out guest", html)

                resp = c.post("/login", data={"guest": True})
                self.assertEqual(resp.status_code, 302)

                with c.session_transaction() as sess:
                    self.assertEqual(sess[CURR_USER_KEY], 4)

                resp = c.get("/convert-guest")
                html = resp.get_data(as_text=True)
                self.assertIn("Set a username and password", html)

                resp = c.post("/convert-guest", data={"username": "guest_user", "password": "testing"})
                self.assertEqual(resp.status_code, 302)

                resp = c.get("/")
                html = resp.get_data(as_text=True)
                self.assertIn("Select a game type to start a new game!", html)

                resp = c.get("/logout")
                self.assertEqual(resp.status_code, 302)

                resp = c.post("/login", data={"username": "guest_user", "password": "testing"})
                self.assertEqual(resp.status_code, 302)

                with c.session_transaction() as sess:
                    self.assertEqual(sess[CURR_USER_KEY], 4)

    def test_user_signup(self):
        with app.app_context():
            with self.client as c:
                resp = c.get("/signup")
                html = resp.get_data(as_text=True)
                self.assertIn("Sign up", html)

                resp = c.get("/")
                self.assertEqual(resp.status_code, 302)

                resp = c.post("/signup", data={"username": "signup_user", "password": "testing"})
                self.assertEqual(resp.status_code, 302)

                resp = c.get("/signup")
                self.assertEqual(resp.status_code, 302)

                resp = c.get("/")
                html = resp.get_data(as_text=True)
                self.assertIn("Select a game type to start a new game!", html)

                resp = c.get("/logout")
                self.assertEqual(resp.status_code, 302)

                resp = c.post("/login", data={"username": "signup_user", "password": "testing"})
                self.assertEqual(resp.status_code, 302)

                resp = c.get("/")
                html = resp.get_data(as_text=True)
                self.assertIn("Select a game type to start a new game!", html)