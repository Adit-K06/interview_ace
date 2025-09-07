# app/services/question_generator.py
import os, re
from dotenv import load_dotenv

# If you want AI questions (Gemini):
USE_AI = True

try:
    import google.generativeai as genai
except Exception:
    genai = None
    USE_AI = False

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

if USE_AI and genai and API_KEY:
    genai.configure(api_key=API_KEY)

def _fallback_questions():
    return [
        "Walk me through a project from your resume you're most proud of. Why?",
        "Given an API spec, how would you design the data models and endpoints?",
        "How do you debug performance issues in a web application?",
        "Describe a tough technical decision you made and how you evaluated trade-offs.",
        "Implement a function to check if a string is a valid palindrome (ignore non-alphanumerics)."
    ]

def generate_questions(resume_text: str, jd_text: str, n: int = 5):
    """
    Returns a list of n questions. Uses Gemini if configured; else falls back to a solid default set.
    """
    if USE_AI and genai and API_KEY:
        prompt = f"""
    You are an expert technical interviewer. Based on the candidate resume and job description below,
    generate {n} concise interview questions tailored to the candidate and role.
    - Mix technical, coding, and behavioral questions.
    - Try to label coding questions by prefixing them with [CODING], but do not require it.
    - Return one question per line, clear and concise.
    Resume (truncated):
    {resume_text[:1500]}

    Job Description (truncated):
    {jd_text[:1500]}
    """
        
        try:
            model = genai.GenerativeModel(MODEL)
            resp = model.generate_content(prompt)
            text = getattr(resp, "text", None)
            if not text:
                text = str(resp)
            lines = [re.sub(r'^[\-\d\.\s]+', '', l).strip() for l in text.splitlines() if l.strip()]
            if not lines:
                return _fallback_questions()[:n]
            return lines[:n]
        except Exception:
            return _fallback_questions()[:n]
    else:
        return _fallback_questions()[:n]
