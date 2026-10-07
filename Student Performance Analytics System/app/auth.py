from flask import (
    Blueprint,
    request,
    render_template,
    redirect,
    url_for,
    flash,
    jsonify
)

from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
    set_access_cookies,
    set_refresh_cookies,
    unset_jwt_cookies
)

from werkzeug.security import check_password_hash

from app.database import SessionLocal
from app.models import User


auth_bp = Blueprint(
    "auth",
    __name__
)


@auth_bp.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "GET":

        return render_template(
            "login.html"
        )

    if request.is_json:

        data = request.get_json() or {}

        email = data.get(
            "email",
            ""
        ).strip()

        password = data.get(
            "password",
            ""
        )

    else:

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

    if not email or not password:

        if request.is_json:

            return jsonify({
                "error": "Email and password are required"
            }), 400

        flash(
            "Email and password are required.",
            "danger"
        )

        return render_template(
            "login.html"
        )

    with SessionLocal() as session:

        user = (
            session.query(User)
            .filter_by(email=email)
            .first()
        )

        if not user:

            if request.is_json:

                return jsonify({
                    "error": "Invalid email or password"
                }), 401

            flash(
                "Invalid email or password.",
                "danger"
            )

            return render_template(
                "login.html"
            )

        if not check_password_hash(
            user.password,
            password
        ):

            if request.is_json:

                return jsonify({
                    "error": "Invalid email or password"
                }), 401

            flash(
                "Invalid email or password.",
                "danger"
            )

            return render_template(
                "login.html"
            )

        additional_claims = {
            "role": user.role,
            "email": user.email,
            "name": user.name
        }

        access_token = create_access_token(
            identity=str(user.id),
            additional_claims=additional_claims
        )

        refresh_token = create_refresh_token(
            identity=str(user.id),
            additional_claims=additional_claims
        )

        if request.is_json:

            return jsonify({
                "message": "Login successful",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "role": user.role
                }
            }), 200

        response = redirect(
            url_for("routes.students")
        )

        set_access_cookies(
            response,
            access_token
        )

        set_refresh_cookies(
            response,
            refresh_token
        )

        return response


@auth_bp.route(
    "/refresh",
    methods=["POST"]
)
@jwt_required(
    refresh=True
)
def refresh():

    identity = get_jwt_identity()

    claims = get_jwt()

    new_access_token = create_access_token(
        identity=identity,
        additional_claims={
            "role": claims.get("role"),
            "email": claims.get("email"),
            "name": claims.get("name")
        }
    )

    response = jsonify({
        "message": "Access token refreshed successfully",
        "access_token": new_access_token
    })

    set_access_cookies(
        response,
        new_access_token
    )

    return response


@auth_bp.route(
    "/logout",
    methods=["GET", "POST"]
)
def logout():

    response = redirect(
        url_for("auth.login")
    )

    unset_jwt_cookies(
        response
    )

    flash(
        "You have been logged out.",
        "success"
    )

    return response