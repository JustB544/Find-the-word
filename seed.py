from models import db, connect_db
from app import app

def seed():
    with app.app_context():
        db.drop_all()
        db.create_all()


seed()
