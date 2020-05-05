#!/usr/bin/env python3
from flask_wtf import Form
from wtforms.fields import StringField, SubmitField
from wtforms.validators import DataRequired

class CreateServer(Form):
    name = StringField('Server Name', validators=[DataRequired()])
    admin = StringField('User Name', validators=[DataRequired()])
    admin_key = StringField('Password', validators=[DataRequired()])
    submit = SubmitField('Create Server')

class ServerLogin(Form):
    user = StringField('User Name', validators=[DataRequired()])
    key = StringField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
