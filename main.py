from app import create_app, db
from app.Model.models import Course, Student, Faculty

app = create_app()

@app.before_first_request
def initDB(*args, **kwargs):
    db.create_all()
    if Course.query.count() == 0:
        majors = [{'course_num': '121', 'course_prefix':'CptS', 'title':'Program Design and Development C/C++'},
                  {'course_num': '122', 'course_prefix':'CptS', 'title':'Data Structures C/C++'},
                  {'course_num': '223', 'course_prefix':'CptS', 'title':'Advanced Data Structures'},
                  {'course_num': '317', 'course_prefix':'CptS', 'title':'Automata and Formal Lanugages'},
                  {'course_num': '322', 'course_prefix':'CptS', 'title':'Software Engineering Principles I'},
                  {'course_num': '214', 'course_prefix':'EE', 'title':'Design of Logic Circuits'},
                  {'course_num': '331', 'course_prefix':'EE', 'title':'Electromagnetic Fields and Waves'},
                  {'course_num': '351', 'course_prefix':'EE', 'title':'Distributed Parameter Systems'},
                  {'course_num': '116', 'course_prefix':'ME', 'title':'Engineering Computer-aided Design and Visualization'},
                  {'course_num': '241', 'course_prefix':'ME', 'title':'Engineering Computations'},
                  {'course_num': '301', 'course_prefix':'ME', 'title':'Fundamentals of Thermodynamics'}]

        for m in majors:
            db.session.add(Course(course_num=m['course_num'], course_prefix=m['course_prefix'], title=m['title']))
        db.session.commit()
    
if __name__ == "__main__":
    app.run(debug=True)