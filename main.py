from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security.api_key import APIKeyHeader
from sqlmodel import SQLModel, Field, create_engine, Session, select
from pydantic import BaseModel
from typing import Optional, List
import secrets

app = FastAPI()

DATABASE_URL = "sqlite:///students.sqlite"
engine = create_engine(DATABASE_URL, echo=True)

API_KEY_NAME = "Authorization"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

class User(SQLModel, table=True):
    username: str = Field(primary_key=True)
    password: str

class Token(SQLModel, table=True):
    username: str = Field(primary_key=True)
    token: str

class Student(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    age: int
    major: str

class StudentCreate(BaseModel):
    name: str
    age: int
    major: str

class UserRegister(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

def get_session():
    with Session(engine) as session:
        yield session

def verify_token(api_key: str = Security(api_key_header), session: Session = Depends(get_session)):
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing authorization token")
    token_obj = session.get(Token, api_key)

    token_obj = session.exec(select(Token).where(Token.token == api_key)).first()
    if not token_obj:
        raise HTTPException(status_code=401, detail="Invalid token")
    return api_key

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

@app.post("/register", status_code=201)
def register(user: UserRegister, session: Session = Depends(get_session)):
    existing_user = session.get(User, user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    user_obj = User(username=user.username, password=user.password)
    session.add(user_obj)
    session.commit()
    return {"message": "User registered successfully"}

@app.post("/login")
def login(user: UserLogin, session: Session = Depends(get_session)):
    user_obj = session.get(User, user.username)
    if not user_obj or user_obj.password != user.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = secrets.token_hex(16)
    token_obj = Token(username=user.username, token=token)
    old_token = session.get(Token, user.username)
    if old_token:
        session.delete(old_token)
        session.commit()
    session.add(token_obj)
    session.commit()
    return {"token": token}

@app.post("/students", status_code=201, dependencies=[Depends(verify_token)])
def create_student(student_create: StudentCreate, session: Session = Depends(get_session)):
    student = Student.from_orm(student_create)
    session.add(student)
    session.commit()
    session.refresh(student)
    return student

@app.get("/students", response_model=List[Student], dependencies=[Depends(verify_token)])
def list_students(major: Optional[str] = None, age: Optional[int] = None, session: Session = Depends(get_session)):
    query = select(Student)
    if major:
        query = query.where(Student.major == major)
    if age:
        query = query.where(Student.age == age)
    students = session.exec(query).all()
    return students

@app.get("/students/{student_id}", response_model=Student, dependencies=[Depends(verify_token)])
def get_student(student_id: int, session: Session = Depends(get_session)):
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@app.put("/students/{student_id}", response_model=Student, dependencies=[Depends(verify_token)])
def update_student(student_id: int, student_update: StudentCreate, session: Session = Depends(get_session)):
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    student.name = student_update.name
    student.age = student_update.age
    student.major = student_update.major
    session.add(student)
    session.commit()
    session.refresh(student)
    return student

@app.delete("/students/{student_id}", status_code=204, dependencies=[Depends(verify_token)])
def delete_student(student_id: int, session: Session = Depends(get_session)):
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    session.delete(student)
    session.commit()
    return

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
    openapi_schema["components"]["securitySchemes"] = {
        "APIKeyHeader": {
            "type": "apiKey",
            "name": API_KEY_NAME,
            "in": "header"
        }
    }
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            openapi_schema["paths"][path][method]["security"] = [{"APIKeyHeader": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
