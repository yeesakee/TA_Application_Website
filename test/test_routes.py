import os
import pytest
from app import create_app, db
from app.Model.models import *
from app.Controller.forms import TapositionForm
from config import Config


class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    SECRET_KEY = 'bad-bad-key'
    WTF_CSRF_ENABLED = False
    DEBUG = True
    TESTING = True


@pytest.fixture(scope='module')
def test_client():
    # create the flask application ; configure the app for tests
    flask_app = create_app(config_class=TestConfig)

    db.init_app(flask_app)
    # Flask provides a way to test your application by exposing the Werkzeug test Client
    # and handling the context locals for you.
    testing_client = flask_app.test_client()
 
    # Establish an application context before running the tests.
    ctx = flask_app.app_context()
    ctx.push()
 
    yield  testing_client 
    # this is where the testing happens!
 
    ctx.pop()

def new_faculty(pwd, first, last, wid, mail, pnum):
    f = Faculty(username = mail,
                first_name = first,
                last_name = last,
                wsu_id = wid,
                email = mail,
                phone = pnum,
                user_type = 'Faculty')
    f.set_password(pwd)
    return f

def new_student(pwd, first, last, wid, mail, pnum, maj, gpavg, grad):
    s = Student(username = mail,
                first_name = first,
                last_name = last,
                wsu_id = wid,
                email = mail,
                phone = pnum,
                user_type = 'Student',
                major = maj, 
                gpa = gpavg,
                graduation = grad)
    s.set_password(pwd)
    return s

def init_courses():
    if Course.query.count() == 0:
        courses = [{'course_num': '121', 'course_prefix':'CptS', 'title':'Program Design and Development C/C++'},
                  {'course_num': '122', 'course_prefix':'CptS', 'title':'Data Structures C/C++'},
                  {'course_num': '223', 'course_prefix':'CptS', 'title':'Advanced Data Structures'},
                  {'course_num': '317', 'course_prefix':'CptS', 'title':'Automata and Formal Lanugages'},
                  {'course_num': '322', 'course_prefix':'CptS', 'title':'Software Engineering Principles I'}]
        for c in courses:
            db.session.add(Course(course_num=c['course_num'], course_prefix=c['course_prefix'], title=c['title']))
        db.session.commit()
    return None

@pytest.fixture
def init_database():
    db.create_all()
    init_courses()
    user_s1 = new_student("pwd", "John", "Doe", 12345678, "john.doe@wsu.edu", 1231231234, "CptS", 3.5, "2025")
    user_f1 = new_faculty("pwd", "Jane", "Doe", 12345679, "jane.doe@wsu.edu", 1231221234)
    db.session.add(user_s1)
    db.session.add(user_f1)
    db.session.commit()
    yield

    db.drop_all()

# faculty_register GET
def test_faculty_register_page(test_client):
    response = test_client.get('/register_faculty')
    assert response.status_code == 200
    assert b"Register Faculty" in response.data

# student_register GET
def test_student_register_page(test_client, init_database):
    response = test_client.get('/register_student')
    assert response.status_code == 200
    assert b"Register Student" in response.data

# faculty_register POST
def test_faculty_register(test_client, init_database):
    response = test_client.post('/register_faculty',
                            data = dict(first_name = "average", last_name = "joe", wsu_id = 12344321,
                            email = "average.joe@wsu.edu", phone = 1231231234, password = "password",password2 = "password"), 
                            follow_redirects = True)
    assert response.status_code == 200
    f = db.session.query(Faculty).filter(Faculty.username=='average.joe@wsu.edu')
    assert f.first().email == 'average.joe@wsu.edu'
    assert f.count() == 1
    assert b"Sign In" in response.data
    assert b"Please log in to access this page" in response.data

# student_register POST
def test_student_register(test_client, init_database):
    response = test_client.post('/register_student',
                            data = dict(first_name = "jay", last_name = "smith", wsu_id = 43214321,
                            email = "jay.smith@wsu.edu", phone = 3213214321, major = Course.query.filter_by(course_prefix = "CptS").first().id, 
                            gpa = 4.0, graduation = "2022", password = "password", password2 = "password"),
                            follow_redirects = True)
    assert response.status_code == 200
    s = db.session.query(Student).filter(Student.username=='jay.smith@wsu.edu')
    assert s.first().email == 'jay.smith@wsu.edu'
    assert s.count() == 1
    assert b"Sign In" in response.data
    assert b"Please log in to access this page" in response.data

# Invalid login
def test_invalid_login(test_client, init_database):
    response = test_client.post('/login',
                            data = dict(username='test@wsu.edu', password = '123', remember_me=False),
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"Invalid Username or Password" in response.data

# Logout
def test_logout(test_client, init_database):
    response = test_client.post('/login',
                            data = dict(username = 'john.doe@wsu.edu', password = 'pwd', remember_me = False),
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"Open TA Positions" in response.data

    response = test_client.get('/logout',
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"Sign In" in response.data
    assert b"Please log in to access this page" in response.data

# create_taposition GET and POST
def test_create_taposition(test_client, init_database):
    response = test_client.post('/login',
                            data = dict(username = 'jane.doe@wsu.edu', password = 'pwd', remember_me = False),
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"TA Positions" in response.data

    response = test_client.get('/create_taposition')
    assert response.status_code == 200
    assert b"Create a New TA Position" in response.data  

    response = test_client.post('/create_taposition',
                            data = dict(courseNum = Course.query.filter_by(course_prefix = "CptS").filter_by(course_num = "322").first().id,
                            semester = "Spring", year = "2023", minGPA = 3.00, minGrade = "B", TAExperience = False, ta_needed = 4 ),
                            follow_redirects = True)
    assert b"CptS 322" in response.data
    assert b"Spring" in response.data
    assert b"Congratulations, you made a new TA position!" in response.data
    ta = db.session.query(Taposition).filter(Taposition.course_id == Course.query.filter_by(course_prefix = "CptS").filter_by(course_num = "322").first().id)
    assert ta.first().minGrade == "B"
    assert ta.count() == 1

    response = test_client.get('/logout',
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"Sign In" in response.data
    assert b"Please log in to access this page" in response.data

# create_application GET and POST
def test_create_application(test_client, init_database):

    response = test_client.post('/login',
                            data = dict(username = 'jane.doe@wsu.edu', password = 'pwd', remember_me = False),
                            follow_redirects = True)
    assert response.status_code == 200

    response = test_client.post('/create_taposition',
                            data = dict(courseNum = Course.query.filter_by(course_prefix = "CptS").filter_by(course_num = "322").first().id,
                            semester = "Spring", year = "2023", minGPA = 3.00, minGrade = "B", TAExperience = False, ta_needed = 4 ),
                            follow_redirects = True)
    assert b"CptS 322" in response.data
    assert b"Spring" in response.data
    assert b"Congratulations, you made a new TA position!" in response.data
    ta = db.session.query(Taposition).filter(Taposition.course_id == Course.query.filter_by(course_prefix = "CptS").filter_by(course_num = "322").first().id)
    assert ta.first().minGrade == "B"
    assert ta.count() == 1

    response = test_client.get('/logout',
                            follow_redirects = True)
    assert response.status_code == 200

    response = test_client.post('/login',
                            data = dict(username = 'john.doe@wsu.edu', password = 'pwd', remember_me = False),
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"Open TA Positions" in response.data
    assert b"CptS 322" in response.data

    ta = db.session.query(Taposition).filter(Taposition.course_id == Course.query.filter_by(course_prefix = "CptS").filter_by(course_num = "322").first().id).first()

    response = test_client.get('/create_application/' + str(ta.id))
    assert response.status_code == 200
    assert b"New Application for CptS 322 TA Position"

    response = test_client.post('/create_application/' + str(ta.id),
                            data = dict(grade_earned = "A", semester_taken = "Fall", year_taken = "2022", 
                            semester_applying = "Spring", year_applying = "2023"),
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"Congratulations, you successfully applied!" in response.data

    application = db.session.query(Application).filter(Application.position_id == ta.id)
    assert application.count() == 1
    assert application.first().status == 1

    response = test_client.get('/logout',
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"Sign In" in response.data
    assert b"Please log in to access this page" in response.data

# view_applicants GET and POST
def test_view_applicants(test_client, init_database):
    response = test_client.post('/login',
                            data = dict(username = 'jane.doe@wsu.edu', password = 'pwd', remember_me = False),
                            follow_redirects = True)
    assert response.status_code == 200

    response = test_client.post('/create_taposition',
                            data = dict(courseNum = Course.query.filter_by(course_prefix = "CptS").filter_by(course_num = "322").first().id,
                            semester = "Spring", year = "2023", minGPA = 3.00, minGrade = "B", TAExperience = False, ta_needed = 4 ),
                            follow_redirects = True)
    assert b"CptS 322" in response.data
    assert b"Spring" in response.data
    assert b"Congratulations, you made a new TA position!" in response.data
    ta = db.session.query(Taposition).filter(Taposition.course_id == Course.query.filter_by(course_prefix = "CptS").filter_by(course_num = "322").first().id)
    assert ta.first().minGrade == "B"
    assert ta.count() == 1

    response = test_client.get('/logout',
                            follow_redirects = True)
    assert response.status_code == 200

    response = test_client.post('/login',
                            data = dict(username = 'john.doe@wsu.edu', password = 'pwd', remember_me = False),
                            follow_redirects = True)
    assert response.status_code == 200

    ta = db.session.query(Taposition).filter(Taposition.course_id == Course.query.filter_by(course_prefix = "CptS").filter_by(course_num = "322").first().id).first()

    response = test_client.post('/create_application/' + str(ta.id),
                            data = dict(grade_earned = "A", semester_taken = "Fall", year_taken = "2022", 
                            semester_applying = "Spring", year_applying = "2023"),
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"Congratulations, you successfully applied!" in response.data

    application = db.session.query(Application).filter(Application.position_id == ta.id)
    assert application.count() == 1
    assert application.first().status == 1

    response = test_client.get('/logout',
                            follow_redirects = True)
    assert response.status_code == 200

    ta = db.session.query(Taposition).filter(Taposition.course_id == Course.query.filter_by(course_prefix = "CptS").filter_by(course_num = "322").first().id).first()

    response = test_client.post('/login',
                            data = dict(username = 'jane.doe@wsu.edu', password = 'pwd', remember_me = False),
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"TA Positions" in response.data

    response = test_client.get('/view_applicants/' + str(ta.id))
    assert response.status_code == 200
    assert b"List of applicants" in response.data

    response = test_client.post('/view_applicants/' + str(ta.id),
                                data = {},
                                follow_redirects = True)
    assert response.status_code == 200
    assert b"Qualifications" in response.data 
    application = db.session.query(Application).filter(Application.position_id == ta.id)
    assert application.first().status == 1

    response = test_client.get('/logout',
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"Sign In" in response.data
    assert b"Please log in to access this page" in response.data

# view_qualifications POST
def test_view_qualifications(test_client, init_database):
    response = test_client.post('/login',
                            data = dict(username = 'jane.doe@wsu.edu', password = 'pwd', remember_me = False),
                            follow_redirects = True)
    assert response.status_code == 200

    response = test_client.post('/create_taposition',
                            data = dict(courseNum = Course.query.filter_by(course_prefix = "CptS").filter_by(course_num = "322").first().id,
                            semester = "Spring", year = "2023", minGPA = 3.00, minGrade = "B", TAExperience = False, ta_needed = 4 ),
                            follow_redirects = True)
    assert b"CptS 322" in response.data
    assert b"Spring" in response.data
    assert b"Congratulations, you made a new TA position!" in response.data
    ta = db.session.query(Taposition).filter(Taposition.course_id == Course.query.filter_by(course_prefix = "CptS").filter_by(course_num = "322").first().id)
    assert ta.first().minGrade == "B"
    assert ta.count() == 1

    response = test_client.get('/logout',
                            follow_redirects = True)
    assert response.status_code == 200

    response = test_client.post('/login',
                            data = dict(username = 'john.doe@wsu.edu', password = 'pwd', remember_me = False),
                            follow_redirects = True)
    assert response.status_code == 200

    ta = db.session.query(Taposition).filter(Taposition.course_id == Course.query.filter_by(course_prefix = "CptS").filter_by(course_num = "322").first().id).first()

    response = test_client.post('/create_application/' + str(ta.id),
                            data = dict(grade_earned = "A", semester_taken = "Fall", year_taken = "2022", 
                            semester_applying = "Spring", year_applying = "2023"),
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"Congratulations, you successfully applied!" in response.data

    application = db.session.query(Application).filter(Application.position_id == ta.id)
    assert application.count() == 1
    assert application.first().status == 1

    response = test_client.get('/logout',
                            follow_redirects = True)
    assert response.status_code == 200

    ta = db.session.query(Taposition).filter(Taposition.course_id == Course.query.filter_by(course_prefix = "CptS").filter_by(course_num = "322").first().id).first()
    application = db.session.query(Application).filter(Application.position_id == ta.id).first()
    response = test_client.post('/login',
                            data = dict(username = 'jane.doe@wsu.edu', password = 'pwd', remember_me = False),
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"TA Positions" in response.data

    response = test_client.post('/view_qualifications/' + str(application.student_id),
                            data = {},
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"Qualifications" in response.data
    assert b"John Doe" in response.data
    assert b"GPA" in response.data
    assert b"Past TA Positions" in response.data
    assert b"Past Courses" in response.data

    response = test_client.get('/logout',
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"Sign In" in response.data
    assert b"Please log in to access this page" in response.data

# approve_applcation POST
def test_approve_application(test_client, init_database):
    response = test_client.post('/login',
                            data = dict(username = 'jane.doe@wsu.edu', password = 'pwd', remember_me = False),
                            follow_redirects = True)
    assert response.status_code == 200

    response = test_client.post('/create_taposition',
                            data = dict(courseNum = Course.query.filter_by(course_prefix = "CptS").filter_by(course_num = "322").first().id,
                            semester = "Spring", year = "2023", minGPA = 3.00, minGrade = "B", TAExperience = False, ta_needed = 4 ),
                            follow_redirects = True)
    assert b"CptS 322" in response.data
    assert b"Spring" in response.data
    assert b"Congratulations, you made a new TA position!" in response.data
    ta = db.session.query(Taposition).filter(Taposition.course_id == Course.query.filter_by(course_prefix = "CptS").filter_by(course_num = "322").first().id)
    assert ta.first().minGrade == "B"
    assert ta.count() == 1

    response = test_client.get('/logout',
                            follow_redirects = True)
    assert response.status_code == 200

    response = test_client.post('/login',
                            data = dict(username = 'john.doe@wsu.edu', password = 'pwd', remember_me = False),
                            follow_redirects = True)
    assert response.status_code == 200

    ta = db.session.query(Taposition).filter(Taposition.course_id == Course.query.filter_by(course_prefix = "CptS").filter_by(course_num = "322").first().id).first()

    response = test_client.post('/create_application/' + str(ta.id),
                            data = dict(grade_earned = "A", semester_taken = "Fall", year_taken = "2022", 
                            semester_applying = "Spring", year_applying = "2023"),
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"Congratulations, you successfully applied!" in response.data

    application = db.session.query(Application).filter(Application.position_id == ta.id)
    assert application.count() == 1
    assert application.first().status == 1

    response = test_client.get('/logout',
                            follow_redirects = True)
    assert response.status_code == 200

    ta = db.session.query(Taposition).filter(Taposition.course_id == Course.query.filter_by(course_prefix = "CptS").filter_by(course_num = "322").first().id).first()
    application = db.session.query(Application).filter(Application.position_id == ta.id).first()

    response = test_client.post('/login',
                            data = dict(username = 'jane.doe@wsu.edu', password = 'pwd', remember_me = False),
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"TA Positions" in response.data

    response = test_client.post('/approve_application/' + str(ta.id) + '/' + str(application.student_id),
                            data = {},
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"TA Positions" in response.data
    assert b"Student has been approved for TA Position" in response.data
    assert application.status == 2
    assert db.session.query(Student).filter(Student.id == application.student_id).first().assigned == True
    
    response = test_client.get('/logout',
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"Sign In" in response.data
    assert b"Please log in to access this page" in response.data

# withdraw_application POST
def test_withdraw_application(test_client, init_database):
    response = test_client.post('/login',
                            data = dict(username = 'jane.doe@wsu.edu', password = 'pwd', remember_me = False),
                            follow_redirects = True)
    assert response.status_code == 200

    response = test_client.post('/create_taposition',
                            data = dict(courseNum = Course.query.filter_by(course_prefix = "CptS").filter_by(course_num = "322").first().id,
                            semester = "Spring", year = "2023", minGPA = 3.00, minGrade = "B", TAExperience = False, ta_needed = 4 ),
                            follow_redirects = True)
    assert b"CptS 322" in response.data
    assert b"Spring" in response.data
    assert b"Congratulations, you made a new TA position!" in response.data
    ta = db.session.query(Taposition).filter(Taposition.course_id == Course.query.filter_by(course_prefix = "CptS").filter_by(course_num = "322").first().id)
    assert ta.first().minGrade == "B"
    assert ta.count() == 1

    response = test_client.get('/logout',
                            follow_redirects = True)
    assert response.status_code == 200

    response = test_client.post('/login',
                            data = dict(username = 'john.doe@wsu.edu', password = 'pwd', remember_me = False),
                            follow_redirects = True)
    assert response.status_code == 200

    ta = db.session.query(Taposition).filter(Taposition.course_id == Course.query.filter_by(course_prefix = "CptS").filter_by(course_num = "322").first().id).first()

    response = test_client.post('/create_application/' + str(ta.id),
                            data = dict(grade_earned = "A", semester_taken = "Fall", year_taken = "2022", 
                            semester_applying = "Spring", year_applying = "2023"),
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"Congratulations, you successfully applied!" in response.data

    application = db.session.query(Application).filter(Application.position_id == ta.id)
    assert application.count() == 1
    assert application.first().status == 1

    response = test_client.get('/logout',
                            follow_redirects = True)
    assert response.status_code == 200

    ta = db.session.query(Taposition).filter(Taposition.course_id == Course.query.filter_by(course_prefix = "CptS").filter_by(course_num = "322").first().id).first()
    application = db.session.query(Application).filter(Application.position_id == ta.id).first()

    response = test_client.post('/login',
                            data = dict(username = 'john.doe@wsu.edu', password = 'pwd', remember_me = False),
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"Open TA Positions" in response.data
    assert b"CptS 322" in response.data
    assert application.status == 1

    response = test_client.post('/withdraw_application/' + str(application.id),
                            data = {},
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"About Me"
    assert b"My Applications"
    application = db.session.query(Application).filter(Application.position_id == ta.id).first()
    assert application == None

    response = test_client.get('/logout',
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"Sign In" in response.data
    assert b"Please log in to access this page" in response.data

# aboutme_student GET
def test_aboutme_student(test_client, init_database):
    response = test_client.post('/login',
                            data = dict(username = 'john.doe@wsu.edu', password = 'pwd', remember_me = False),
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"Open TA Positions" in response.data

    response = test_client.get('/aboutme_student')
    assert response.status_code == 200
    assert b"John Doe" in response.data
    assert b"About Me" in response.data
    assert b"My Past TA Position" in response.data
    assert b"My Past Courses" in response.data
    assert b"My Applications" in response.data

    response = test_client.get('/logout',
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"Sign In" in response.data
    assert b"Please log in to access this page" in response.data

# add_course GET and POST
def test_add_course(test_client, init_database):
    response = test_client.post('/login',
                            data = dict(username = 'john.doe@wsu.edu', password = 'pwd', remember_me = False),
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"Open TA Positions" in response.data

    response = test_client.get('add_course')
    assert response.status_code == 200
    assert b"Add Previously Taken Course" in response.data

    response = test_client.post('add_course',
                            data = dict(courseNum = Course.query.filter_by(id = 5).first().id, 
                            student_id = Student.query.filter_by(username = "john.doe@wsu.edu").first().id,
                            course_id = 5, grade_earned = "A"),
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"You added CptS322 to your courses taken list" in response.data
    student = db.session.query(Student).filter(Student.username == 'john.doe@wsu.edu').first()
    prev_course = db.session.query(Coursestaken).filter(Coursestaken.student_id == student.id).filter(Coursestaken.course_id == 5)
    assert prev_course.first().grade_earned == "A"
    assert prev_course.count() == 1

    response = test_client.get('/logout',
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"Sign In" in response.data
    assert b"Please log in to access this page" in response.data

# remove_course POST
def test_remove_course(test_client, init_database):
    response = test_client.post('/login',
                            data = dict(username = 'john.doe@wsu.edu', password = 'pwd', remember_me = False),
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"Open TA Positions" in response.data

    response = test_client.post('add_course',
                            data = dict(courseNum = Course.query.filter_by(id = 5).first().id, 
                            student_id = Student.query.filter_by(username = "john.doe@wsu.edu").first().id,
                            course_id = 5, grade_earned = "A"),
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"You added CptS322 to your courses taken list" in response.data
    student = db.session.query(Student).filter(Student.username == 'john.doe@wsu.edu').first()
    prev_course = db.session.query(Coursestaken).filter(Coursestaken.student_id == student.id).filter(Coursestaken.course_id == 5)
    assert prev_course.first().grade_earned == "A"
    assert prev_course.count() == 1

    course = db.session.query(Course).filter(Course.id == 5).first()

    response = test_client.post('/remove_course/' + str(course.id),
                            data = {},
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"About Me"
    assert b"My Past Courses"
    prev_course = db.session.query(Coursestaken).filter(Coursestaken.course_id == 5).filter(
                    Coursestaken.student_id == db.session.query(Student).filter(Student.username == 'john.doe@wsu.edu').first().id)
    assert prev_course.first() == None

    response = test_client.get('/logout',
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"Sign In" in response.data
    assert b"Please log in to access this page" in response.data

# add_prevta GET and POST
def test_add_prevta(test_client, init_database):
    response = test_client.post('/login',
                            data = dict(username = 'john.doe@wsu.edu', password = 'pwd', remember_me = False),
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"Open TA Positions" in response.data

    response = test_client.get('add_prevta')
    assert response.status_code == 200
    assert b"Add Previously TA'd Course" in response.data

    response = test_client.post('add_prevta',
                            data = dict(courseNum = Course.query.filter_by(id = 5).first().id),
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"You added CptS322 to your courses TA'd list"
    student = db.session.query(Student).filter(Student.username == 'john.doe@wsu.edu').first()
    assert student.prevta.count() == 1

    response = test_client.get('/logout',
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"Sign In" in response.data
    assert b"Please log in to access this page" in response.data

# remove_prevta POST
def test_remove_prevta(test_client, init_database):
    response = test_client.post('/login',
                            data = dict(username = 'john.doe@wsu.edu', password = 'pwd', remember_me = False),
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"Open TA Positions" in response.data

    response = test_client.post('add_prevta',
                            data = dict(courseNum = Course.query.filter_by(id = 5).first().id),
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"You added CptS322 to your courses TA'd list"
    student = db.session.query(Student).filter(Student.username == 'john.doe@wsu.edu').first()
    assert student.prevta.count() == 1

    course = db.session.query(Course).filter(Course.id == 5).first()

    response = test_client.post('/remove_prevta/' + str(course.id),
                            data = {},
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"About Me"
    assert b"My Past TA Positions"
    student = db.session.query(Student).filter(Student.username == 'john.doe@wsu.edu').first()
    assert student.prevta.count() == 0

    response = test_client.get('/logout',
                            follow_redirects = True)
    assert response.status_code == 200
    assert b"Sign In" in response.data
    assert b"Please log in to access this page" in response.data
