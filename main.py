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
    # request init
    start_time = time.time()
    request_id = random.randint(1000, 9999)

    # incorrect HTTP method
    if request.method == "GET":
        return {"message": "send data first"}
    print(f"[{request_id}]: Request ID: {request_id}")
    print(f"[{request_id}]: Received {request.method} request from {request.client.host}")

    # read files
    if not question_file:
        return {"message": "No questions.txt uploaded"}
    question = (await question_file.read()).decode("utf-8").strip()
    text_files, binary_files = await utils.get_files(request)
    
    if text_files:
        print(f"[{request_id}]: Files Received: {list(text_files.keys())}")
    if binary_files:
        print(f"[{request_id}]: Binary files received: {[f['filename'] for f in binary_files]}")

    # prepare prompt and get LLM response
    prompt = utils.prepare_prompt(question, text_files)
    llm_response = await utils.get_llm_response(prompt, request_id, binary_files)

    # execute code and get answers
    print(f"[{request_id}]: Executing code:")
    code_str = utils.clean_python_code(llm_response)
    code_exec_response = await asyncio.to_thread(utils.execute_code, code_str, text_files)

    if not code_exec_response['success']:
        print(f"[{request_id}]: Error Executing Code: {code_exec_response['error']}")

        # error correction prompt
        prompt = utils.prepare_error_prompt(question, code_exec_response['error'], llm_response)
        
        # get corrected code from LLM
        print(f"[{request_id}]: Sending LLM request for error correction")
        llm_response = await utils.get_llm_response(prompt, request_id, binary_files)

        # execute corrected code
        print(f"[{request_id}]: Executing corrected code:")
        code_str = utils.clean_python_code(llm_response)
        code_exec_response = await asyncio.to_thread(utils.execute_code, code_str, text_files)

        if not code_exec_response['success']:
            print(f"[{request_id}]: Error executing corrected code: {code_exec_response['error']}")
            print(f"[{request_id}]: Sending back failure msg after {time.time() - start_time}s")
            return {'message': f"Error executing corrected code: {code_exec_response['error']}"}

    print(f"[{request_id}]: Successful response sent back in {time.time() - start_time}s !!!")
    return code_exec_response['answers']