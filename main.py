from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Optional
import shelve

app = FastAPI()

class Student(BaseModel):
    name: str
    age: int
    major: str

SHELVE_DB = "students.db"

def get_all_students() -> Dict[str, Student]:
    with shelve.open(SHELVE_DB) as db:
        return dict(db)

def get_student(student_id: str) -> Student:
    with shelve.open(SHELVE_DB) as db:
        if student_id in db:
            return db[student_id]
        raise HTTPException(status_code=404, detail="Student not found")

def add_student(student: Student) -> str:
    with shelve.open(SHELVE_DB, writeback=True) as db:
        next_id = str(max([int(k) for k in db.keys()] + [0]) + 1)
        db[next_id] = student
        return next_id

def update_student(student_id: str, student: Student):
    with shelve.open(SHELVE_DB, writeback=True) as db:
        if student_id not in db:
            raise HTTPException(status_code=404, detail="Student not found")
        db[student_id] = student

def delete_student(student_id: str):
    with shelve.open(SHELVE_DB, writeback=True) as db:
        if student_id not in db:
            raise HTTPException(status_code=404, detail="Student not found")
        del db[student_id]

@app.get("/students")
def list_students(major: Optional[str] = Query(None), age: Optional[int] = Query(None)):
    students = get_all_students()
    filtered = {
        sid: s for sid, s in students.items()
        if (major is None or s.major == major) and (age is None or s.age == age)
    }
    return filtered

@app.get("/students/{student_id}")
def get_student_by_id(student_id: str):
    return get_student(student_id)

@app.post("/students")
def create_student(student: Student):
    student_id = add_student(student)
    return {"id": student_id, "student": student}

@app.put("/students/{student_id}")
def update_student_by_id(student_id: str, student: Student):
    update_student(student_id, student)
    return {"message": "Student updated", "student": student}

@app.delete("/students/{student_id}")
def delete_student_by_id(student_id: str):
    delete_student(student_id)
    return {"message": "Student deleted"}
