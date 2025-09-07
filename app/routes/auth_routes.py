# app/routes/auth_routes.py
from fastapi import APIRouter, Form, Depends, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db import SessionLocal, User
from app.auth import hash_password, verify_password, create_access_token
from app.db import SessionLocal

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/register", response_class=HTMLResponse, name="register_form")
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register", response_class=HTMLResponse)
def register_action(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return templates.TemplateResponse("register.html", {"request": request, "error": "User already exists"})
    user = User(email=email, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    # After registration, redirect to login page (GET)
    return templates.TemplateResponse("login.html", {"request": request, "success": "Registration successful. Please log in."})

@router.get("/login", response_class=HTMLResponse, name="login_form")
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login_action(request: Request, response: Response, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
    token = create_access_token({"user_id": user.id, "sub": user.email})
    redirect = RedirectResponse(url="/files/upload_form", status_code=status.HTTP_303_SEE_OTHER)
    # set cookie on the RedirectResponse that we will return
    redirect.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True, secure=False, samesite="lax", max_age=60*60*24)
    return redirect

@router.get("/logout")
def logout(response: Response):
    redirect = RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    redirect.delete_cookie("access_token")
    return redirect
