from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy.orm import Session
from datetime import date

from .database import engine
from .models import Student, Course, Grade


api_bp = Blueprint("api", __name__, url_prefix="/api")

def get_current_user():
    """
    Get role and email from the JWT token.
    """
    claims = get_jwt()

    return {
        "role": claims.get("role"),
        "email": claims.get("email")
    }


def admin_required():
    """
    Check whether logged-in user is an admin.
    """
    user = get_current_user()

    if user["role"] != "admin":
        return False

    return True

@api_bp.route("/students", methods=["GET"])
@jwt_required()
def get_students():

    search = request.args.get("search")
    current_user = get_current_user()

    with Session(engine) as session:

        # Student can only see their own record
        if current_user["role"] == "student":

            students = session.query(Student).filter_by(
                email=current_user["email"]
            ).all()

        else:

            if search:
                students = session.query(Student).filter(
                    Student.name.like(f"%{search}%")
                ).all()
            else:
                students = session.query(Student).all()

        result = []

        for student in students:
            result.append({
                "id": student.id,
                "name": student.name,
                "email": student.email
            })

    return jsonify(result), 200


@api_bp.route("/students", methods=["POST"])
@jwt_required()
def create_student_api():

    if not admin_required():
        return jsonify({
            "error": "Admin access required"
        }), 403

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "JSON body is required"
        }), 400

    name = data.get("name")
    email = data.get("email")

    if not name or not email:
        return jsonify({
            "error": "name and email are required"
        }), 400

    with Session(engine) as session:

        existing = session.query(Student).filter_by(
            email=email
        ).first()

        if existing:
            return jsonify({
                "error": "Email already exists"
            }), 409

        student = Student(
            name=name,
            email=email
        )

        session.add(student)
        session.commit()

        return jsonify({
            "message": "Student created successfully",
            "student": {
                "id": student.id,
                "name": student.name,
                "email": student.email
            }
        }), 201


@api_bp.route("/students/<int:id>", methods=["GET"])
@jwt_required()
def get_student_api(id):

    current_user = get_current_user()

    with Session(engine) as session:

        student = session.query(Student).filter_by(
            id=id
        ).first()

        if not student:
            return jsonify({
                "error": "Student not found"
            }), 404

        # Student can only view their own record
        if current_user["role"] == "student":
            if student.email != current_user["email"]:
                return jsonify({
                    "error": "You can only view your own data"
                }), 403

        return jsonify({
            "id": student.id,
            "name": student.name,
            "email": student.email
        }), 200


@api_bp.route("/students/<int:id>", methods=["PUT"])
@jwt_required()
def update_student_api(id):

    if not admin_required():
        return jsonify({
            "error": "Admin access required"
        }), 403

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "JSON body is required"
        }), 400

    with Session(engine) as session:

        student = session.query(Student).filter_by(
            id=id
        ).first()

        if not student:
            return jsonify({
                "error": "Student not found"
            }), 404

        name = data.get("name")
        email = data.get("email")

        if not name or not email:
            return jsonify({
                "error": "name and email are required for PUT"
            }), 400

        student.name = name
        student.email = email

        session.commit()

        return jsonify({
            "message": "Student updated successfully"
        }), 200


@api_bp.route("/students/<int:id>", methods=["PATCH"])
@jwt_required()
def patch_student_api(id):

    if not admin_required():
        return jsonify({
            "error": "Admin access required"
        }), 403

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "JSON body is required"
        }), 400

    with Session(engine) as session:

        student = session.query(Student).filter_by(
            id=id
        ).first()

        if not student:
            return jsonify({
                "error": "Student not found"
            }), 404

        if "name" in data:
            student.name = data["name"]

        if "email" in data:
            student.email = data["email"]

        session.commit()

        return jsonify({
            "message": "Student partially updated"
        }), 200


@api_bp.route("/students/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_student_api(id):

    if not admin_required():
        return jsonify({
            "error": "Admin access required"
        }), 403

    with Session(engine) as session:

        student = session.query(Student).filter_by(
            id=id
        ).first()

        if not student:
            return jsonify({
                "error": "Student not found"
            }), 404

        grades = session.query(Grade).filter_by(
            student_id=id
        ).all()

        for grade in grades:
            session.delete(grade)

        session.delete(student)
        session.commit()

        return jsonify({
            "message": "Student deleted successfully"
        }), 200

@api_bp.route("/courses", methods=["GET"])
@jwt_required()
def get_courses():

    with Session(engine) as session:

        courses = session.query(Course).all()

        result = []

        for course in courses:
            result.append({
                "id": course.id,
                "name": course.name,
                "code": course.code
            })

    return jsonify(result), 200


@api_bp.route("/courses", methods=["POST"])
@jwt_required()
def create_course_api():

    if not admin_required():
        return jsonify({
            "error": "Admin access required"
        }), 403

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "JSON body is required"
        }), 400

    name = data.get("name")
    code = data.get("code")

    if not name or not code:
        return jsonify({
            "error": "name and code are required"
        }), 400

    with Session(engine) as session:

        existing = session.query(Course).filter_by(
            code=code
        ).first()

        if existing:
            return jsonify({
                "error": "Course code already exists"
            }), 409

        course = Course(
            name=name,
            code=code
        )

        session.add(course)
        session.commit()

        return jsonify({
            "message": "Course created successfully",
            "course": {
                "id": course.id,
                "name": course.name,
                "code": course.code
            }
        }), 201


@api_bp.route("/courses/<int:id>", methods=["GET"])
@jwt_required()
def get_course_api(id):

    with Session(engine) as session:

        course = session.query(Course).filter_by(
            id=id
        ).first()

        if not course:
            return jsonify({
                "error": "Course not found"
            }), 404

        return jsonify({
            "id": course.id,
            "name": course.name,
            "code": course.code
        }), 200


@api_bp.route("/courses/<int:id>", methods=["PUT"])
@jwt_required()
def update_course_api(id):

    if not admin_required():
        return jsonify({
            "error": "Admin access required"
        }), 403

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "JSON body is required"
        }), 400

    with Session(engine) as session:

        course = session.query(Course).filter_by(
            id=id
        ).first()

        if not course:
            return jsonify({
                "error": "Course not found"
            }), 404

        if not data.get("name") or not data.get("code"):
            return jsonify({
                "error": "name and code are required"
            }), 400

        course.name = data["name"]
        course.code = data["code"]

        session.commit()

        return jsonify({
            "message": "Course updated successfully"
        }), 200


@api_bp.route("/courses/<int:id>", methods=["PATCH"])
@jwt_required()
def patch_course_api(id):

    if not admin_required():
        return jsonify({
            "error": "Admin access required"
        }), 403

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "JSON body is required"
        }), 400

    with Session(engine) as session:

        course = session.query(Course).filter_by(
            id=id
        ).first()

        if not course:
            return jsonify({
                "error": "Course not found"
            }), 404

        if "name" in data:
            course.name = data["name"]

        if "code" in data:
            course.code = data["code"]

        session.commit()

        return jsonify({
            "message": "Course partially updated"
        }), 200


@api_bp.route("/courses/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_course_api(id):

    if not admin_required():
        return jsonify({
            "error": "Admin access required"
        }), 403

    with Session(engine) as session:

        course = session.query(Course).filter_by(
            id=id
        ).first()

        if not course:
            return jsonify({
                "error": "Course not found"
            }), 404

        grades = session.query(Grade).filter_by(
            course_id=id
        ).all()

        for grade in grades:
            session.delete(grade)

@api_bp.route("/grades", methods=["GET"])
@jwt_required()
def get_grades():

    current_user = get_current_user()

    with Session(engine) as session:

        if current_user["role"] == "student":

            student = session.query(Student).filter_by(
                email=current_user["email"]
            ).first()

            if not student:
                return jsonify([]), 200

            grades = session.query(Grade).filter_by(
                student_id=student.id
            ).all()

        else:
            grades = session.query(Grade).all()

        result = []

        for grade in grades:
            result.append({
                "id": grade.id,
                "student_id": grade.student_id,
                "course_id": grade.course_id,
                "score": grade.score,
                "date": str(grade.date)
            })

    return jsonify(result), 200


@api_bp.route("/grades", methods=["POST"])
@jwt_required()
def create_grade_api():

    if not admin_required():
        return jsonify({
            "error": "Admin access required"
        }), 403

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "JSON body is required"
        }), 400

    required = ["student_id", "course_id", "score", "date"]

    for field in required:
        if field not in data:
            return jsonify({
                "error": f"{field} is required"
            }), 400

    try:
        student_id = int(data["student_id"])
        course_id = int(data["course_id"])
        score = float(data["score"])
        grade_date = date.fromisoformat(data["date"])
    except (ValueError, TypeError):
        return jsonify({
            "error": "Invalid student_id, course_id, score or date"
        }), 400

    if score < 0 or score > 100:
        return jsonify({
            "error": "Score must be between 0 and 100"
        }), 400

    with Session(engine) as session:

        student = session.query(Student).filter_by(
            id=student_id
        ).first()

        course = session.query(Course).filter_by(
            id=course_id
        ).first()

        if not student:
            return jsonify({
                "error": "Student not found"
            }), 404

        if not course:
            return jsonify({
                "error": "Course not found"
            }), 404

        grade = Grade(
            student_id=student_id,
            course_id=course_id,
            score=score,
            date=grade_date
        )

        session.add(grade)
        session.commit()

        return jsonify({
            "message": "Grade created successfully",
            "grade_id": grade.id
        }), 201


@api_bp.route("/grades/<int:id>", methods=["GET"])
@jwt_required()
def get_grade_api(id):

    current_user = get_current_user()

    with Session(engine) as session:

        grade = session.query(Grade).filter_by(
            id=id
        ).first()

        if not grade:
            return jsonify({
                "error": "Grade not found"
            }), 404

        if current_user["role"] == "student":

            student = session.query(Student).filter_by(
                id=grade.student_id
            ).first()

            if not student or student.email != current_user["email"]:
                return jsonify({
                    "error": "You can only view your own data"
                }), 403

        return jsonify({
            "id": grade.id,
            "student_id": grade.student_id,
            "course_id": grade.course_id,
            "score": grade.score,
            "date": str(grade.date)
        }), 200


@api_bp.route("/grades/<int:id>", methods=["PUT"])
@jwt_required()
def update_grade_api(id):

    if not admin_required():
        return jsonify({
            "error": "Admin access required"
        }), 403

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "JSON body is required"
        }), 400

    try:
        student_id = int(data["student_id"])
        course_id = int(data["course_id"])
        score = float(data["score"])
        grade_date = date.fromisoformat(data["date"])
    except (KeyError, ValueError, TypeError):
        return jsonify({
            "error": "student_id, course_id, score and date are required"
        }), 400

    if score < 0 or score > 100:
        return jsonify({
            "error": "Score must be between 0 and 100"
        }), 400

    with Session(engine) as session:

        grade = session.query(Grade).filter_by(
            id=id
        ).first()

        if not grade:
            return jsonify({
                "error": "Grade not found"
            }), 404

        student = session.query(Student).filter_by(
            id=student_id
        ).first()

        course = session.query(Course).filter_by(
            id=course_id
        ).first()

        if not student:
            return jsonify({
                "error": "Student not found"
            }), 404

        if not course:
            return jsonify({
                "error": "Course not found"
            }), 404

        grade.student_id = student_id
        grade.course_id = course_id
        grade.score = score
        grade.date = grade_date

        session.commit()

        return jsonify({
            "message": "Grade updated successfully"
        }), 200


@api_bp.route("/grades/<int:id>", methods=["PATCH"])
@jwt_required()
def patch_grade_api(id):

    if not admin_required():
        return jsonify({
            "error": "Admin access required"
        }), 403

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "JSON body is required"
        }), 400

    with Session(engine) as session:

        grade = session.query(Grade).filter_by(
            id=id
        ).first()

        if not grade:
            return jsonify({
                "error": "Grade not found"
            }), 404

        if "student_id" in data:
            student_id = int(data["student_id"])

            student = session.query(Student).filter_by(
                id=student_id
            ).first()

            if not student:
                return jsonify({
                    "error": "Student not found"
                }), 404

            grade.student_id = student_id

        if "course_id" in data:
            course_id = int(data["course_id"])

            course = session.query(Course).filter_by(
                id=course_id
            ).first()

            if not course:
                return jsonify({
                    "error": "Course not found"
                }), 404

            grade.course_id = course_id

        if "score" in data:
            try:
                score = float(data["score"])
            except (ValueError, TypeError):
                return jsonify({
                    "error": "Invalid score"
                }), 400

            if score < 0 or score > 100:
                return jsonify({
                    "error": "Score must be between 0 and 100"
                }), 400

            grade.score = score

        if "date" in data:
            try:
                grade.date = date.fromisoformat(data["date"])
            except (ValueError, TypeError):
                return jsonify({
                    "error": "Invalid date"
                }), 400

        session.commit()

        return jsonify({
            "message": "Grade partially updated"
        }), 200


@api_bp.route("/grades/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_grade_api(id):

    if not admin_required():
        return jsonify({
            "error": "Admin access required"
        }), 403

    with Session(engine) as session:

        grade = session.query(Grade).filter_by(
            id=id
        ).first()

        if not grade:
            return jsonify({
                "error": "Grade not found"
            }), 404

        session.delete(grade)
        session.commit()

        return jsonify({
            "message": "Grade deleted successfully"
        }), 200