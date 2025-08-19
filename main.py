from fastapi import FastAPI, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import asyncio
import time
import random
import utils

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

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
    binary_files = []
    for key, f in form.items():
        if key != "questions.txt":
            content = await f.read()
            try:
                # Try UTF-8 text decode
                all_files[f.filename] = content.decode("utf-8").strip()
            except UnicodeDecodeError:
                # If binary, store binary data
                binary_files.append({
                    "filename": f.filename,
                    "content": content,
                    "mime_type": f.content_type or utils.get_mime_type(f.filename)
                })
    if binary_files:
        print(f"[{request_id}]: Binary files received: {[f['filename'] for f in binary_files]}")

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
    llm_response = await utils.get_llm_response(prompt, request_id, binary_files)
    print(f"[{request_id}]: LLM response received")

    # execute code and get answers
    print(f"[{request_id}]: Executing code:")
    code_str = utils.clean_python_code(llm_response)
    code_exec_response = await asyncio.to_thread(utils.execute_code, code_str, all_files)

    if not code_exec_response['success']:
        print(f"[{request_id}]: Error Executing Code: {code_exec_response['error']}")

        # error correction prompt
        with open("error-correction-prompt.md", "r") as f:
            prompt = f.read().strip()
        prompt = prompt.replace("{{question}}", question)
        prompt = prompt.replace("{{error}}", code_exec_response['error'])
        prompt = prompt.replace("{{code}}", llm_response)
        print(f"[{request_id}]: Sending LLM request for error correction")

        # get corrected code from LLM
        llm_response = await utils.get_llm_response(prompt, request_id, binary_files)
        print(f"[{request_id}]: LLM response received")

        # execute corrected code
        print(f"[{request_id}]: Executing corrected code:")
        code_str = utils.clean_python_code(llm_response)
        code_exec_response = await asyncio.to_thread(utils.execute_code, code_str, all_files)

        if not code_exec_response['success']:
            print(f"[{request_id}]: Error executing corrected code: {code_exec_response['error']}")
            print(f"[{request_id}]: Sending back failure msg after {time.time() - start_time}s")
            return {'message': f"Error executing corrected code: {code_exec_response['error']}"}

    print(f"[{request_id}]: Successful response sent back in {time.time() - start_time}s !!!")
    return code_exec_response['answers']