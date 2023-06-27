import warnings
warnings.filterwarnings("ignore")
import unittest
from app import create_app, db
from app.Model.models import Student, Faculty, Taposition, Application, Course, Coursestaken
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'

class TestModels(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_password_hashing(self):
        s = Student(username='m.w@wsu.edu', first_name='michael', last_name='w', email='m.w@wsu.edu', wsu_id='11111111', major='Computer Science', gpa='4.0', graduation='Spring 2023')
        s.set_password('abcd')
        self.assertFalse(s.get_password('defg'))
        self.assertTrue(s.get_password('abcd'))

    def test_student_get_previous_ta(self):
        s = Student(username='m.w@wsu.edu', first_name='michael', last_name='w', email='m.w@wsu.edu', wsu_id='11111111', major='Computer Science', gpa='4.0', graduation='Spring 2023')
        c122 = Course(course_num='122', course_prefix='CptS', title='Program Design and Development C/C++')
        db.session.add(s)
        db.session.add(c122)
        s.prevta.append(c122)
        db.session.commit()
        self.assertTrue(s.get_previous_ta().all()[0], c122)

    def test_student_get_student_applications(self):
        s = Student(username='m.w@wsu.edu', first_name='michael', last_name='w', email='m.w@wsu.edu', wsu_id='11111111', major='Computer Science', gpa='4.0', graduation='Spring 2023')
        f = Faculty(username='a.b@wsu.edu', first_name='a', last_name='b', email='a.b@wsu.edu', wsu_id='22222222')
        c122 = Course(course_num='122', course_prefix='CptS', title='Program Design and Development C/C++')
        db.session.add(s)
        db.session.add(f)
        db.session.add(c122)
        db.session.commit()
        t122 = Taposition(semester='Spring', year='2023', minGPA=3.0, minGrade='B', TAExperience=False, ta_needed=5, ta_filled=0, faculty_id=f.id, course_id=c122.id)
        db.session.add(t122)
        db.session.commit()
        s_a122 = Application(grade_earned='A', student_id=s.id, semester_taken='Spring', semester_applying='Spring', year_taken='2020', year_applying='2023', status=1, position_id=t122.id)
        db.session.add(s_a122)
        db.session.commit()
        self.assertTrue(s.get_student_applications(), s_a122)

        c223 = Course(course_num='223', course_prefix='CptS', title='Advanced Data Structures')
        t223 = Taposition(semester='Spring', year='2023', minGPA=3.0, minGrade='B', TAExperience=False, ta_needed=5, ta_filled=0, faculty_id=f.id, course_id=c223.id)
        s_a223 = Application(grade_earned='A', student_id=s.id, semester_taken='Spring', semester_applying='Spring', year_taken='2020', year_applying='2023', status=1, position_id=t223.id)
        db.session.add(c223)
        db.session.add(t223)
        db.session.add(s_a223)
        db.session.commit()
        self.assertTrue(s.get_student_applications(), [t122, t223])
        db.drop_all()

    def test_student_get_studentid(self):
        self.setUp()
        s = Student(username='m.w@wsu.edu', first_name='michael', last_name='w', email='m.w@wsu.edu', wsu_id='11111111', major='Computer Science', gpa='4.0', graduation='Spring 2023')
        db.session.add(s)
        db.session.commit()
        self.assertTrue(s.id, s.get_studentid())

    def test_student_remove_coursetaken(self):
        s = Student(username='m.w@wsu.edu', first_name='michael', last_name='w', email='m.w@wsu.edu', wsu_id='11111111', major='Computer Science', gpa='4.0', graduation='Spring 2023')
        c122 = Course(course_num='122', course_prefix='CptS', title='Program Design and Development C/C++')
        db.session.add(s)
        db.session.add(c122)
        db.session.commit()
        s_c122 = Coursestaken(student_id=s.id, course_id=c122.id, grade_earned='A')
        db.session.add(s_c122)
        db.session.commit()
        prev_taken = Coursestaken.query.filter_by(student_id=s.id).filter_by(course_id=c122.id).first()
        self.assertTrue(prev_taken, s_c122)
        
        s.remove_coursetaken(c122.id)
        db.session.commit()
        previous_taken = Coursestaken.query.filter_by(student_id=s.id).filter_by(course_id=c122.id).count()
        self.assertTrue(previous_taken == 0)

    def test_student_remove_prevta(self):
        s = Student(username='m.w@wsu.edu', first_name='michael', last_name='w', email='m.w@wsu.edu', wsu_id='11111111', major='Computer Science', gpa='4.0', graduation='Spring 2023')
        c122 = Course(course_num='122', course_prefix='CptS', title='Program Design and Development C/C++')
        db.session.add(s)
        db.session.add(c122)
        db.session.commit()
        s.prevta.append(c122)
        db.session.commit()

        previous_ta_courses = s.get_previous_ta().first()
        self.assertEqual(c122, previous_ta_courses)
        s.remove_prevta(c122.id)
        db.session.commit()
        previous_ta_courses = s.get_previous_ta().count()
        self.assertTrue(previous_ta_courses == 0)
    
    def test_faculty_get_ta_positions(self):
        f = Faculty(username='a.b@wsu.edu', first_name='a', last_name='b', email='a.b@wsu.edu', wsu_id='22222222')
        c122 = Course(course_num='122', course_prefix='CptS', title='Program Design and Development C/C++')
        t122 = Taposition(semester='Spring', year='2023', minGPA=3.0, minGrade='B', TAExperience=False, ta_needed=5, ta_filled=0, faculty_id=f.id, course_id=c122.id)
        c223 = Course(course_num='223', course_prefix='CptS', title='Advanced Data Structures')
        t223 = Taposition(semester='Spring', year='2023', minGPA=3.0, minGrade='B', TAExperience=False, ta_needed=5, ta_filled=0, faculty_id=f.id, course_id=c223.id)
        self.assertTrue(f.get_ta_positions(), [t122, t223])
    
    def test_taposition_get_appications(self):
        s1 = Student(username='m.w@wsu.edu', first_name='michael', last_name='w', email='m.w@wsu.edu', wsu_id='11111111', major='Computer Science', gpa='4.0', graduation='Spring 2023')
        s2 = Student(username='d.e@wsu.edu', first_name='daniel', last_name='e', email='d.e@wsu.edu', wsu_id='33333333', major='Computer Science', gpa='4.0', graduation='Fall 2023')
        f = Faculty(username='a.b@wsu.edu', first_name='a', last_name='b', email='a.b@wsu.edu', wsu_id='22222222')
        c122 = Course(course_num='122', course_prefix='CptS', title='Program Design and Development C/C++')
        db.session.add(s1)
        db.session.add(s2)
        db.session.add(f)
        db.session.add(c122)
        db.session.commit()
        t122 = Taposition(semester='Spring', year='2023', minGPA=3.0, minGrade='B', TAExperience=False, ta_needed=5, ta_filled=0, faculty_id=f.id, course_id=c122.id)
        db.session.add(t122)
        db.session.commit()
        s1_a122 = Application(grade_earned='A', student_id=s1.id, semester_taken='Spring', semester_applying='Spring', year_taken='2020', year_applying='2023', status=1, position_id=t122.id)
        s2_a122 = Application(grade_earned='B', student_id=s2.id, semester_taken='Spring', semester_applying='Spring', year_taken='2020', year_applying='2023', status=1, position_id=t122.id)
        db.session.add(s1_a122)
        db.session.add(s2_a122)
        db.session.commit()
        self.assertTrue(t122.get_applications(), [s1_a122, s2_a122])
        db.drop_all()

    def test_course_get_positions(self):
        f = Faculty(username='a.b@wsu.edu', first_name='a', last_name='b', email='a.b@wsu.edu', wsu_id='22222222')
        c122 = Course(course_num='122', course_prefix='CptS', title='Program Design and Development C/C++')
        c223 = Course(course_num='223', course_prefix='CptS', title='Advanced Data Structures')
        db.session.add(f)
        db.session.add(c122)
        db.session.add(c223)
        db.session.commit()
        t122 = Taposition(semester='Spring', year='2023', minGPA=3.0, minGrade='B', TAExperience=False, ta_needed=5, ta_filled=0, faculty_id=f.id, course_id=c122.id)
        t223 = Taposition(semester='Spring', year='2023', minGPA=3.0, minGrade='B', TAExperience=False, ta_needed=5, ta_filled=0, faculty_id=f.id, course_id=c223.id)
        db.session.add(t122)
        db.session.add(t223)
        db.session.commit()
        self.assertTrue(c122.get_positions(), t122)
        self.assertTrue(c223.get_positions(), t223)


if __name__ == '__main__':
    unittest.main(verbosity=2)