from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash

from app.database import engine
from app.models import User


with Session(engine) as session:

    existing_user = (
        session.query(User)
        .filter_by(email="naseema@gmail.com")
        .first()
    )

    if existing_user:
        print("Student user already exists.")

    else:
        user = User(
            name="Naseema",
            email="naseema@gmail.com",
            password=generate_password_hash("student123"),
            role="student"
        )

        session.add(user)
        session.commit()

        print("Student user created successfully.")