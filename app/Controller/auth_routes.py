from flask import Blueprint
from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user, login_user, logout_user
from config import Config
from app.Controller.auth_forms import SRegistrationForm, FRegistrationForm, LoginForm
from app.Model.models import User, Faculty, Student
from app import db


bp_auth = Blueprint('auth', __name__)
bp_auth.template_folder = Config.TEMPLATE_FOLDER 


@bp_auth.route('/register_student', methods=['GET', 'POST'])
def register_student():
    if current_user.is_authenticated:
        return redirect(url_for('routes.index_student'))
    sform = SRegistrationForm()
    if sform.validate_on_submit():
        new_student = Student (
            first_name = sform.first_name.data,
            last_name = sform.last_name.data,
            wsu_id = sform.wsu_id.data,
            email = sform.email.data,
            phone = sform.phone.data,
            username = sform.email.data,
            major = sform.major.data.course_prefix,
            gpa = sform.gpa.data,
            graduation = sform.graduation.data, 
            user_type = 'Student'
        )
        new_student.set_password(sform.password.data)
        db.session.add(new_student)
        db.session.commit()
        flash('Congratulations, you are now a registered student user')
        return redirect(url_for('routes.index_student'))
    return render_template('register_student.html', form=sform)


@bp_auth.route('/register_faculty', methods=['GET', 'POST'])
def register_faculty():
    if current_user.is_authenticated:
        return redirect(url_for('routes.index_faculty'))
    fform = FRegistrationForm()
    if fform.validate_on_submit():
        new_faculty = Faculty (
            first_name = fform.first_name.data,
            last_name = fform.last_name.data,
            wsu_id = fform.wsu_id.data,
            email = fform.email.data,
            phone = fform.phone.data,
            username = fform.email.data,
            user_type = 'Faculty'
        )
        new_faculty.set_password(fform.password.data)
        db.session.add(new_faculty)
        db.session.commit()
        flash('Congratulations, you are now a registered faculty user')
        return redirect(url_for('routes.index_faculty'))
    return render_template('register_faculty.html', form=fform)


@bp_auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.user_type == "Student":
            return redirect(url_for('routes.index_student'))
        else:
            return redirect(url_for('routes.index_faculty'))
    lform = LoginForm()
    if lform.validate_on_submit():
        user = User.query.filter_by(username = lform.username.data).first()
        if(user is None) or (not user.get_password(lform.password.data)):
            flash("Invalid Username or Password")
            return redirect(url_for('auth.login'))
        login_user(user, remember = lform.remember_me.data)
        if current_user.user_type == "Student":
            return redirect(url_for('routes.index_student'))
        else:
            return redirect(url_for('routes.index_faculty'))
    return render_template('login.html', title = 'Sign In', form = lform)

@bp_auth.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    flash('Please log in to access this page.')
    return redirect(url_for('auth.login'))