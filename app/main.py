import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from app.routes import auth_routes, upload_routes, suitability, interview
from starlette.middleware.sessions import SessionMiddleware
from fastapi.routing import APIRoute
from fastapi.responses import HTMLResponse

App = FastAPI(title="AI Powered Interview simulator")

# Mounting the templates and static files:
App.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Setting CORS:
App.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY"),
    same_site="lax",
    session_cookie="session",
    max_age=None
)

# Include the interview route:
App.include_router(interview.router, prefix="/interview")
App.include_router(auth_routes.router, prefix="/auth")
App.include_router(upload_routes.router, prefix="/files")
App.include_router(suitability.router, prefix="/suitability")

@App.get("/", include_in_schema=False)
def home(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})

@App.get("/test-set")
def test_set(request: Request):
    request.session["foo"] = "bar"
    return {"message": "session foo set"}

@App.get("/test-get")
def test_get(request: Request):
    return {"foo": request.session.get("foo")}

for route in App.routes:
    if isinstance(route, APIRoute):
        print(f"Path: {route.path}, Methods: {route.methods}")


@App.get("/ping")
async def ping(): return {"ping": "pong"}
