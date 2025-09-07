from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db import SessionLocal, Upload
from app.services.pdf_reader import extract_text
from app.services.suitability_agent import analyze_candidate
import json

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/view/{upload_id}")
def view_suitability(request: Request, upload_id: int, db: Session = Depends(get_db)):
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        return templates.TemplateResponse("suitability.html", {"request": request, "error": "Upload not found"})
    resume_text = extract_text(upload.resume_path)
    jd_text = extract_text(upload.jd_path)
    result = analyze_candidate(resume_text, jd_text)
    # save to DB
    upload.analysis_score = result.get("score")
    upload.analysis_summary = result.get("summary")
    upload.strengths = json.dumps(result.get("strengths", []))
    upload.weaknesses = json.dumps(result.get("weaknesses", []))
    upload.recommendations = json.dumps(result.get("recommendations", []))
    db.add(upload)
    db.commit()
    # convert lists back for template
    result["strengths"] = result.get("strengths", [])
    result["weaknesses"] = result.get("weaknesses", [])
    result["recommendations"] = result.get("recommendations", [])
    return templates.TemplateResponse("suitability.html", {"request": request, "result": result, "upload_id": upload_id})
