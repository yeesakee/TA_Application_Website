from flask_wtf import FlaskForm
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms import StringField, SubmitField, PasswordField, BooleanField, IntegerField, DecimalField
from wtforms.validators import  ValidationError, DataRequired, EqualTo, Email, Length, NumberRange
from app.Model.models import User, Course
import datetime

def get_course():
    course = Course.query.all()
    course_prefix=set()
    result = []
    for c in course:
        if c.course_prefix not in course_prefix:
            course_prefix.add(c.course_prefix)
            result.append(c)
    return result

def get_majors(theCourse):
    return theCourse.course_prefix

class FRegistrationForm(FlaskForm):

    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    wsu_id = IntegerField('WSU ID', validators=[DataRequired(), NumberRange(min=00000000, max=99999999)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = IntegerField('Phone Number')
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('The email already exists! Please use a different email address.')
        if email.data[-8:] != '@wsu.edu':
            raise ValidationError('Please use WSU email')
    
    def validate_wsu_id(self, wsu_id):
        user = User.query.filter_by(wsu_id=wsu_id.data).first()
        if user is not None:
            raise ValidationError('The WSU ID already exists! Please enter your valid WSU ID.')

    def validate_phone(self, phone):
        if len(str(phone.data)) > 16 or len(str(phone.data)) < 10:
            raise ValidationError('Invalid phone number')


class SRegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    wsu_id = IntegerField('WSU ID', validators=[DataRequired(),NumberRange(min=10000000, max=99999999)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = IntegerField('Phone Number')
    major = QuerySelectField('Major', query_factory = get_course, get_label = get_majors, allow_blank=False)
    gpa = DecimalField('GPA', validators=[DataRequired(), NumberRange(min=0, max=4)], places = 2)
    graduation = StringField('Expected Graduation', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')


    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('The email already exists! Please use a different email address.')
        if email.data[-8:] != '@wsu.edu':
            raise ValidationError('Please use WSU email')

    def validate_wsu_id(self, wsu_id):
        user = User.query.filter_by(wsu_id=wsu_id.data).first()
        if user is not None:
            raise ValidationError('The WSU ID already exists! Please enter your valid WSU ID.')

    def validate_phone(self, phone):
        if len(str(phone.data)) > 16 or len(str(phone.data)) < 10:
            raise ValidationError('Invalid phone number')

    def validate_graduation(self, graduation):
        if int(graduation.data) > datetime.date.today().year + 6 or int(graduation.data) < datetime.date.today().year:
            raise ValidationError('Unreasonable graduation year')



class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')