from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, BooleanField, PasswordField
from wtforms.validators import InputRequired, Optional, URL, NumberRange, Length, DataRequired

class AddUserForm(FlaskForm):
    """Add user form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])

class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])

class GameForm(FlaskForm):
    """Form for passing game data"""

    guess = StringField('', validators=[Optional()])
