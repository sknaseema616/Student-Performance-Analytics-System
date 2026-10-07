from datetime import date

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify
)

from flask_jwt_extended import (
    jwt_required,
    get_jwt,
    get_jwt_identity
)

from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models import (
    Student,
    Course,
    Grade,
    User
)


routes_bp = Blueprint(
    "routes",
    __name__
)


def get_current_user():

    identity = get_jwt_identity()

    if identity is None:
        return None

    with SessionLocal() as session:

        user = (
            session.query(User)
            .filter_by(id=int(identity))
            .first()
        )

        if not user:
            return None

        session.expunge(user)

        return user


def admin_required():

    claims = get_jwt()

    return (
        claims.get("role", "").lower()
        == "admin"
    )


def get_role():

    return get_jwt().get(
        "role",
        ""
    ).lower()


def get_student_for_current_user(session):

    claims = get_jwt()

    return (
        session.query(Student)
        .filter_by(
            email=claims.get("email")
        )
        .first()
    )


# =========================================================
# HOME
# =========================================================

@routes_bp.route("/")
def home():

    return redirect(
        url_for("auth.login")
    )


# =========================================================
# STUDENTS
# =========================================================

@routes_bp.route(
    "/students",
    methods=["GET"]
)
@jwt_required()
def students():

    role = get_role()

    with SessionLocal() as session:

        if role == "student":

            student = get_student_for_current_user(
                session
            )

            students_list = (
                [student]
                if student
                else []
            )

        else:

            search = request.args.get(
                "search",
                ""
            ).strip()

            query = session.query(Student)

            if search:

                query = query.filter(
                    Student.name.ilike(
                        f"%{search}%"
                    )
                    |
                    Student.email.ilike(
                        f"%{search}%"
                    )
                )

            students_list = (
                query
                .order_by(Student.id)
                .all()
            )

        return render_template(
            "students/list.html",
            students=students_list,
            role=role
        )


@routes_bp.route(
    "/students/new",
    methods=["GET"]
)
@jwt_required()
def new_student():

    if not admin_required():

        return (
            "Access denied. Admins only.",
            403
        )

    return render_template(
        "students/new.html"
    )


@routes_bp.route(
    "/students",
    methods=["POST"]
)
@jwt_required()
def create_student():

    if not admin_required():

        return (
            "Access denied. Admins only.",
            403
        )

    name = request.form.get(
        "name",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip()

    if not name or not email:

        flash(
            "Name and email are required.",
            "danger"
        )

        return redirect(
            url_for("routes.new_student")
        )

    with SessionLocal() as session:

        existing = (
            session.query(Student)
            .filter_by(email=email)
            .first()
        )

        if existing:

            flash(
                "A student with this email already exists.",
                "danger"
            )

            return redirect(
                url_for("routes.new_student")
            )

        student = Student(
            name=name,
            email=email
        )

        session.add(student)

        try:

            session.commit()

        except IntegrityError:

            session.rollback()

            flash(
                "Student email already exists.",
                "danger"
            )

            return redirect(
                url_for("routes.new_student")
            )

    flash(
        "Student created successfully.",
        "success"
    )

    return redirect(
        url_for("routes.students")
    )


@routes_bp.route(
    "/students/<int:id>",
    methods=["GET"]
)
@jwt_required()
def student_detail(id):

    role = get_role()

    with SessionLocal() as session:

        student = (
            session.query(Student)
            .filter_by(id=id)
            .first()
        )

        if not student:

            return (
                "Student not found.",
                404
            )

        if role == "student":

            current_student = (
                get_student_for_current_user(
                    session
                )
            )

            if (
                not current_student
                or current_student.id != student.id
            ):

                return (
                    "Access denied.",
                    403
                )

        grades = (
            session.query(Grade)
            .filter_by(
                student_id=student.id
            )
            .order_by(
                Grade.date.desc()
            )
            .all()
        )

        return render_template(
            "students/detail.html",
            student=student,
            grades=grades,
            role=role
        )


@routes_bp.route(
    "/students/<int:id>/edit",
    methods=["GET"]
)
@jwt_required()
def edit_student(id):

    if not admin_required():

        return (
            "Access denied. Admins only.",
            403
        )

    with SessionLocal() as session:

        student = (
            session.query(Student)
            .filter_by(id=id)
            .first()
        )

        if not student:

            return (
                "Student not found.",
                404
            )

        return render_template(
            "students/edit.html",
            student=student
        )


@routes_bp.route(
    "/students/<int:id>",
    methods=["PUT", "PATCH"]
)
@jwt_required()
def update_student(id):

    if not admin_required():

        return (
            "Access denied. Admins only.",
            403
        )

    if request.is_json:

        data = request.get_json() or {}

    else:

        data = request.form

    with SessionLocal() as session:

        student = (
            session.query(Student)
            .filter_by(id=id)
            .first()
        )

        if not student:

            return (
                "Student not found.",
                404
            )

        if request.method == "PUT":

            name = str(
                data.get("name", "")
            ).strip()

            email = str(
                data.get("email", "")
            ).strip()

            if not name or not email:

                return (
                    "Name and email are required for PUT.",
                    400
                )

            student.name = name
            student.email = email

        elif request.method == "PATCH":

            if "name" in data:

                name = str(
                    data.get("name", "")
                ).strip()

                if not name:

                    return (
                        "Name cannot be empty.",
                        400
                    )

                student.name = name

            if "email" in data:

                email = str(
                    data.get("email", "")
                ).strip()

                if not email:

                    return (
                        "Email cannot be empty.",
                        400
                    )

                student.email = email

        try:

            session.commit()

        except IntegrityError:

            session.rollback()

            return (
                "Student email already exists.",
                409
            )

    if request.is_json:

        return jsonify({
            "message": "Student updated successfully"
        }), 200

    flash(
        "Student updated successfully.",
        "success"
    )

    return redirect(
        url_for(
            "routes.student_detail",
            id=id
        )
    )


@routes_bp.route(
    "/students/<int:id>",
    methods=["DELETE"]
)
@jwt_required()
def delete_student(id):

    if not admin_required():

        return (
            "Access denied. Admins only.",
            403
        )

    with SessionLocal() as session:

        student = (
            session.query(Student)
            .filter_by(id=id)
            .first()
        )

        if not student:

            return (
                "Student not found.",
                404
            )

        session.query(Grade).filter_by(
            student_id=student.id
        ).delete(
            synchronize_session=False
        )

        session.delete(student)

        session.commit()

    if request.is_json:

        return jsonify({
            "message": "Student deleted successfully"
        }), 200

    flash(
        "Student deleted successfully.",
        "success"
    )

    return redirect(
        url_for("routes.students")
    )


# =========================================================
# COURSES
# =========================================================

@routes_bp.route(
    "/courses",
    methods=["GET"]
)
@jwt_required()
def courses():

    role = get_role()

    with SessionLocal() as session:

        courses_list = (
            session.query(Course)
            .order_by(Course.id)
            .all()
        )

        return render_template(
            "courses/list.html",
            courses=courses_list,
            role=role
        )


@routes_bp.route(
    "/courses/new",
    methods=["GET"]
)
@jwt_required()
def new_course():

    if not admin_required():

        return (
            "Access denied. Admins only.",
            403
        )

    return render_template(
        "courses/new.html"
    )


@routes_bp.route(
    "/courses",
    methods=["POST"]
)
@jwt_required()
def create_course():

    if not admin_required():

        return (
            "Access denied. Admins only.",
            403
        )

    name = request.form.get(
        "name",
        ""
    ).strip()

    code = request.form.get(
        "code",
        ""
    ).strip().upper()

    if not name or not code:

        flash(
            "Course name and code are required.",
            "danger"
        )

        return redirect(
            url_for("routes.new_course")
        )

    with SessionLocal() as session:

        existing = (
            session.query(Course)
            .filter_by(code=code)
            .first()
        )

        if existing:

            flash(
                "Course code already exists.",
                "danger"
            )

            return redirect(
                url_for("routes.new_course")
            )

        course = Course(
            name=name,
            code=code
        )

        session.add(course)

        try:

            session.commit()

        except IntegrityError:

            session.rollback()

            flash(
                "Course code already exists.",
                "danger"
            )

            return redirect(
                url_for("routes.new_course")
            )

    flash(
        "Course created successfully.",
        "success"
    )

    return redirect(
        url_for("routes.courses")
    )


@routes_bp.route(
    "/courses/<int:id>",
    methods=["GET"]
)
@jwt_required()
def course_detail(id):

    role = get_role()

    with SessionLocal() as session:

        course = (
            session.query(Course)
            .filter_by(id=id)
            .first()
        )

        if not course:

            return (
                "Course not found.",
                404
            )

        if role == "student":

            student = (
                get_student_for_current_user(
                    session
                )
            )

            if not student:

                return (
                    "Student record not found.",
                    404
                )

            grades = (
                session.query(Grade)
                .filter_by(
                    course_id=course.id,
                    student_id=student.id
                )
                .all()
            )

        else:

            grades = (
                session.query(Grade)
                .filter_by(
                    course_id=course.id
                )
                .all()
            )

        return render_template(
            "courses/detail.html",
            course=course,
            grades=grades,
            role=role
        )


@routes_bp.route(
    "/courses/<int:id>/edit",
    methods=["GET"]
)
@jwt_required()
def edit_course(id):

    if not admin_required():

        return (
            "Access denied. Admins only.",
            403
        )

    with SessionLocal() as session:

        course = (
            session.query(Course)
            .filter_by(id=id)
            .first()
        )

        if not course:

            return (
                "Course not found.",
                404
            )

        return render_template(
            "courses/edit.html",
            course=course
        )


@routes_bp.route(
    "/courses/<int:id>",
    methods=["PUT", "PATCH"]
)
@jwt_required()
def update_course(id):

    if not admin_required():

        return (
            "Access denied. Admins only.",
            403
        )

    data = (
        request.get_json() or {}
        if request.is_json
        else request.form
    )

    with SessionLocal() as session:

        course = (
            session.query(Course)
            .filter_by(id=id)
            .first()
        )

        if not course:

            return (
                "Course not found.",
                404
            )

        if request.method == "PUT":

            name = str(
                data.get("name", "")
            ).strip()

            code = str(
                data.get("code", "")
            ).strip().upper()

            if not name or not code:

                return (
                    "Course name and code are required for PUT.",
                    400
                )

            course.name = name
            course.code = code

        else:

            if "name" in data:

                name = str(
                    data.get("name", "")
                ).strip()

                if not name:

                    return (
                        "Course name cannot be empty.",
                        400
                    )

                course.name = name

            if "code" in data:

                code = str(
                    data.get("code", "")
                ).strip().upper()

                if not code:

                    return (
                        "Course code cannot be empty.",
                        400
                    )

                course.code = code

        try:

            session.commit()

        except IntegrityError:

            session.rollback()

            return (
                "Course code already exists.",
                409
            )

    if request.is_json:

        return jsonify({
            "message": "Course updated successfully"
        }), 200

    flash(
        "Course updated successfully.",
        "success"
    )

    return redirect(
        url_for(
            "routes.course_detail",
            id=id
        )
    )


@routes_bp.route(
    "/courses/<int:id>",
    methods=["DELETE"]
)
@jwt_required()
def delete_course(id):

    if not admin_required():

        return (
            "Access denied. Admins only.",
            403
        )

    with SessionLocal() as session:

        course = (
            session.query(Course)
            .filter_by(id=id)
            .first()
        )

        if not course:

            return (
                "Course not found.",
                404
            )

        session.query(Grade).filter_by(
            course_id=course.id
        ).delete(
            synchronize_session=False
        )

        session.delete(course)

        session.commit()

    if request.is_json:

        return jsonify({
            "message": "Course deleted successfully"
        }), 200

    flash(
        "Course deleted successfully.",
        "success"
    )

    return redirect(
        url_for("routes.courses")
    )


# =========================================================
# GRADES
# =========================================================

@routes_bp.route(
    "/grades",
    methods=["GET"]
)
@jwt_required()
def grades():

    role = get_role()

    with SessionLocal() as session:

        if role == "student":

            student = (
                get_student_for_current_user(
                    session
                )
            )

            if not student:

                grades_list = []

            else:

                grades_list = (
                    session.query(Grade)
                    .filter_by(
                        student_id=student.id
                    )
                    .order_by(
                        Grade.date.desc()
                    )
                    .all()
                )

        else:

            grades_list = (
                session.query(Grade)
                .order_by(
                    Grade.date.desc()
                )
                .all()
            )

        return render_template(
            "grades/list.html",
            grades=grades_list,
            role=role
        )


@routes_bp.route(
    "/grades/new",
    methods=["GET"]
)
@jwt_required()
def new_grade():

    if not admin_required():

        return (
            "Access denied. Admins only.",
            403
        )

    with SessionLocal() as session:

        students = (
            session.query(Student)
            .order_by(Student.name)
            .all()
        )

        courses = (
            session.query(Course)
            .order_by(Course.name)
            .all()
        )

        return render_template(
            "grades/new.html",
            students=students,
            courses=courses
        )


@routes_bp.route(
    "/grades",
    methods=["POST"]
)
@jwt_required()
def create_grade():

    if not admin_required():

        return (
            "Access denied. Admins only.",
            403
        )

    student_id = request.form.get(
        "student_id"
    )

    course_id = request.form.get(
        "course_id"
    )

    score = request.form.get(
        "score"
    )

    grade_date = request.form.get(
        "date"
    )

    if not student_id or not course_id or score is None or not grade_date:

        flash(
            "Student, course, score and date are required.",
            "danger"
        )

        return redirect(
            url_for("routes.new_grade")
        )

    try:

        student_id = int(student_id)
        course_id = int(course_id)
        score = float(score)
        grade_date = date.fromisoformat(
            grade_date
        )

    except (
        ValueError,
        TypeError
    ):

        flash(
            "Invalid grade information.",
            "danger"
        )

        return redirect(
            url_for("routes.new_grade")
        )

    if score < 0 or score > 100:

        flash(
            "Score must be between 0 and 100.",
            "danger"
        )

        return redirect(
            url_for("routes.new_grade")
        )

    with SessionLocal() as session:

        student = (
            session.query(Student)
            .filter_by(id=student_id)
            .first()
        )

        course = (
            session.query(Course)
            .filter_by(id=course_id)
            .first()
        )

        if not student:

            flash(
                "Student not found.",
                "danger"
            )

            return redirect(
                url_for("routes.new_grade")
            )

        if not course:

            flash(
                "Course not found.",
                "danger"
            )

            return redirect(
                url_for("routes.new_grade")
            )

        grade = Grade(
            student_id=student_id,
            course_id=course_id,
            score=score,
            date=grade_date
        )

        session.add(grade)

        try:

            session.commit()

        except IntegrityError:

            session.rollback()

            flash(
                "Unable to create grade. Check the student, course and date.",
                "danger"
            )

            return redirect(
                url_for("routes.new_grade")
            )

    flash(
        "Grade created successfully.",
        "success"
    )

    return redirect(
        url_for("routes.grades")
    )


@routes_bp.route(
    "/grades/<int:id>",
    methods=["GET"]
)
@jwt_required()
def grade_detail(id):

    role = get_role()

    with SessionLocal() as session:

        grade = (
            session.query(Grade)
            .filter_by(id=id)
            .first()
        )

        if not grade:

            return (
                "Grade not found.",
                404
            )

        student = (
            session.query(Student)
            .filter_by(id=grade.student_id)
            .first()
        )

        course = (
            session.query(Course)
            .filter_by(id=grade.course_id)
            .first()
        )

        if role == "student":

            current_student = (
                get_student_for_current_user(
                    session
                )
            )

            if (
                not current_student
                or current_student.id
                != grade.student_id
            ):

                return (
                    "Access denied.",
                    403
                )

        return render_template(
            "grades/detail.html",
            grade=grade,
            student=student,
            course=course,
            role=role
        )


@routes_bp.route(
    "/grades/<int:id>/edit",
    methods=["GET"]
)
@jwt_required()
def edit_grade(id):

    if not admin_required():

        return (
            "Access denied. Admins only.",
            403
        )

    with SessionLocal() as session:

        grade = (
            session.query(Grade)
            .filter_by(id=id)
            .first()
        )

        if not grade:

            return (
                "Grade not found.",
                404
            )

        students = (
            session.query(Student)
            .order_by(Student.name)
            .all()
        )

        courses = (
            session.query(Course)
            .order_by(Course.name)
            .all()
        )

        return render_template(
            "grades/edit.html",
            grade=grade,
            students=students,
            courses=courses
        )


@routes_bp.route(
    "/grades/<int:id>",
    methods=["PUT", "PATCH"]
)
@jwt_required()
def update_grade(id):

    if not admin_required():

        return (
            "Access denied. Admins only.",
            403
        )

    data = (
        request.get_json() or {}
        if request.is_json
        else request.form
    )

    with SessionLocal() as session:

        grade = (
            session.query(Grade)
            .filter_by(id=id)
            .first()
        )

        if not grade:

            return (
                "Grade not found.",
                404
            )

        if request.method == "PUT":

            student_id = data.get(
                "student_id"
            )

            course_id = data.get(
                "course_id"
            )

            score = data.get(
                "score"
            )

            grade_date = data.get(
                "date"
            )

            if (
                student_id is None
                or course_id is None
                or score is None
                or not grade_date
            ):

                return (
                    "All grade fields are required for PUT.",
                    400
                )

        else:

            student_id = data.get(
                "student_id"
            )

            course_id = data.get(
                "course_id"
            )

            score = data.get(
                "score"
            )

            grade_date = data.get(
                "date"
            )

        try:

            if student_id is not None:

                student_id = int(
                    student_id
                )

                student = (
                    session.query(Student)
                    .filter_by(id=student_id)
                    .first()
                )

                if not student:

                    return (
                        "Student not found.",
                        404
                    )

                grade.student_id = student_id

            if course_id is not None:

                course_id = int(
                    course_id
                )

                course = (
                    session.query(Course)
                    .filter_by(id=course_id)
                    .first()
                )

                if not course:

                    return (
                        "Course not found.",
                        404
                    )

                grade.course_id = course_id

            if score is not None:

                score = float(score)

                if score < 0 or score > 100:

                    return (
                        "Score must be between 0 and 100.",
                        400
                    )

                grade.score = score

            if grade_date:

                grade.date = date.fromisoformat(
                    grade_date
                )

        except (
            ValueError,
            TypeError
        ):

            return (
                "Invalid grade information.",
                400
            )

        try:

            session.commit()

        except IntegrityError:

            session.rollback()

            return (
                "Unable to update grade. Check the values.",
                409
            )

    if request.is_json:

        return jsonify({
            "message": "Grade updated successfully"
        }), 200

    flash(
        "Grade updated successfully.",
        "success"
    )

    return redirect(
        url_for(
            "routes.grade_detail",
            id=id
        )
    )


@routes_bp.route(
    "/grades/<int:id>",
    methods=["DELETE"]
)
@jwt_required()
def delete_grade(id):

    if not admin_required():

        return (
            "Access denied. Admins only.",
            403
        )

    with SessionLocal() as session:

        grade = (
            session.query(Grade)
            .filter_by(id=id)
            .first()
        )

        if not grade:

            return (
                "Grade not found.",
                404
            )

        session.delete(grade)

        session.commit()

    if request.is_json:

        return jsonify({
            "message": "Grade deleted successfully"
        }), 200

    flash(
        "Grade deleted successfully.",
        "success"
    )

    return redirect(
        url_for("routes.grades")
    )