from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import os

app = FastAPI()

# JSON file to store student data
DATA_FILE = "students.json"

# Define the structure of a student
class Student(BaseModel):
    name: str
    age: int
    major: str

# Load existing students from the file
def load_students():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return [Student(**s) for s in json.load(f)]
    return []

# Save the current list of students to the file
def save_students():
    with open(DATA_FILE, "w") as f:
        json.dump([s.dict() for s in students], f, indent=2)

# Load students at startup
students = load_students()

# Root endpoint to test if API is running
@app.get("/")
def root():
    return {"Hello": "Student API"}

# Add a new student
@app.post("/students")
def create_student(student: Student):
    students.append(student)  # Add student to list
    save_students()           # Save updated list to file
    return students           # Return updated list

# List all students (with a limit)
@app.get("/students/", response_model=list[Student])
def list_students(limit: int = 10):
    return students[0:limit]  # Return limited list of students

# Get one student by index
@app.get("/students/{student_id}", response_model=Student)
def get_student(student_id: int):
    if student_id < len(students):
        return students[student_id]
    else:
        raise HTTPException(status_code=404, detail="Student not found")

# ✅ Update an existing student
@app.put("/students/{student_id}", response_model=Student)
def update_student(student_id: int, updated_student: Student):
    if student_id < len(students):
        students[student_id] = updated_student     # Replace existing student data
        save_students()                            # Save changes to file
        return updated_student                      # Return updated data
    else:
        raise HTTPException(status_code=404, detail="Student not found")

# ❌ Delete a student by index
@app.delete("/students/{student_id}")
def delete_student(student_id: int):
    if student_id < len(students):
        deleted = students.pop(student_id)  # Remove the student from the list
        save_students()                     # Save updated list
        return {"message": "Student deleted", "student": deleted}
    else:
        raise HTTPException(status_code=404, detail="Student not found")
