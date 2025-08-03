import os 
from dotenv import load_dotenv
from google import genai
import sys
from google.genai import types
from functions.get_files_info import  config
load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)
prompt = sys.argv[1]


response = client.models.generate_content(
    model="gemini-2.0-flash-001",contents=prompt,
    config=config
)
if response.function_calls:
    function_call_part = response.function_calls[0]
    print(f"Calling function: {function_call_part.name}({function_call_part.args})")
else: 
    print(response.text)

if len(sys.argv) == 1:
    sys.exit(1)
if sys.argv[-1] == "--verbose":
    print(f"User prompt:{prompt}")
    print(f'Prompt tokens: {response.usage_metadata.prompt_token_count}')
    print(f'Response tokens: {response.usage_metadata.candidates_token_count}')
    print(response.text)
     
else:
    print(response.text)
    sys.exit(0)