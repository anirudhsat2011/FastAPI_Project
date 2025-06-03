from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
import os

app = FastAPI()

class Student(BaseModel):
    name: str
    age: int
    major: str

DATA_FILE = "students.json"

def load_students() -> List[dict]:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_students(students: List[dict]) -> None:
    with open(DATA_FILE, "w") as f:
        json.dump(students, f, indent=4)

def get_next_id() -> int:
    used_ids = sorted(student["id"] for student in students)
    for i in range(1, len(used_ids) + 2):
        if i not in used_ids:
            return i

students = load_students()

@app.get("/")
def root():
    return {"message": "Welcome to the Student API"}

@app.get("/students")
def list_students(major: Optional[str] = None):
    if major:
        return [s for s in students if s["major"].lower() == major.lower()]
    return students

@app.post("/students")
def create_student(student: Student):
    student_data = student.dict()
    student_data["id"] = get_next_id()
    students.append(student_data)
    save_students(students)
    return student_data

@app.get("/students/{student_id}")
def get_student(student_id: int):
    for student in students:
        if student["id"] == student_id:
            return student
    raise HTTPException(status_code=404, detail="Student not found")

@app.put("/students/{student_id}")
def update_student(student_id: int, updated_student: Student):
    for i, student in enumerate(students):
        if student["id"] == student_id:
            updated = updated_student.dict()
            updated["id"] = student_id
            students[i] = updated
            save_students(students)
            return updated
    raise HTTPException(status_code=404, detail="Student not found")

@app.delete("/students/{student_id}")
def delete_student(student_id: int):
    for i, student in enumerate(students):
        if student["id"] == student_id:
            students.pop(i)
            save_students(students)
            return {"detail": "Student deleted successfully"}
    raise HTTPException(status_code=404, detail="Student not found")
