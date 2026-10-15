import os

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import distinct, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Student
from .schemas import ClassesOut, StatsOut, StudentCreate, StudentOut, StudentUpdate

app = FastAPI(title="学生管理系统 API", version="1.0.0")

origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

SAMPLE_DATA = [
    {"id": "20260101", "name": "陈晓", "class_name": "三年级 1 班", "age": 9, "score": 95},
    {"id": "20260102", "name": "李思远", "class_name": "三年级 1 班", "age": 9, "score": 88},
    {"id": "20260103", "name": "王雨桐", "class_name": "三年级 2 班", "age": 10, "score": 72},
    {"id": "20260104", "name": "张子墨", "class_name": "三年级 2 班", "age": 9, "score": 61},
    {"id": "20260105", "name": "刘一诺", "class_name": "四年级 1 班", "age": 11, "score": 99},
    {"id": "20260106", "name": "赵可欣", "class_name": "四年级 1 班", "age": 10, "score": 45},
]

SORTABLE = {
    "name": Student.name,
    "className": Student.class_name,
    "age": Student.age,
    "score": Student.score,
}


@app.on_event("startup")
def startup():
    # 建表；表为空时写入示例数据，方便演示
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        if db.scalar(select(func.count()).select_from(Student)) == 0:
            db.add_all(Student(**row) for row in SAMPLE_DATA)
            db.commit()
    finally:
        db.close()


@app.get("/api/students", response_model=list[StudentOut])
def list_students(
    q: str = Query("", description="按姓名/学号/班级模糊搜索"),
    class_name: str = Query("", alias="className", description="按班级精确筛选"),
    sort_by: str = Query("name", alias="sortBy"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    stmt = select(Student)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(Student.name.like(like), Student.id.like(like), Student.class_name.like(like))
        )
    if class_name:
        stmt = stmt.where(Student.class_name == class_name)

    column = SORTABLE.get(sort_by, Student.name)
    stmt = stmt.order_by(column.asc() if order == "asc" else column.desc())
    return db.scalars(stmt).all()


@app.post("/api/students", response_model=StudentOut, status_code=201)
def create_student(payload: StudentCreate, db: Session = Depends(get_db)):
    student = Student(**payload.model_dump())
    db.add(student)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="学号已存在")
    db.refresh(student)
    return student


@app.put("/api/students/{student_id}", response_model=StudentOut)
def update_student(student_id: str, payload: StudentUpdate, db: Session = Depends(get_db)):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    for key, value in payload.model_dump().items():
        setattr(student, key, value)
    db.commit()
    db.refresh(student)
    return student


@app.delete("/api/students/{student_id}", status_code=204)
def delete_student(student_id: str, db: Session = Depends(get_db)):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    db.delete(student)
    db.commit()


@app.get("/api/classes", response_model=ClassesOut)
def list_classes(db: Session = Depends(get_db)):
    rows = db.scalars(select(distinct(Student.class_name)).order_by(Student.class_name)).all()
    return {"classes": rows}


@app.get("/api/stats", response_model=StatsOut)
def get_stats(db: Session = Depends(get_db)):
    total = db.scalar(select(func.count()).select_from(Student)) or 0
    class_count = db.scalar(select(func.count(distinct(Student.class_name)))) or 0
    avg_score = db.scalar(select(func.avg(Student.score))) if total else None
    excellent = db.scalar(select(func.count()).select_from(Student).where(Student.score >= 90)) or 0
    return {
        "total": total,
        "class_count": class_count,
        "avg_score": round(float(avg_score), 1) if avg_score is not None else None,
        "excellent": excellent,
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}
