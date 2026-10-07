from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="student")

    def __repr__(self):
        return f"<User(name='{self.name}', email='{self.email}', role='{self.role}')>"


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), nullable=False, unique=True)

    grades = relationship("Grade", back_populates="student")

    def __repr__(self):
        return f"<Student(name='{self.name}', email='{self.email}')>"


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), nullable=False, unique=True)

    grades = relationship("Grade", back_populates="course")

    def __repr__(self):
        return f"<Course(name='{self.name}', code='{self.code}')>"


class Grade(Base):
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True)

    student_id = Column(
        Integer,
        ForeignKey("students.id"),
        nullable=False
    )

    course_id = Column(
        Integer,
        ForeignKey("courses.id"),
        nullable=False
    )

    score = Column(Float, nullable=False)
    date = Column(Date, nullable=False)

    student = relationship("Student", back_populates="grades")
    course = relationship("Course", back_populates="grades")

    def __repr__(self):
        return f"<Grade(student_id={self.student_id}, course_id={self.course_id}, score={self.score})>"