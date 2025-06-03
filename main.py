from fastapi import FastAPI, HTTPException  # Import FastAPI and error handler
from pydantic import BaseModel              # Import BaseModel for data validation
from typing import List                     # For type hinting list of students
import json                                 # To read/write JSON data
import os                                   # To check file existence

app = FastAPI()  # Create FastAPI app instance

# Define a Pydantic model for Student
class Student(BaseModel):
    name: str
    age: int
    major: str

# JSON file path where student data is stored
DATA_FILE = "students.json"

# Function to load student data from JSON file
def load_students():
    if os.path.exists(DATA_FILE):  # Check if file exists
        with open(DATA_FILE, "r") as f:
            return json.load(f)    # Return loaded data
    return []                      # If file doesn't exist, return empty list

# Function to save student data to JSON file
def save_students(students):
    with open(DATA_FILE, "w") as f:
        json.dump(students, f, indent=4)  # Write data with indentation

# Load students into memory at app start
students = load_students()

@app.get("/")  # Root endpoint
def root():
    return {"message": "Welcome to the Student API"}

# Endpoint to list all students
@app.get("/students", response_model=List[Student])
def get_students():
    return students  # Return in-memory list

# Endpoint to create a new student
@app.post("/students", response_model=Student)
def create_student(student: Student):
    student_data = student.dict()   # Convert Pydantic model to dictionary
    students.append(student_data)   # Add to list
    save_students(students)         # Save to file
    return student_data             # Return created student

# Endpoint to get a student by index
@app.get("/students/{student_id}", response_model=Student)
def get_student(student_id: int):
    if 0 <= student_id < len(students):   # Check if index is valid
        return students[student_id]       # Return student
    raise HTTPException(status_code=404, detail="Student not found")  # Error

# Endpoint to update a student by index
@app.put("/students/{student_id}", response_model=Student)
def update_student(student_id: int, updated_student: Student):
    if 0 <= student_id < len(students):
        students[student_id] = updated_student.dict()  # Replace with new data
        save_students(students)                        # Save to file
        return updated_student                         # Return updated
    raise HTTPException(status_code=404, detail="Student not found")

# Endpoint to delete a student by index
@app.delete("/students/{student_id}")
def delete_student(student_id: int):
    if 0 <= student_id < len(students):
        students.pop(student_id)       # Remove from list
        save_students(students)        # Save updated list
        return {"detail": "Student deleted successfully"}
    raise HTTPException(status_code=404, detail="Student not found")

