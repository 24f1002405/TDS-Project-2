from fastapi import FastAPI, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from typing import List
import os
import base64

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.api_route("/", methods=["GET", "POST"])
async def home(request: Request, files: List[UploadFile] = File(None)):
    if request.method == "GET":
        return {"message": "send data first"}
    
    if not files:
        return {"error": "No files uploaded"}

    # Read questions.txt
    question_file = next((f for f in files if f.filename == "questions.txt"), None)
    if not question_file:
        return {"error": "'questions.txt' file is missing"}
    question = (await question_file.read()).decode("utf-8").strip()

    # read all files
    all_files = {}
    for f in files:
        if f.filename != "questions.txt":
            content = await f.read()
            try:
                # Try UTF-8 text decode
                all_files[f.filename] = content.decode("utf-8").strip()
            except UnicodeDecodeError:
                # If binary, store base64 string
                all_files[f.filename] = base64.b64encode(content).decode("utf-8")

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

    local_scope = {"all_files": all_files}
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