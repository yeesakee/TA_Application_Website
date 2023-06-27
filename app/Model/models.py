
from datetime import datetime
from sqlalchemy import ForeignKey
import werkzeug.security as werkzeug
from werkzeug.security import generate_password_hash, check_password_hash
from app import *
from flask_login import UserMixin

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

prevta = db.Table('prevta', 
            db.Column('student_id', db.Integer, db.ForeignKey('student.id')),
            db.Column('course_id', db.Integer, db.ForeignKey('course.id'))
        )

class User(db.Model, UserMixin) :
    __tablename__= "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    wsu_id = db.Column(db.Integer, unique=True)
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(64))
    user_type = db.Column(db.String(64))

    __mapper_args__ = {
        'polymorphic_identity': 'User',
        'polymorphic_on': 'user_type'
    }

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def get_password(self, password):
        return check_password_hash(self.password_hash, password)


class Student(User) :
    __tablename__= 'student'
    id = db.Column(db.ForeignKey("user.id"), primary_key=True)
    major = db.Column(db.String(64))
    gpa = db.Column(db.DECIMAL(3,2))
    graduation = db.Column(db.String(64))
    assigned = db.Column(db.Boolean(), default = False)
    _studentapplication = db.relationship('Application')
    _coursestaken = db.relationship('Coursestaken', back_populates='students')
    prevta = db.relationship(
        'Course', secondary=prevta,
        primaryjoin=(prevta.c.student_id == id),
        backref=db.backref('prevta', lazy='dynamic'),
        lazy='dynamic'
    )

        
    __mapper_args__ = {
        'polymorphic_identity': 'Student'
    }

    def get_previous_ta(self):
        return self.prevta

    def get_student_applications(self):
        return self._studentapplication
    
    def get_studentid(self):
        return self.id

    def remove_coursetaken(self, courseid):
        course_taken = Coursestaken.query.filter_by(student_id=self.id).filter_by(course_id=courseid).first()
        db.session.delete(course_taken)
        db.session.commit()

    def remove_prevta(self, courseid):
        course = Course.query.filter_by(id=courseid).first()
        self.prevta.remove(course)
        db.session.commit()

    def __repr__(self):
        return 'Student: {} -- {} {} -- {}'.format(self.id, self.first_name, self.last_name, self.email)

class Faculty(User):
    __tablename__= 'faculty'
    id = db.Column(db.ForeignKey("user.id"), primary_key=True)
    _positions = db.relationship('Taposition', backref = 'writer', lazy = 'dynamic')

    __mapper_args__ = {
        'polymorphic_identity': 'Faculty'
    }

    def get_ta_positions(self):
        return self._positions

    def __repr__(self):
        return 'Faculty: {} -- {} {} -- {}'.format(self.id, self.first_name, self.last_name, self.email)
    
class Taposition(db.Model):
    id = db.Column(db.Integer(), primary_key=True) 
    semester = db.Column(db.String(64))
    year = db.Column(db.String(4))
    minGPA = db.Column(db.DECIMAL(3,2))
    minGrade = db.Column(db.String(2))
    TAExperience = db.Column(db.Boolean)
    ta_needed = db.Column(db.Integer())
    ta_filled = db.Column(db.Integer())
    faculty_id = db.Column(db.Integer(), db.ForeignKey('faculty.id'))
    course_id = db.Column(db.Integer(), db.ForeignKey('course.id'))
    _positionapplication = db.relationship('Application')
 

    def __repr__(self):
        return 'TA Position: {} -- semester, year: {}, {} -- course: {}'.format(self.id, self.semester, self.year, self.course_id)

    def get_applications(self):
        return self._positionapplication

class Application(db.Model):
    id = db.Column(db.Integer(), primary_key = True)
    grade_earned = db.Column(db.String())
    student_id = db.Column(db.Integer(), db.ForeignKey('student.id'))
    semester_taken = db.Column(db.String(64))
    semester_applying = db.Column(db.String(64))
    year_taken = db.Column(db.String(4))
    year_applying = db.Column(db.String(4))
    status = db.Column(db.Integer(), default = 0)
    # 0: not applied, 1: applied, 2: accepted
    position_id = db.Column(db.Integer(), db.ForeignKey('taposition.id'))

    def __repr__(self):
        return 'Application {} for student: {} '.format(self.id, self.student_id)
    
class Course(db.Model):
    id = db.Column(db.Integer(), primary_key = True)
    course_num = db.Column(db.String(3))
    course_prefix = db.Column(db.String(10))
    title = db.Column(db.String(200))
    _positions = db.relationship('Taposition')
    _students = db.relationship('Coursestaken', back_populates='courses')

    def __repr__(self):
        return 'Course: {} -- name: {}{}'.format(self.id, self.course_prefix, self.course_num)

    def get_positions(self):
        return self._positions

class Coursestaken(db.Model):
    student_id = db.Column(db.Integer(), db.ForeignKey('student.id'), primary_key = True)
    course_id = db.Column(db.Integer(), db.ForeignKey('course.id'), primary_key = True)
    grade_earned = db.Column(db.String(2))
    students = db.relationship('Student')
    courses = db.relationship('Course')

    def __repr__(self):
        return 'Prev course: {} --- Student: {} '.format(self.course_id, self.student_id)
