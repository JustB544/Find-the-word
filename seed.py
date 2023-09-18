from models import db, connect_db, User, Words, ApiTracker
from word_sift import extract, transform
from app import app

def seed(with_words = False):
    with app.app_context():
        db.drop_all()
        db.create_all()


        user1 = User.signup(username="testing", password="testing")
        user2 = User.signup(guest=True)
        user3 = User.signup(username="itsjustb544", password="testytesty")

        words = transform(extract("words.txt"), ",")

        db.session.add_all([Words(word=word["word"], length=word["length"]) for word in words])

        api_tracker = ApiTracker(user=user1.id, date="Sep 17 2023", api_calls=3000)

        db.session.commit()

#separate function so it isn't called
def write_words():
    with app.app_context():
        Words.__table__.drop(db.engine)
        Words.__table__.create(db.engine)

        words = transform(extract("words.txt"), ",")

        db.session.add_all([Words(word=word["word"], length=word["length"]) for word in words])
        db.session.commit()
seed()
# write_words()
