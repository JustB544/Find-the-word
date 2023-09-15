from unittest import TestCase
from app import app
from flask import session
from seed import seed
# from models import 

class FlaskTests(TestCase):
    """tests"""
    def setUp(self):
        seed()
    
    

        