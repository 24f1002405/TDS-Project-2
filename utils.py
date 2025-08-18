import os
from google import genai
from google.genai import types
import asyncio

def clean_python_code(code_str: str, request_id: int) -> str:
    code_str = code_str.strip()
    if code_str.startswith("```python"):
        code_str = code_str.replace("```python", "").strip()
    if code_str.endswith("```"):
        code_str = code_str[:-3].strip()
    
    print(code_str)
    return code_str

def get_mime_type(file_name: str) -> str:
    ext = os.path.splitext(file_name)[1].lower()
    if ext in ['.jpg', '.jpeg']:
        return 'image/jpeg'
    elif ext == '.png':
        return 'image/png'
    elif ext == '.pdf':
        return 'application/pdf'
    else:
        return 'application/octet-stream'

async def get_llm_response(prompt: str, request_id: int, binary_files: list = None, retries: int = 3):
    for attempt in range(1, retries + 1):
        try:
            print(f"[{request_id}]: Attempt {attempt} to get response from LLM...")

            client = genai.Client()

            # sending request without binary files
            if not binary_files:
                response = await client.aio.models.generate_content(
                    model="gemini-2.5-pro",
                    contents=prompt,
                )
            # sending request with binary files
            else:
                contents_with_binary = [
                    types.Part.from_bytes(
                        data=f['content'],
                        mime_type=f['mime_type'],
                    )
                    for f in binary_files
                ]
                contents_with_binary.append(prompt)

                response = await client.aio.models.generate_content(
                    model="gemini-2.5-pro",
                    contents=contents_with_binary,
                )

            # check for invalid response
            if not response or not hasattr(response, 'text') or not response.text:
                raise ValueError(f"[{request_id}]: Empty response from LLM")
            
            return response.text
        except Exception as e:
            print(f"[{request_id}]: Attempt {attempt} failed with {e}. Retrying in 60s...")
            await asyncio.sleep(60)
    
    raise RuntimeError(f"[{request_id}]: Failed to get a valid response from the LLM after {retries} attempts")