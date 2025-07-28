from fastapi import FastAPI, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from google import genai
import os

os.environ['GEMINI_API_KEY'] = "AIzaSyBKMCKffo3wvzG9qbXb1IX-K8DOWEvyEek"
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.api_route("/", methods=["GET", "POST"])
async def home(request: Request, file: UploadFile = File(None)):
    if request.method == "GET":
        return {"message": "send data first"}
    
    if not file:
        return {"error": "No file uploaded"}

    # load question
    question = (await file.read()).decode("utf-8").strip()

    # prepare prompt
    with open("prompt.md", "r") as f:
        prompt = f.read().strip()
    prompt = prompt.replace("{{question}}", question)
    
    # send llm request
    client = genai.Client()
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=prompt,
    )

    local_scope = {}
    exec(clean_python_code(response.text), {}, local_scope)
    answers = local_scope.get("answers")
    
    return answers

def clean_python_code(code_str: str) -> str:
    code_str = code_str.strip()
    if code_str.startswith("```python"):
        code_str = code_str.replace("```python", "").strip()
    if code_str.endswith("```"):
        code_str = code_str[:-3].strip()
    print(f"Cleaned code: {code_str}")
    
    return code_str