from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, IntegerField, DecimalField, SelectField
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms.validators import  ValidationError, DataRequired, EqualTo, Length, NumberRange
from app.Model.models import User, Course, Taposition

def get_course():
    return Course.query.all()

def get_course_name(theCourse):
    return theCourse.course_prefix + theCourse.course_num


class TapositionForm(FlaskForm):
    courseNum = QuerySelectField('Course', query_factory = get_course, get_label = get_course_name, allow_blank=False) 
    semester = SelectField('Semester', choices = ['Spring', 'Fall'])
    year = SelectField('Year', choices = ['2023', '2024', '2025', '2026', '2027'])
    minGPA = DecimalField('Minimum GPA', validators=[NumberRange(min=0, max=4)], places = 2)           
    minGrade = SelectField('Minimum Grade', choices = ['A', 'B', 'C', 'D'])
    TAExperience = BooleanField('Previous TA Experience')
    ta_needed = IntegerField('Number of TAs needed', validators=[DataRequired()])
    submit = SubmitField('Submit')

class ApplicationForm(FlaskForm):
    grade_earned = SelectField('Grade Earned', choices = ['A', 'B', 'C', 'D'])
    semester_taken = SelectField('Semester Taken', choices = ['Spring', 'Fall'])
    year_taken = SelectField('Year Taken', choices = ['2017', '2018', '2019', '2020', '2021', '2022'])
    semester_applying = SelectField('Semester', choices = ['Spring', 'Fall'])
    year_applying = SelectField('Year', choices = ['2023', '2024', '2025', '2026', '2027'])
    submit = SubmitField('Submit')

class CourseForm(FlaskForm):
    courseNum = QuerySelectField('Course', query_factory = get_course, get_label = get_course_name, allow_blank=False) 
    grade_earned = StringField('Grade Earned', [Length(min=1, max=2)])
    submit = SubmitField('Submit') 

class PrevtaForm(FlaskForm):
    courseNum = QuerySelectField('Course', query_factory = get_course, get_label = get_course_name, allow_blank=False) 
    submit = SubmitField('Submit') 