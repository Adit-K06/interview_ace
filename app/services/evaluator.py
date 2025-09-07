# app/services/evaluator.py
import os
import json
import re
import ast
from dotenv import load_dotenv

try:
    import google.generativeai as genai
except ImportError:
    genai = None

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
print("GEMINI_API_KEY:", API_KEY)
print("GEMINI_MODEL:", MODEL)

if genai and API_KEY:
    genai.configure(api_key=API_KEY)


def safe_parse_json(json_str: str):
    """
    Safely extracts and parses JSON from Gemini responses, removing code fences, extra text,
    and handling unescaped characters or smart quotes.
    """
    if not json_str:
        return None

    # Remove leading text before first ```
    json_str = re.sub(r'^.*?```', '```', json_str.strip(), flags=re.DOTALL)

    # Extract JSON inside ```json ... ```
    match = re.search(r'```json(.*?)```', json_str, flags=re.DOTALL)
    if match:
        json_str = match.group(1)
    else:
        # Fallback: try everything between first { and last }
        start = json_str.find("{")
        end = json_str.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        json_str = json_str[start:end+1]

    # Replace newlines and smart quotes
    json_str = json_str.replace('\n', ' ').replace('\r', '')
    json_str = json_str.replace('“', '"').replace('”', '"').replace('’', "'")

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print("Final JSON parse failed:", e)
        return None


def parse_gemini_response(resp):
    text = getattr(resp, "text", None) or str(resp)
    # Remove markdown code fences and leading 'json' if present
    text = re.sub(r"^```json|^```|```$", "", text.strip(), flags=re.MULTILINE).strip()
    # Find the first and last curly braces to extract JSON
    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        json_str = text[start:end+1]
        # Replace escaped newlines and double backslashes
        json_str = json_str.replace('\\n', ' ').replace('\\\\', '\\')
        try:
            return json.loads(json_str)
        except Exception as e:
            print("json.loads failed:", e)
            try:
                return ast.literal_eval(json_str)
            except Exception as e2:
                print("ast.literal_eval failed:", e2)
                print("Gemini response was:", json_str)
    return None
    
def evaluate_interview(resume_text: str, jd_text: str, qa_list: list):
    """
    Returns a dict with detailed evaluation fields if AI is available,
    otherwise uses a simple heuristic fallback.
    """
    if genai and API_KEY:
        prompt = f"""
        You are an expert technical interviewer and evaluator.

        Candidate resume (truncated):
        {resume_text[:1500]}

        Job description (truncated):
        {jd_text[:1500]}

        Interview data (questions and candidate answers):
        {json.dumps(qa_list, ensure_ascii=False, indent=2)}

        Your task is to provide an extremely detailed, structured, and point-wise evaluation
        of the candidate's interview performance. Be exhaustive, analytical, and specific.
        Follow these steps:

        1. Summarize candidate performance in the interview (max 3 sentences).
        2. List at least 3 positives, with crisp explanations.
        3. List at least 3 improvements needed, crisp explanations.
        4. Suggest at least 8 further preparation areas, detailed explanations.
        5. Provide a very precise evaluation (max 100 words, max 3 sentences).
        6. Give an overall score (0-10) and summary feedback (min 4 sentences).

        Respond ONLY with valid JSON (no markdown, no code fences) with keys:

        {{
          "summary": "<summary>",
          "positives": ["<positive point 1>", ...],
          "improvements": ["<improvement 1>", ...],
          "preparation_needed": ["<topic 1>", ...],
          "detailed_evaluation": "<detailed evaluation>",
          "score": <integer 0-10>,
          "feedback": "<overall feedback>"
        }}

        """

        try:
            model = genai.GenerativeModel(MODEL)
            resp = model.generate_content(prompt)
            # data = resp
            data = parse_gemini_response(resp)
            print(data['summary'])
            if data:
                return {
                    "score": data['score'],
                    "summary": data['summary'],
                }
        except Exception as e:
            print("Gemini API error:", e)

    # Fallback heuristic if AI unavailable or parse failed
    answered = sum(1 for qa in qa_list if qa.get("a", "").strip())
    total = len(qa_list) or 1
    score = round(10 * (answered / total))
    feedback = (
        "Basic evaluation: answers were measured by completeness only (AI disabled or unavailable). "
        f"Provided answers for {answered} out of {total} questions."
    )
    return {
        "score": score,
        "feedback": feedback,
        "summary": "",
        "positives": [],
        "improvements": [],
        "preparation_needed": [],
        "detailed_evaluation": ""
    }
    