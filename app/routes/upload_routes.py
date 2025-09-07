# app/routes/upload_routes.py

import os
import uuid
import aiofiles
from fastapi import APIRouter, UploadFile, File, Form, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from starlette import status

from app.db import SessionLocal, Upload

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/upload_form")
def upload_form(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@router.post("/upload")
async def upload_files(
    request: Request,
    user_id: int = Form(...),
    resume: UploadFile = File(...),
    jd: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    uid = str(uuid.uuid4())
    folder = os.path.join(UPLOAD_DIR, uid)
    os.makedirs(folder, exist_ok=True)

    resume_path = os.path.join(folder, "resume.pdf")
    jd_path = os.path.join(folder, "jd.pdf")

    resume_bytes = await resume.read()
    jd_bytes = await jd.read()

    async with aiofiles.open(resume_path, "wb") as f:
        await f.write(resume_bytes)
    async with aiofiles.open(jd_path, "wb") as f:
        await f.write(jd_bytes)

    record = Upload(
        user_id=user_id,
        resume_path=resume_path,
        resume_blob=resume_bytes,
        jd_path=jd_path,
        jd_blob=jd_bytes
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    # Store paths in session
    request.session["resume_path"] = resume_path
    request.session["jd_path"] = jd_path

    return RedirectResponse(
        url=f"/suitability/view/{record.id}",
        status_code=status.HTTP_303_SEE_OTHER
    )
