from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import json
import os

app = FastAPI()  # Initialize FastAPI app

# Define the Student model
class Student(BaseModel):
    name: str
    age: int
    major: str

# File to persist student data
DATA_FILE = "students.json"

def load_students():
    """Load student data from disk."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_students(students):
    """Save student data to disk."""
    with open(DATA_FILE, "w") as f:
        json.dump(students, f, indent=4)

# Load students on app startup
students = load_students()

@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "Welcome to the Student API"}

@app.get("/students", response_model=List[Student])
def get_students():
    """List all students."""
    return students

@app.post("/students", response_model=Student)
def create_student(student: Student):
    """Create a new student."""
    student_data = student.dict()
    students.append(student_data)
    save_students(students)
    return student

@app.get("/students/{student_id}", response_model=Student)
def get_student(student_id: int):
    """Get a student by ID (index)."""
    if 0 <= student_id < len(students):
        return students[student_id]
    else:
        raise HTTPException(status_code=404, detail="Student not found")

@app.put("/students/{student_id}", response_model=Student)
def update_student(student_id: int, updated_student: Student):
    """Update a student's information."""
    if 0 <= student_id < len(students):
        students[student_id] = updated_student.dict()
        save_students(students)
        return updated_student
    else:
        raise HTTPException(status_code=404, detail="Student not found")

@app.delete("/students/{student_id}")
def delete_student(student_id: int):
    """Delete a student by ID."""
    if 0 <= student_id < len(students):
        students.pop(student_id)
        save_students(students)
        return {"detail": "Student deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Student not found")
