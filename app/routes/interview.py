from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.services.question_generator import generate_questions
from app.services.evaluator import evaluate_interview
from app.services.pdf_utils import read_pdf_text
from app.db import SessionLocal, Upload
import json

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ Default fallback if AI fails
DEFAULT_QUESTIONS = [
    "Tell me about yourself.",
    "Describe a project you worked on.",
    "What is your greatest strength?",
    "What is your greatest weakness?",
    "Why do you want this job?"
]

@router.get("/start/{upload_id}")
async def interview_start(request: Request, upload_id: int, db: Session = Depends(get_db)):
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        return JSONResponse({"error": "Upload ID not found"}, status_code=404)

    try:
        questions = json.loads(upload.questions) if upload.questions else []
    except Exception:
        questions = []

    # ✅ Always guarantee some questions
    if not questions:
        resume_text = read_pdf_text(upload.resume_path)
        jd_text = read_pdf_text(upload.jd_path)
        questions = generate_questions(resume_text, jd_text, n=5)
        if not questions:
            questions = [
                "Tell me about yourself.",
                "Describe a project you worked on.",
                "What is your greatest strength?",
                "What is your greatest weakness?",
                "Why do you want this job?"
            ]
        upload.questions = json.dumps(questions, ensure_ascii=False)
        db.add(upload)
        db.commit()

    return templates.TemplateResponse("interview.html", {
        "request": request,
        "upload_id": upload_id,
        "questions_json": json.dumps(questions, ensure_ascii=False)
    })

@router.post("/submit")
async def interview_submit(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        upload_id = data.get("upload_id")
        qa_list = data.get("qa_list", [])

        if not upload_id or not qa_list:
            return JSONResponse({"error": "Missing upload_id or answers"}, status_code=400)

        upload = db.query(Upload).filter(Upload.id == upload_id).first()
        if not upload:
            return JSONResponse({"error": "Upload ID not found"}, status_code=404)

        resume_text = read_pdf_text(upload.resume_path) if upload.resume_path else ""
        jd_text = read_pdf_text(upload.jd_path) if upload.jd_path else ""

        # ✅ Wrap evaluator safely
        try:
            result = evaluate_interview(resume_text, jd_text, qa_list)
        except Exception as e:
            result = {"score": 5, "feedback": f"Evaluation failed: {e}"}

        # Save into DB
        upload.analysis_score = result.get("score")
        upload.analysis_summary = result.get("feedback")
        db.add(upload)
        db.commit()

        return JSONResponse(result)

    except Exception as e:
        return JSONResponse({"error": f"Submit crashed: {e}"}, status_code=500)


@router.post("/upload_pdfs")
async def upload_pdfs(resume_path: str = Form(...), jd_path: str = Form(...), db: Session = Depends(get_db)):
    """
    Accepts resume and JD paths, generates questions, and saves them in DB.
    """
    resume_text = read_pdf_text(resume_path)
    jd_text = read_pdf_text(jd_path)

    questions = generate_questions(resume_text, jd_text, n=5)
    if not questions or not isinstance(questions, list):
        questions = DEFAULT_QUESTIONS

    upload = Upload(
        resume_path=resume_path,
        jd_path=jd_path,
        questions=json.dumps(questions, ensure_ascii=False)
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)

    return JSONResponse({"upload_id": upload.id, "questions": questions})
