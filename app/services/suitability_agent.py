# app/services/suitability_agent.py
import os, re, json
import google.generativeai as genai

from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "gemini-2.5-flash-lite"

def analyze_candidate(resume_text: str, jd_text: str):
    prompt = f"""
    You are a senior technical hiring evaluator. Given the resume and job description, return ONLY valid JSON with fields:
    {{"score": <0-100 integer>, "summary": "<1-2 sentence summary>", "strengths": ["..."], "weaknesses": ["..."], "recommendations": ["..."]}}

    Resume:
    {resume_text[:2000]}

    Job Description:
    {jd_text[:2000]}
    """
    model = genai.GenerativeModel(MODEL)
    resp = model.generate_content(prompt)
    raw = resp if isinstance(resp, str) else getattr(resp, "text", str(resp))
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
    try:
        return json.loads(raw)
    except Exception:
        return {"score": None, "summary": raw, "strengths": [], "weaknesses": [], "recommendations": []}
