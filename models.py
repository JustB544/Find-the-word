from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from random import choices
from string import ascii_letters
from constants import TZ_NOW
bcrypt = Bcrypt()

db = SQLAlchemy()


def connect_db(app):
    """Connect to database."""

    db.app = app
    db.init_app(app)

class User(db.Model):
    """User in the system."""

    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    username = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    password = db.Column(
        db.Text,
        nullable=False,
    )
    @classmethod
    def signup(cls, username=None, password=None, guest=False, user=None):
        """Sign up user.

        Hashes password and adds user to system.
        """

        if (user != None):
            hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')
            user.username = username
            user.password = hashed_pwd
            db.session.commit()
            return user
        elif (guest):
            last_id = User.query.with_entities(User.id.label("id")).order_by(User.id.desc()).limit(1).one_or_none()
            if (last_id == None):
                last_id = 0
            else:
                last_id = last_id.id
            username = f"guest{last_id+1}"
            password = ''.join(choices(ascii_letters, k=10))
            # print(password)

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            password=hashed_pwd,
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If can't find matching user (or if password is wrong), returns False.
        """

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False
    
class Words(db.Model):
    """Word dictionary"""

    __tablename__ = 'words'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    word = db.Column(
            db.Text,
            nullable=False
            )

    length = db.Column(
            db.Integer,
            nullable=False
            )
    
    example = db.Column(
        db.Boolean,
        default=True
    )

    definition = db.Column(
        db.Boolean,
        default=True
    )

    synonym = db.Column(
        db.Boolean,
        default=True
    )

    antonym = db.Column(
        db.Boolean,
        default=True
    )

class ApiTracker(db.Model):
    """Keeps track of daily API calls by users"""

    __tablename__ = "api_tracker"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    date = db.Column(
        db.Text,
        default=TZ_NOW(),
        nullable=False
    )

    api_calls = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )

# class GameType(db.Model):
#     """Holds all game types"""

#     __tablename__ = "game_types"

#     id = db.Column(
#         db.Integer,
#         primary_key=True
#     )

#     name = db.Column(
#         db.Text,
#         unique=True,
#         nullable=False
#     )


class Game(db.Model):
    """Game that each round associates with"""

    __tablename__ = "games"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    game_type = db.Column(
        db.Text,
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    score = db.Column(
        db.Integer,
        default=0
    )

    rounds = db.Column(
        db.Integer,
        default=10
    )

    completed = db.Column(
        db.Boolean,
        default=False
    )

    user = db.relationship("User")


class Round(db.Model):
    """Individual round in a game"""

    __tablename__ = "rounds"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    game_id = db.Column(
        db.Integer,
        db.ForeignKey("games.id", ondelete="CASCADE"),
        nullable=False
    )

    score = db.Column(
        db.Boolean
    )

    # hints = db.Column(
    #     db.Integer,
    #     nullable=False,
    #     default=0
    # )

    # In the form "word1, word2, word3, word4"
    words = db.Column(
        db.Text
    )

    answer = db.Column(
        db.Text
    )

    data = db.Column(
        db.Text
    )

    guess = db.Column(
        db.Text
    )

    completed = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    game = db.relationship("Game")

