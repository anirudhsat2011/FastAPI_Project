from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.security.api_key import APIKeyHeader
from sqlmodel import SQLModel, Field, Session, create_engine, select
from typing import Optional, List, Dict
from pydantic import BaseModel
import secrets
import hashlib

app = FastAPI(
    title="CampusCore",
    description="The heart of student management and communication!!!",
    version="1.0.0",
)

# Database setup
DATABASE_URL = "sqlite:///./students.sqlite"
engine = create_engine(DATABASE_URL, echo=False)

# Role levels
ROLE_GUEST = 100
ROLE_VIP = 200
ROLE_OWNER = 300

# API key header for auth
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# --- Models ---

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    role: int = ROLE_GUEST
    api_key: str = Field(default_factory=lambda: secrets.token_hex(16))
    suspended: bool = False

class UserCreate(BaseModel):
    username: str
    password: str

class Student(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    age: int
    course: str

class StudentCreate(BaseModel):
    name: str
    age: int
    course: str

class StudentUpdate(BaseModel):
    name: Optional[str]
    age: Optional[int]
    course: Optional[str]

class ChatMessage(BaseModel):
    username: str
    message: str

# --- Utility functions ---

def get_session():
    with Session(engine) as session:
        yield session

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def get_user_by_username(session: Session, username: str) -> Optional[User]:
    statement = select(User).where(User.username == username.lower())
    return session.exec(statement).first()

def get_user_by_api_key(session: Session, api_key: str) -> Optional[User]:
    statement = select(User).where(User.api_key == api_key)
    return session.exec(statement).first()

def create_owner_user():
    with Session(engine) as session:
        owner = get_user_by_username(session, "anirudh")
        if not owner:
            password = "Aaradhya2509"
            hashed = hash_password(password)
            owner = User(username="anirudh", hashed_password=hashed, role=ROLE_OWNER)
            session.add(owner)
            session.commit()
            print("Owner user created: username='anirudh', password='Aaradhya2509'")

# --- Dependency for authentication ---

async def get_current_user(api_key: str = Depends(api_key_header), session: Session = Depends(get_session)) -> User:
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API Key")
    user = get_user_by_api_key(session, api_key)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")
    if user.suspended:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User suspended")
    return user

# --- Welcome endpoint ---

@app.get("/root", tags=["Welcome Message"])
def root():
    return {"Welcome to CampusCore, The heart of student management and communication!!!"}

# --- User Management ---

@app.post("/register", tags=["User Management"])
def register(user_create: UserCreate, session: Session = Depends(get_session)):
    username_lower = user_create.username.lower()
    if get_user_by_username(session, username_lower):
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed = hash_password(user_create.password)
    user = User(username=username_lower, hashed_password=hashed)
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"username": user.username, "api_key": user.api_key, "role": user.role}

@app.post("/login", tags=["User Management"])
def login(user_create: UserCreate, session: Session = Depends(get_session)):
    username_lower = user_create.username.lower()
    user = get_user_by_username(session, username_lower)
    if not user or not verify_password(user_create.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if user.suspended:
        raise HTTPException(status_code=403, detail="User suspended")
    # Return API key and role
    return {"username": user.username, "api_key": user.api_key, "role": user.role}

@app.get("/users", tags=["User Management"])
def list_users(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    if current_user.role != ROLE_OWNER:
        raise HTTPException(status_code=403, detail="Only owner can list users")
    statement = select(User)
    users = session.exec(statement).all()
    return [{"username": u.username, "role": u.role, "suspended": u.suspended} for u in users]

@app.delete("/users/{username}", tags=["User Management"])
def delete_user(username: str, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    if current_user.role != ROLE_OWNER:
        raise HTTPException(status_code=403, detail="Only owner can delete users")
    username_lower = username.lower()
    user = get_user_by_username(session, username_lower)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == ROLE_OWNER:
        raise HTTPException(status_code=403, detail="Cannot delete owner")
    session.delete(user)
    session.commit()
    return {"detail": f"User '{username_lower}' deleted"}

@app.post("/users/{username}/suspend", tags=["User Management"])
def suspend_user(username: str, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    if current_user.role != ROLE_OWNER:
        raise HTTPException(status_code=403, detail="Only owner can suspend users")
    username_lower = username.lower()
    user = get_user_by_username(session, username_lower)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == ROLE_OWNER:
        raise HTTPException(status_code=403, detail="Cannot suspend owner")
    user.suspended = True
    session.add(user)
    session.commit()
    return {"detail": f"User '{username_lower}' suspended"}

@app.post("/users/{username}/unsuspend", tags=["User Management"])
def unsuspend_user(username: str, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    if current_user.role != ROLE_OWNER:
        raise HTTPException(status_code=403, detail="Only owner can unsuspend users")
    username_lower = username.lower()
    user = get_user_by_username(session, username_lower)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.suspended = False
    session.add(user)
    session.commit()
    return {"detail": f"User '{username_lower}' unsuspended"}

@app.post("/users/{username}/role", tags=["User Management"])
def change_user_role(username: str, new_role: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    if current_user.role != ROLE_OWNER:
        raise HTTPException(status_code=403, detail="Only owner can change user roles")
    username_lower = username.lower()
    if username_lower == current_user.username:
        raise HTTPException(status_code=403, detail="Cannot change your own role")
    if new_role == ROLE_OWNER:
        raise HTTPException(status_code=403, detail="Cannot assign Owner role")
    if new_role not in [ROLE_GUEST, ROLE_VIP]:
        raise HTTPException(status_code=400, detail="Invalid role level")
    user = get_user_by_username(session, username_lower)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = new_role
    session.add(user)
    session.commit()
    return {"detail": f"User '{username_lower}' role changed to {new_role}"}

# --- Student Management ---

@app.post("/students", tags=["Student Management"])
def create_student(student: StudentCreate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    if current_user.role < ROLE_VIP:
        raise HTTPException(status_code=403, detail="Insufficient permissions to create student")
    new_student = Student(name=student.name, age=student.age, course=student.course)
    session.add(new_student)
    session.commit()
    session.refresh(new_student)
    return new_student

@app.get("/students", tags=["Student Management"])
def list_students(course: Optional[str] = None, age: Optional[int] = None, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    statement = select(Student)
    if course:
        statement = statement.where(Student.course == course)
    if age:
        statement = statement.where(Student.age == age)
    students = session.exec(statement).all()
    return students

@app.get("/students/{student_id}", tags=["Student Management"])
def get_student(student_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@app.put("/students/{student_id}", tags=["Student Management"])
def update_student(student_id: int, student_update: StudentUpdate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    if current_user.role < ROLE_VIP:
        raise HTTPException(status_code=403, detail="Insufficient permissions to update student")
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if student_update.name is not None:
        student.name = student_update.name
    if student_update.age is not None:
        student.age = student_update.age
    if student_update.course is not None:
        student.course = student_update.course
    session.add(student)
    session.commit()
    session.refresh(student)
    return student

@app.delete("/students/{student_id}", tags=["Student Management"])
def delete_student(student_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    if current_user.role < ROLE_VIP:
        raise HTTPException(status_code=403, detail="Insufficient permissions to delete student")
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    session.delete(student)
    session.commit()
    return {"detail": f"Student with id {student_id} deleted"}

# --- Communication (Chatbox) ---

chat_messages: List[Dict] = []

@app.get("/chat", tags=["Communication"])
def get_chat_messages():
    # Return last 100 messages
    return chat_messages[-100:]

@app.post("/chat", tags=["Communication"])
def post_chat_message(message: ChatMessage, current_user: User = Depends(get_current_user)):
    chat_messages.append({"username": current_user.username, "message": message.message})
    # Limit chat length
    if len(chat_messages) > 200:
        chat_messages.pop(0)
    return {"detail": "Message sent"}

# --- Startup event to create DB and owner user ---

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)
    create_owner_user()
