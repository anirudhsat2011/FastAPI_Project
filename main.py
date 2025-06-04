from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security.api_key import APIKeyHeader, APIKey
from pydantic import BaseModel
from typing import Dict, Optional, List
import shelve
import secrets

app = FastAPI()

DB_FILE = "data.db"

# Security
API_KEY_NAME = "Authorization"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Models
class User(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Student(BaseModel):
    id: Optional[int] = None  # ID is optional for creation
    name: str
    age: int
    major: str

# Helpers for shelve access
def get_db():
    return shelve.open(DB_FILE)

def verify_token(api_key: str = Security(api_key_header)):
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing authorization token")
    with get_db() as db:
        tokens = db.get("tokens", {})
        if api_key not in tokens.values():
            raise HTTPException(status_code=401, detail="Invalid token")
    return api_key

# User management
@app.post("/register", status_code=201)
def register(user: User):
    with get_db() as db:
        users = db.get("users", {})
        if user.username in users:
            raise HTTPException(status_code=400, detail="User already exists")
        users[user.username] = user.password
        db["users"] = users
    return {"message": "User registered successfully"}

@app.post("/login")
def login(user: UserLogin):
    with get_db() as db:
        users = db.get("users", {})
        if users.get(user.username) != user.password:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        tokens = db.get("tokens", {})
        # Generate a token and store it
        token = secrets.token_hex(16)
        tokens[user.username] = token
        db["tokens"] = tokens
    return {"token": token}

# Student CRUD
@app.post("/students", status_code=201, dependencies=[Depends(verify_token)])
def create_student(student: Student):
    with get_db() as db:
        students = db.get("students", {})
        # Generate new ID
        if students:
            new_id = max(int(k) for k in students.keys()) + 1
        else:
            new_id = 1
        student.id = new_id
        students[str(new_id)] = student.dict()
        db["students"] = students
    return student

@app.get("/students", response_model=List[Student], dependencies=[Depends(verify_token)])
def list_students(major: Optional[str] = None, age: Optional[int] = None):
    with get_db() as db:
        students = db.get("students", {})
        result = []
        for s in students.values():
            if major and s["major"] != major:
                continue
            if age and s["age"] != age:
                continue
            result.append(Student(**s))
    return result

@app.get("/students/{student_id}", response_model=Student, dependencies=[Depends(verify_token)])
def get_student(student_id: int):
    with get_db() as db:
        students = db.get("students", {})
        student = students.get(str(student_id))
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
    return Student(**student)

@app.put("/students/{student_id}", response_model=Student, dependencies=[Depends(verify_token)])
def update_student(student_id: int, student: Student):
    with get_db() as db:
        students = db.get("students", {})
        if str(student_id) not in students:
            raise HTTPException(status_code=404, detail="Student not found")
        student.id = student_id  # ensure ID stays consistent
        students[str(student_id)] = student.dict()
        db["students"] = students
    return student

@app.delete("/students/{student_id}", status_code=204, dependencies=[Depends(verify_token)])
def delete_student(student_id: int):
    with get_db() as db:
        students = db.get("students", {})
        if str(student_id) not in students:
            raise HTTPException(status_code=404, detail="Student not found")
        del students[str(student_id)]
        db["students"] = students
    return

# Add token to Swagger UI Authorize button
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Student Registry with Auth",
        version="1.0.0",
        description="API for student registry with token-based auth",
        routes=app.routes,
    )
    # Add security scheme for Authorization header (Bearer token style)
    openapi_schema["components"]["securitySchemes"] = {
        "APIKeyHeader": {
            "type": "apiKey",
            "name": API_KEY_NAME,
            "in": "header"
        }
    }
    # Apply globally to all endpoints
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            openapi_schema["paths"][path][method]["security"] = [{"APIKeyHeader": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
