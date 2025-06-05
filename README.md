# FastAPI Student Registry

A secure and modern student registry API built using **FastAPI**, **SQLModel**, and **QLite**, with **JWT-based authentication**. This project allows authenticated users to manage student records.

# Features

- User registration and login with password hashing
- JWT token-based authentication
- Full CRUD API for student records
- SQLite database with SQLModel ORM
- Swagger UI at `/docs` for easy testing

# Requirements

- Python 3.10+
- `virtualenv` or `venv`

# Installation

```bash
# To access the git repository
cd FastAPI_Project

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate 

```
# Run the code
Type in "uv run -- uvicorn main:app --reload" in your terminal.
Go to the link "http://127.0.0.1:8000" in your browser to access the app.