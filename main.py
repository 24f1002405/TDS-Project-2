from fastapi import FastAPI, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from typing import List
import os
import base64
import asyncio
import time
import random

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.api_route("/", methods=["GET", "POST"])
async def home(
    request: Request,
    question_file: UploadFile = File(None, alias="questions.txt")
):
    start_time = time.time()
    request_id = random.randint(1000, 9999)

    # incorrect HTTP method
    if request.method == "GET":
        return {"message": "send data first"}
    print(f"[{request_id}]: Request ID: {request_id}")
    print(f"[{request_id}]: Received {request.method} request from {request.client.host}")

    # No question file uploaded
    if not question_file:
        return {"message": "No questions.txt uploaded"}
    question = (await question_file.read()).decode("utf-8").strip()

    # read all files
    form = await request.form()
    all_files = {}
    for key, f in form.items():
        if key != "questions.txt":
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

        print(f"[{request_id}]: Files Received: {list(all_files.keys())}")

    # send llm request
    response = await asyncio.to_thread(get_llm_response, prompt, request_id)
    print(f"[{request_id}]: LLM response received")

    # execute code and get answers
    local_scope = {"all_files": all_files}
    try:
        print(f"[{request_id}]: Executing code...")
        exec(clean_python_code(response.text, request_id), {}, local_scope)
    except Exception as e:
        print(f"[{request_id}]: {e}")
        return {"message": "Error executing code"}
    answers = local_scope.get("answers")
    
    print(f"[{request_id}]: Successful response sent back in {time.time() - start_time}s !!!")
    return answers

def clean_python_code(code_str: str, request_id: int) -> str:
    code_str = code_str.strip()
    if code_str.startswith("```python"):
        code_str = code_str.replace("```python", "").strip()
    if code_str.endswith("```"):
        code_str = code_str[:-3].strip()
    
    print(code_str)
    return code_str

def get_llm_response(prompt: str, request_id: int, retries: int = 3):
    client = genai.Client()

    for attempt in range(1, retries + 1):
        try:
            print(f"[{request_id}]: Attempt {attempt} to get response from LLM...")
            response = client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prompt,
            )
            if not response or not hasattr(response, 'text') or not response.text:
                raise ValueError(f"[{request_id}]: Empty response from LLM")
            
            return response
        except Exception as e:
            print(f"[{request_id}]: Attempt {attempt} failed with {e}. Retrying in 60s...")
            time.sleep(60)
    
    raise RuntimeError(f"[{request_id}]: Failed to get a valid response from the LLM after {retries} attempts")