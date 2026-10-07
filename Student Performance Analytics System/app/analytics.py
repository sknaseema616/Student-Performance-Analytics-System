from flask import (
    Blueprint,
    render_template,
    request,
    send_file,
    redirect,
    url_for,
    flash
)

from flask_jwt_extended import (
    jwt_required,
    get_jwt
)

import pandas as pd
import numpy as np

from io import (
    BytesIO,
    StringIO
)

from datetime import date

from app.database import SessionLocal

from app.models import (
    Student,
    Course,
    Grade
)


analytics_bp = Blueprint(
    "analytics",
    __name__,
    url_prefix="/analytics"
)


def get_grade_dataframe(session):

    grades = (
        session.query(Grade)
        .all()
    )

    rows = []

    for grade in grades:

        student = (
            session.query(Student)
            .filter_by(
                id=grade.student_id
            )
            .first()
        )

        course = (
            session.query(Course)
            .filter_by(
                id=grade.course_id
            )
            .first()
        )

        if not student or not course:
            continue

        rows.append({
            "grade_id": grade.id,
            "student_id": student.id,
            "student_name": student.name,
            "student_email": student.email,
            "course_id": course.id,
            "course_name": course.name,
            "course_code": course.code,
            "score": float(grade.score),
            "date": grade.date
        })

    return pd.DataFrame(rows)


def apply_filters(
    df,
    selected_course=None,
    selected_student=None
):

    if df.empty:
        return df

    if selected_course:

        df = df[
            df["course_id"].astype(str)
            == str(selected_course)
        ]

    if selected_student:

        df = df[
            df["student_id"].astype(str)
            == str(selected_student)
        ]

    return df


@analytics_bp.route(
    "",
    methods=["GET"]
)
@analytics_bp.route(
    "/",
    methods=["GET"]
)
@jwt_required()
def dashboard():

    claims = get_jwt()

    role = claims.get(
        "role",
        ""
    ).lower()

    with SessionLocal() as session:

        df = get_grade_dataframe(
            session
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

        if role == "student":

            email = claims.get(
                "email"
            )

            df = df[
                df["student_email"]
                == email
            ]

            student = (
                session.query(Student)
                .filter_by(email=email)
                .first()
            )

            if student:

                students = [student]

            else:

                students = []

    selected_course = request.args.get(
        "course"
    )

    selected_student = request.args.get(
        "student"
    )

    if role == "student":

        selected_student = ""

    df = apply_filters(
        df,
        selected_course,
        selected_student
    )

    overall_mean = 0
    overall_median = 0
    overall_std = 0

    if not df.empty:

        scores = pd.to_numeric(
            df["score"],
            errors="coerce"
        ).dropna()

        if not scores.empty:

            overall_mean = round(
                float(np.mean(scores)),
                2
            )

            overall_median = round(
                float(np.median(scores)),
                2
            )

            overall_std = round(
                float(np.std(scores)),
                2
            )

    course_averages = []

    if not df.empty:

        course_group = (
            df.groupby(
                [
                    "course_id",
                    "course_name",
                    "course_code"
                ]
            )["score"]
            .mean()
            .reset_index()
        )

        course_group["average"] = (
            course_group["score"]
            .round(2)
        )

        course_group = course_group.sort_values(
            "average",
            ascending=False
        )

        course_averages = (
            course_group
            .to_dict("records")
        )

    rankings = []

    if not df.empty:

        ranking_df = (
            df.groupby(
                [
                    "student_id",
                    "student_name"
                ]
            )["score"]
            .mean()
            .reset_index()
        )

        ranking_df = ranking_df.sort_values(
            "score",
            ascending=False
        )

        ranking_df["rank"] = (
            ranking_df["score"]
            .rank(
                method="dense",
                ascending=False
            )
            .astype(int)
        )

        ranking_df["average"] = (
            ranking_df["score"]
            .round(2)
        )

        rankings = (
            ranking_df
            .to_dict("records")
        )

    return render_template(
        "analytics/dashboard.html",
        students=students,
        courses=courses,
        course_averages=course_averages,
        rankings=rankings,
        overall_mean=overall_mean,
        overall_median=overall_median,
        overall_std=overall_std,
        selected_course=selected_course,
        selected_student=selected_student,
        role=role
    )


@analytics_bp.route(
    "/export/csv"
)
@jwt_required()
def export_csv():

    claims = get_jwt()

    role = claims.get(
        "role",
        ""
    ).lower()

    with SessionLocal() as session:

        df = get_grade_dataframe(
            session
        )

    if role == "student":

        df = df[
            df["student_email"]
            == claims.get("email")
        ]

    selected_course = request.args.get(
        "course"
    )

    selected_student = request.args.get(
        "student"
    )

    if role == "student":

        selected_student = None

    df = apply_filters(
        df,
        selected_course,
        selected_student
    )

    output = StringIO()

    df.to_csv(
        output,
        index=False
    )

    output.seek(0)

    return send_file(
        BytesIO(
            output.getvalue().encode(
                "utf-8"
            )
        ),
        mimetype="text/csv",
        as_attachment=True,
        download_name=(
            "student_performance_report.csv"
        )
    )


@analytics_bp.route(
    "/export/excel"
)
@jwt_required()
def export_excel():

    claims = get_jwt()

    role = claims.get(
        "role",
        ""
    ).lower()

    with SessionLocal() as session:

        df = get_grade_dataframe(
            session
        )

    if role == "student":

        df = df[
            df["student_email"]
            == claims.get("email")
        ]

    selected_course = request.args.get(
        "course"
    )

    selected_student = request.args.get(
        "student"
    )

    if role == "student":

        selected_student = None

    df = apply_filters(
        df,
        selected_course,
        selected_student
    )

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name="Performance"
        )

        if not df.empty:

            course_average = (
                df.groupby(
                    [
                        "course_name",
                        "course_code"
                    ]
                )["score"]
                .mean()
                .round(2)
                .reset_index()
            )

            course_average.to_excel(
                writer,
                index=False,
                sheet_name="Course Average"
            )

            ranking = (
                df.groupby(
                    ["student_name"]
                )["score"]
                .mean()
                .round(2)
                .reset_index()
                .sort_values(
                    "score",
                    ascending=False
                )
            )

            ranking.to_excel(
                writer,
                index=False,
                sheet_name="Student Ranking"
            )

    output.seek(0)

    return send_file(
        output,
        mimetype=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        as_attachment=True,
        download_name=(
            "student_performance_report.xlsx"
        )
    )


@analytics_bp.route(
    "/upload",
    methods=["POST"]
)
@jwt_required()
def upload_csv():

    claims = get_jwt()

    if (
        claims.get("role", "").lower()
        != "admin"
    ):

        return (
            "Access denied. Admins only.",
            403
        )

    file = request.files.get(
        "file"
    )

    if not file or not file.filename:

        flash(
            "Please select a CSV file.",
            "danger"
        )

        return redirect(
            url_for(
                "analytics.dashboard"
            )
        )

    if not file.filename.lower().endswith(
        ".csv"
    ):

        flash(
            "Only CSV files are allowed.",
            "danger"
        )

        return redirect(
            url_for(
                "analytics.dashboard"
            )
        )

    try:
        df = pd.read_csv(
            file
        )
        required_columns = {
            "student_id",
            "course_id",
            "score",
            "date"
        }
        missing = (
            required_columns
            - set(df.columns)
        )
        if missing:
            raise ValueError(
                "Missing columns: "
                + ", ".join(
                    sorted(missing)
                )
            )
        df["student_id"] = pd.to_numeric(
            df["student_id"],
            errors="coerce"
        )
        df["course_id"] = pd.to_numeric(
            df["course_id"],
            errors="coerce"
        )
        df["score"] = pd.to_numeric(
            df["score"],
            errors="coerce"
        )
        df["date"] = pd.to_datetime(
            df["date"],
            errors="coerce"
        )
        if df[
            [
                "student_id",
                "course_id",
                "score",
                "date"
            ]
        ].isna().any().any():
            raise ValueError(
                "CSV contains invalid or empty values."
            )
        if (
            (df["score"] < 0)
            |
            (df["score"] > 100)
        ).any():
            raise ValueError(
                "Scores must be between 0 and 100."
            )
        with SessionLocal() as session:
            for _, row in df.iterrows():
                student_id = int(
                    row["student_id"]
                )
                course_id = int(
                    row["course_id"]
                )
                score = float(
                    row["score"]
                )
                grade_date = row[
                    "date"
                ].date()
                student = (
                    session.query(Student)
                    .filter_by(
                        id=student_id
                    )
                    .first()
                )
                course = (
                    session.query(Course)
                    .filter_by(
                        id=course_id
                    )
                    .first()
                )
                if not student:
                    raise ValueError(
                        f"Student ID {student_id} "
                        "does not exist."
                    )
                if not course:
                    raise ValueError(
                        f"Course ID {course_id} "
                        "does not exist."
                    )
                existing = (
                    session.query(Grade)
                    .filter_by(
                        student_id=student_id,
                        course_id=course_id,
                        date=grade_date
                    )
                    .first()
                )
                if existing:
                    existing.score = score
                else:
                    grade = Grade(
                        student_id=student_id,
                        course_id=course_id,
                        score=score,
                        date=grade_date
                    )
                    session.add(grade)
            session.commit()
        flash(
            f"{len(df)} grades uploaded successfully.",
            "success"
        )
    except Exception as error:

        flash(
            f"Upload failed: {error}",
            "danger"
        )
    return redirect(
        url_for(
            "analytics.dashboard"
        )
    )