from sqlalchemy import Column, Float, Integer, String

from .database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(String(20), primary_key=True, comment="学号")
    name = Column(String(50), nullable=False, index=True, comment="姓名")
    class_name = Column(String(50), nullable=False, index=True, comment="班级")
    age = Column(Integer, default=0, comment="年龄")
    score = Column(Float, default=0, comment="成绩")
