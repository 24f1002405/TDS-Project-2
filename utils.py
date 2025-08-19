import os
from google import genai
from google.genai import types
import asyncio
import importlib

# to avoid matplotlib backend issues in headless environments
import matplotlib
matplotlib.use('Agg')

def clean_python_code(code_str: str) -> str:
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

def import_libs_from_code_str(code_str: str):
    namespace = globals()

    code_lines = code_str.strip().splitlines()
    for line in code_lines:
        if 'import' not in line:
            break
        if line.startswith('#'):
            continue
        
        line = line.strip()
        if line.startswith('import'):
            modules = [m.strip() for m in line[7:].split(',')]
            for m in modules:
                if ' as ' in m:
                    m, alias = m.split(' as ')
                else:
                    alias = m
                imported_module = importlib.import_module(m)
                namespace[alias] = imported_module
        else:
            base_module_str = line.split(' ')[1]
            if '.' not in base_module_str:
                imported_module = importlib.import_module(base_module_str)
            else:
                parts = base_module_str.split('.')
                imported_module = importlib.import_module(parts[0])
                for part in parts[1:]:
                    imported_module = getattr(imported_module, part)

            sub_modules = [
                m.strip()
                for m in line.split('import')[1].strip().split(',')
            ]
            for m in sub_modules:
                if ' as ' in m:
                    m, alias = m.split(' as ')
                else:
                    alias = m
                imported_sub_module = getattr(imported_module, m)
                namespace[alias] = imported_sub_module

def execute_code(code_str: str, all_files: dict):
    # import libraries
    import_libs_from_code_str(code_str)

    # remove import lines
    code_starting_line = 0
    code_lines = code_str.strip().split('\n')
    for i in range(len(code_lines)):
        if 'import' not in code_lines[i]:
            code_starting_line = i
            break
    code_str = '\n'.join(code_lines[code_starting_line:]).strip()
    
    local_scope = {'all_files': all_files}
    response = {'success': None, 'error': None, 'answers': None}
    try:
        exec(code_str, globals(), local_scope)
        response['success'] = True
        response['answers'] = local_scope.get('answers', None)
    except Exception as e:
        response['success'] = False
        response['error'] = str(e)
    
    return response
