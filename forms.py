from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, BooleanField
from wtforms.validators import InputRequired, Optional, URL, NumberRange

# class AddPetsForm(FlaskForm):
#     """Form for adding pets"""

#     name = StringField("Name of pet", validators=[InputRequired()])
#     species = SelectField("Pet Species", validators=[InputRequired()],
#                            choices=[('Dog', 'Dog'), ('Porcupine', 'Porcupine'), ('Cat', 'Cat')])
#     photo_url = StringField("Photo of pet", validators=[Optional(), URL()])
#     age = IntegerField("Age of pet", validators=[Optional(), NumberRange(min=0, max=30, message="Age is invalid")])
#     notes = StringField("Any notes regarding the pet", validators=[Optional()])
#     available = SelectField("Pet Species", validators=[Optional()],
#                            choices=[('True', 'Available'), ('False', 'Not available')])
