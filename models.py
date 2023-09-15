from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def connect_db(app):
    """Connect to database."""

    db.app = app
    db.init_app(app)

# class User(db.Model):
#     """Blogly user"""

#     __tablename__ = "users"

#     id = db.Column(db.Integer,
#                    primary_key=True,
#                    autoincrement=True)
#     first_name = db.Column(db.String(50),
#                      nullable=False)
#     last_name = db.Column(db.String(50),
#                      nullable=False)
#     img = db.Column(db.String(), nullable=True)

