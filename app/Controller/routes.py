from flask import Blueprint
from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from config import Config
import sys
from app.Model.models import Taposition, Application, Student, Course, Coursestaken, Faculty
from app.Controller.forms import TapositionForm, ApplicationForm, CourseForm, PrevtaForm
from app import db

bp_routes = Blueprint('routes', __name__)
bp_routes.template_folder = Config.TEMPLATE_FOLDER

@bp_routes.route('/', methods=['GET'])
@bp_routes.route('/index_student', methods=['GET'])
@login_required
def index_student():
    if current_user.user_type == 'Student':
        alltapositions = Taposition.query.all()
        positions = Taposition.query.filter(Taposition.minGPA <= current_user.gpa).all()
        all_positions = []
        for position in positions:
            course = Course.query.filter_by(id=position.course_id).first()
            if course.course_prefix == current_user.major:
                all_positions.append(position)
                
        recommended_positions = {}
        index = 0
        for position in all_positions:
            if index < 3:
                recommended_positions[position] = Course.query.filter_by(id = position.course_id).first()
                index = index + 1
 
        taposition_course = {}
        for ta in alltapositions:
            taposition_course[ta] = Course.query.filter_by(id = ta.course_id).first()

        instructors = Faculty.query.all()
        return render_template('index_student.html', title="Home", tapositions = alltapositions, 
            data = taposition_course, recommended = recommended_positions, profs = instructors)
    else:
        return redirect(url_for('routes.index_faculty'))
    
@bp_routes.route('/', methods=['GET'])
@bp_routes.route('/index_faculty', methods=['GET'])
@login_required
def index_faculty():
    if current_user.user_type == 'Faculty':
        tapositions = current_user.get_ta_positions()
        taposition_course = {}
        for ta in tapositions:
            taposition_course[ta] = Course.query.filter_by(id = ta.course_id).first()
        return render_template('index_faculty.html', title="Home", tapositions = taposition_course)
    else:
        return redirect(url_for('routes.index_student'))
    
@bp_routes.route('/create_taposition', methods=['GET', 'POST'])
@login_required
def create_taposition():
    if current_user.user_type == 'Faculty':
        tform = TapositionForm()
        if tform.validate_on_submit():
            new_position = Taposition(
                semester = tform.semester.data,
                year = tform.year.data,
                minGPA = tform.minGPA.data,
                minGrade = tform.minGrade.data,
                TAExperience = tform.TAExperience.data,
                ta_needed = tform.ta_needed.data,
                ta_filled = 0,
                faculty_id = current_user.id,
                course_id = tform.courseNum.data.id
            )
            position_check = Taposition.query.filter_by(faculty_id = new_position.faculty_id).filter_by(
                course_id = new_position.course_id).filter_by(
                semester = new_position.semester).filter_by(
                year = new_position.year).first()
            if position_check:
                flash('A TA position matching your credentials and the information you entered already exists. Please try again.')
            else:
                db.session.add(new_position)
                db.session.commit()
                flash('Congratulations, you made a new TA position!')
            return redirect(url_for('routes.index_faculty'))
        return render_template('create_taposition.html', form=tform)
    else:
        return redirect(url_for('routes.index_student'))

@bp_routes.route('/create_application/<positionid>', methods=['GET', 'POST'])
@login_required
def create_application(positionid):
    if current_user.user_type == 'Student':
        theposition = Taposition.query.filter_by(id=positionid).first()
        thecourse = Course.query.filter_by(id = theposition.course_id).first()
        if theposition is None:
            flash('Ta position with id "{}" not found.'.format(positionid))
            return redirect(url_for('routes.index_student'))
        
        # check that student hasn't already applied to ta position
        check_application = Application.query.filter_by(position_id=theposition.id).filter_by(student_id = current_user.id).first()
        if check_application is not None:
            course = thecourse.course_prefix + thecourse.course_num
            flash("Already applied to {}!".format(course))
            return redirect(url_for('routes.index_student'))
        aform = ApplicationForm()
        aform.year_applying.choices = [theposition.year]
        aform.semester_applying.choices = [theposition.semester]
        if aform.validate_on_submit():
            new_application = Application(
                grade_earned = aform.grade_earned.data,
                student_id = current_user.id,
                semester_taken = aform.semester_taken.data,
                semester_applying = aform.semester_applying.data,
                year_taken = aform.year_taken.data,
                year_applying = aform.year_applying.data, 
                status = 1,
                position_id = theposition.id
            )
            db.session.add(new_application)
            db.session.commit()
            flash('Congratulations, you successfully applied!')
            return redirect(url_for('routes.index_student'))
        return render_template('create_application.html', form = aform, course = thecourse)
    else:
        return redirect(url_for('routes.index_faculty'))

@bp_routes.route('/view_applicants/<positionid>', methods=['GET', 'POST'])
@login_required
def view_applicants(positionid):
    if current_user.user_type == 'Faculty':
        theposition = Taposition.query.filter_by(id=positionid).first()
        applications = theposition.get_applications()
        students = []
        for a in applications:
            students.append(Student.query.filter_by(id = a.student_id).first())
        
        return render_template('faculty_applicants.html', title="Title", students = students, position = theposition )
    else:
        return redirect(url_for('routes.index_student'))

@bp_routes.route('/view_qualifications/<studentid>', methods=['POST'])
@login_required
def view_qualifications(studentid):
    if current_user.user_type == 'Faculty':
        student = Student.query.filter_by(id = studentid).first()
        prev_ta = student.get_previous_ta().all()
        coursestaken = Coursestaken.query.filter_by(student_id = studentid).all()
        courses = {}
        for c in coursestaken:
            courses[c] = Course.query.filter_by(id = c.course_id).first()
        return render_template('qualifications.html',student = student, courses = courses, prev_ta=prev_ta)
    else:
        return redirect(url_for('routes.index_student'))

@bp_routes.route('/approve_application/<positionid>/<studentid>', methods = ['POST'])
@login_required
def approve_application(positionid, studentid):
    if current_user.user_type == 'Faculty':
        theposition = Taposition.query.filter_by(id = positionid).first()
        thestudent = Student.query.filter_by(id = studentid).first()
        if theposition.ta_needed != theposition.ta_filled:
            if not thestudent.assigned:
                theposition.ta_filled += 1
                thestudent.assigned = True
                Application.query.filter_by(position_id = theposition.id).filter_by(student_id = thestudent.id).first().status = 2
                db.session.commit()
                flash('Student has been approved for TA Position')
            else:
                flash('Error: unable to approve student. Student is already assigned to another TA position!')
        else:
            flash('Error: unable to approve student. All TA positions already filled!')
        return redirect(url_for('routes.index_faculty'))
    else:
        return redirect(url_for('routes.index_student'))

@bp_routes.route('/withdraw_application/<applicationid>', methods=['POST'])
@login_required
def withdraw_application(applicationid):
    if current_user.user_type == 'Student':
        application = Application.query.filter_by(id = applicationid).first()
        db.session.delete(application)
        db.session.commit()
        return redirect(url_for('routes.aboutme_student'))
    else:
        return redirect(url_for('routes.index_faculty'))

@bp_routes.route('/', methods=['GET'])
@bp_routes.route('/aboutme_student', methods=['GET'])
@login_required
def aboutme_student():
    if current_user.user_type == 'Student':
        s = Student.query.filter_by(id=current_user.id).first()
        prev_ta = s.get_previous_ta().all()
        coursestaken = Coursestaken.query.filter_by(student_id = current_user.id).all()
        courses = {}
        for c in coursestaken:
            courses[c] = Course.query.filter_by(id = c.course_id).first()
        my_applications = Application.query.filter_by(student_id=current_user.id).all()
        applications = {}
        for application in my_applications:
            ta_position_applied = Taposition.query.filter_by(id = application.position_id).first()
            course_applied = Course.query.filter_by(id = ta_position_applied.course_id).first()
            applications[application] = course_applied.course_prefix + " " + course_applied.course_num
        return render_template('aboutme_student.html', title="About Me", courses = courses, prev_ta=prev_ta, applications=applications)
    else:
        return redirect(url_for('routes.index_faculty'))
@bp_routes.route('/add_course', methods=['GET', 'POST'])
@login_required
def add_course():
    if current_user.user_type == 'Student':
        add_cform = CourseForm()
        if add_cform.validate_on_submit():
            prev_taken = Coursestaken.query.filter_by(student_id=current_user.id).filter_by(course_id=add_cform.courseNum.data.id).all()
            course_name = add_cform.courseNum.data.course_prefix + add_cform.courseNum.data.course_num
            if len(prev_taken) == 0:
                course = Coursestaken(
                    student_id = current_user.id,
                    course_id = add_cform.courseNum.data.id,
                    grade_earned = add_cform.grade_earned.data
                )
                db.session.add(course)
                db.session.commit()
                flash('You added {} to your courses taken list.'.format(course_name))
                return redirect(url_for('routes.aboutme_student'))
            else:
                flash('You already added {} to your previous taken courses list!'.format(course_name))
        return render_template('add_course_taken.html', form = add_cform)
    else:
        return redirect(url_for('routes.index_faculty')) 

@bp_routes.route('/remove_course/<courseid>', methods=['POST'])
@login_required
def remove_course(courseid):
    if current_user.user_type == 'Student':
            s = Student.query.filter_by(id=current_user.id).first()
            s.remove_coursetaken(courseid)
            db.session.commit()
            course_name = Course.query.filter_by(id=courseid).first()
            flash('You deleted {} from your courses taken list.'.format(course_name.course_prefix + course_name.course_num))
            return redirect(url_for('routes.aboutme_student'))
    else:
        return redirect(url_for('routes.index_faculty')) 

@bp_routes.route('/add_prevta', methods=['GET', 'POST'])
@login_required
def add_prevta():
    if current_user.user_type == 'Student':
        pform = PrevtaForm()
        if pform.validate_on_submit():
            curr_student = Student.query.filter_by(id=current_user.id).first()
            course_name = pform.courseNum.data.course_prefix + pform.courseNum.data.course_num
            course = curr_student.get_previous_ta().all()
            if pform.courseNum.data in course:
                flash('You already added {} to your previous TA\'d courses list!'.format(course_name))
                return render_template('add_prevta.html', form = pform)
            else:
                my_course = pform.courseNum.data
                curr_student.prevta.append(my_course)
                db.session.commit()
                flash('You added {} to your courses TA\'d list.'.format(course_name))
                return redirect(url_for('routes.aboutme_student'))
        return render_template('add_prevta.html', form = pform)
    else:
        return redirect(url_for('routes.index_faculty')) 

@bp_routes.route('/remove_prevta/<courseid>', methods=['POST'])
@login_required
def remove_prevta(courseid):
    if current_user.user_type == 'Student':
            s = Student.query.filter_by(id=current_user.id).first()
            s.remove_prevta(courseid)
            db.session.commit()
            course_name = Course.query.filter_by(id=courseid).first()
            flash('You deleted {} from your previously TA\'d list.'.format(course_name.course_prefix + course_name.course_num))
            return redirect(url_for('routes.aboutme_student'))
    else:
        return redirect(url_for('routes.index_faculty')) 