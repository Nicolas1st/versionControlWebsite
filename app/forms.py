from flask_wtf import FlaskForm
from sqlalchemy.sql.expression import text
from wtforms import StringField, SubmitField, PasswordField, EmailField
from wtforms.validators import DataRequired, Length, EqualTo


class LoginForm(FlaskForm):

    name = StringField(label=('Name:'), validators=[DataRequired(), Length(min=1)])
    password = PasswordField(label=('Password:'), validators=[DataRequired(), Length(min=2)])
    submit = SubmitField(label=('Submit'))


class SignupForm(FlaskForm):

    name = StringField(label=('Name:'), validators=[DataRequired(), Length(min=2)])
    email = EmailField(label=('Email:'), validators=[DataRequired()])
    password = PasswordField(label=('Password'), validators=[DataRequired(), Length(min=8, message='Password should be at least %(min)d characters long')])
    repeated_password = PasswordField(label=('Repeat the password'), validators=[DataRequired(message='*Required')])
    submit = SubmitField(label=('Submit'))


class ChangeNameForm(FlaskForm):

    name = StringField(label=('Enter new name:'), validators=[DataRequired(), Length(min=2)])
    submit = SubmitField(label=('Submit'))


class ChangeEmailForm(FlaskForm):

    email = EmailField(label=('Enter new email:'), validators=[DataRequired(), Length(min=2)])
    submit = SubmitField(label=('Submit'))


class ChangePasswordForm(FlaskForm):

    password = PasswordField(label=('Enter new password:'), validators=[DataRequired(), Length(min=8)])
    repeated_password = PasswordField(label=('Repeat the password:'),
                                      validators=[DataRequired(),
                                      EqualTo('password', message='Both password fields must be equal!')])
    submit = SubmitField(label=('Submit'))


class CreateProjectForm(FlaskForm):

    name = StringField(label=('Name:'), validators=[DataRequired(), Length(min=5)])
    description = StringField(label=('Description:'))
    submit = SubmitField(label=('Submit'))