"""User and ApiTracker model tests"""

import os
from unittest import TestCase
from flask import session, g
from sqlalchemy import func
from models import db, User, Round, Game, ApiTracker, Words
from constants import *
from unittest.mock import patch

os.environ['DATABASE_URL'] = "postgresql:///Capstone_1_testing"

from app import app, CURR_USER_KEY, check_api_tracker

with app.app_context():
    db.create_all()

from seed import seed

class ModelTestCase(TestCase):
    """Tests models and functions that manipulate them"""

    def setUp(self):
        seed()
    
    def test_user_setup(self):
        with app.app_context():
            with app.test_client() as c:
                user = User.signup(username="test", password="test")

                db.session.add(user)
                db.session.commit()

                _user = User.authenticate("test", "test")

                self.assertNotEqual("test", user.password)
                self.assertEqual(user.id, _user.id)
    
    def test_guest_user(self):
        with app.app_context():
            with app.test_client() as c:
                user = User.signup(guest=True)

                self.assertEqual("guest4", user.username)

    def test_api_tracker(self):
        with app.app_context():
            with patch("app.session", dict()) as session:
                session[CURR_USER_KEY] = 1
                api_tracker1 = ApiTracker(user_id=1, date=TZ_NOW(), api_calls=3000)
                api_tracker2 = ApiTracker(user_id=1, date="Not today", api_calls=3000)
                db.session.add_all([api_tracker1, api_tracker2])
                db.session.commit()
                self.assertEqual("brick", check_api_tracker(api_tracker1))
                self.assertEqual("brick", check_api_tracker(api_tracker2))
                api_tracker1 = ApiTracker.query.filter_by(id=1).delete()
                db.session.commit()
                self.assertEqual(True, check_api_tracker(api_tracker2))




