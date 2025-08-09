import os 
from dotenv import load_dotenv
from google import genai
import sys
from google.genai import types
from functions.get_files_info import  config, call_function
load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)
prompt = sys.argv[1]
verbose = len(sys.argv) > 2 and sys.argv[-1] == "--verbose"

response = client.models.generate_content(
    model="gemini-2.0-flash-001",contents=prompt,
    config=config
)
if response.function_calls:
    function_call_part = response.function_calls[0]
    function_call_result = call_function(function_call_part, verbose)
    if not function_call_result.parts[0].function_response.response:
        raise Exception("Function call failed")
    if verbose:
        print(f"-> {function_call_result.parts[0].function_response.response}")
else: 
    print(response.text)

if sys.argv[-1] == "--verbose":
    print(f"User prompt:{prompt}")
    print(f'Prompt tokens: {response.usage_metadata.prompt_token_count}')
    print(f'Response tokens: {response.usage_metadata.candidates_token_count}')
    print(response.text)
     
else:
    print(response.text)
    sys.exit(0)