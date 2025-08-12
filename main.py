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
    # incorrect HTTP method
    if request.method == "GET":
        return {"message": "send data first"}
    
    # No files uploaded
    if not files:
        return {"message": "No files uploaded"}

    # Read questions.txt
    question_file = next((f for f in files if f.filename == "questions.txt"), None)
    if not question_file:
        return {"message": "'questions.txt' file is missing"}
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
                # all_files[f.filename] = base64.b64encode(content).decode("utf-8")
                pass

    # prepare prompt
    with open("prompt.md", "r") as f:
        prompt = f.read().strip()
    prompt = prompt.replace("{{question}}", question)

    if all_files:
        prompt += "\n\n### Supporting Files' Details\n\n"
        for filename, content in all_files.items():
            file_info = f"- **{filename}**"
            if filename.endswith('.csv'):
                file_info += f": {content.split('\n')[0]}"
            
            prompt += file_info + "\n"

    # send llm request
    client = genai.Client()
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=prompt,
    )

    local_scope = {"all_files": all_files}
    try:
        exec(clean_python_code(response.text), {}, local_scope)
    except Exception as e:
        print(f"Error executing code: {e}")
        return {"message": "Error executing code"}
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