from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import os

app = FastAPI()  # Create FastAPI app instance

# Define the data model for a student
class Student(BaseModel):
    name: str
    age: int
    major: str

DATA_FILE = "students.json"  # File to save/load student data

def load_students():
    """
    Load students data from the JSON file.
    Returns a list of students as dictionaries.
    If the file doesn't exist, returns an empty list.
    """
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_students(students):
    """
    Save the list of students (as dictionaries) to the JSON file.
    """
    with open(DATA_FILE, "w") as f:
        json.dump(students, f, indent=4)

# Load students once when the app starts
students = load_students()

@app.get("/")
def root():
    """
    Root endpoint: simple hello world message.
    """
    return {"message": "Welcome to the Student API"}

@app.get("/students")
def get_students():
    """
    Return the full list of students.
    """
    return students

@app.post("/students", response_model=Student)
def create_student(student: Student):
    """
    Create a new student.
    Append to the in-memory list and save to disk.
    Returns the newly created student.
    """
    # Convert the Pydantic model to dict for JSON serialization
    student_data = student.dict()

    # Optional: Prevent duplicates by checking if student exists (commented out)
    # for s in students:
    #     if s == student_data:
    #         raise HTTPException(status_code=400, detail="Student already exists")

    students.append(student_data)  # Add new student
    save_students(students)        # Save updated list to file
    return student

@app.get("/students/{student_id}")
def get_student(student_id: int):
    """
    Retrieve a student by their index (ID).
    If index is out of range, return 404 error.
    """
    if 0 <= student_id < len(students):
        return students[student_id]
    else:
        raise HTTPException(status_code=404, detail="Student not found")

@app.put("/students/{student_id}", response_model=Student)
def update_student(student_id: int, updated_student: Student):
    """
    Update an existing student's data by index.
    Save the changes to disk.
    """
    if 0 <= student_id < len(students):
        students[student_id] = updated_student.dict()  # Update data
        save_students(students)                        # Save to file
        return updated_student
    else:
        raise HTTPException(status_code=404, detail="Student not found")

@app.delete("/students/{student_id}")
def delete_student(student_id: int):
    """
    Delete a student by index.
    Save the updated list to disk.
    """
    if 0 <= student_id < len(students):
        students.pop(student_id)   # Remove student from list
        save_students(students)    # Save updated list
        return {"detail": "Student deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Student not found")
