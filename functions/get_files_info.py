import os 
from config import MAX_CHARS
import subprocess as sub 
from google.genai import types

schema_get_files_info = types.FunctionDeclaration(
    name="get_files_info",
    description="Lists files in the specified directory along with their sizes, constrained to the working directory.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "directory": types.Schema(
                type=types.Type.STRING,
                description="The directory to list files from, relative to the working directory. If not provided, lists files in the working directory itself.",
            ),
        },
    ),
)

schema_get_file_content = types.FunctionDeclaration(
    name="get_file_content",
    description="Lists files in the specified directory along with their sizes, constrained to the working directory.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "directory": types.Schema(
                type=types.Type.STRING,
                description="The directory to list files from, relative to the working directory. If not provided, lists files in the working directory itself.",
            ),
        },
    ),
)

schema_write_file = types.FunctionDeclaration(
    name="write_file",
    description="Lists files in the specified directory along with their sizes, constrained to the working directory.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "directory": types.Schema(
                type=types.Type.STRING,
                description="The directory to list files from, relative to the working directory. If not provided, lists files in the working directory itself.",
            ),
        },
    ),
)

schema_run_python_file = types.FunctionDeclaration(
    name="run_python_file",
    description="Lists files in the specified directory along with their sizes, constrained to the working directory.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "directory": types.Schema(
                type=types.Type.STRING,
                description="The directory to list files from, relative to the working directory. If not provided, lists files in the working directory itself.",
            ),
        },
    ),
)

    
available_functions = types.Tool(
    function_declarations=[
        schema_get_files_info, 
        schema_write_file, schema_run_python_file,schema_get_file_content
    ]
)

    
    
system_prompt = """
    You are a helpful AI coding agent.

    When a user asks a question or makes a request, make a function call plan. You can perform the following operations:

    - List files and directories
    - Read file contents 
    - Execute Python files with optional arguments
    - Write or overwrite files 

    All paths you provide should be relative to the working directory. You do not need to specify the working directory in your function calls as it is automatically injected for security reasons.
    """
config=types.GenerateContentConfig(
    tools=[available_functions], system_instruction=system_prompt
)
function_call_part = types.FunctionCall()
f"Calling function: {function_call_part.name}({function_call_part.args})"
    


def get_files_info(working_directory, directory="."):
    combined = os.path.join(working_directory, directory)
    if not os.path.abspath(combined).startswith(os.path.abspath(working_directory)):
        return f'Error: Cannot list "{directory}" as it is outside the permitted working directory'
    if not os.path.isdir(combined):
        return f'Error: "{directory}" is not a directory'
    
    try:
        lists = os.listdir(combined)
        results_line = []
        for item in lists: 
            item_path = os.path.join(combined,item)
            line= f"- {item}: file_size={os.path.getsize(item_path)} bytes, is_dir={os.path.isdir(item_path)}"
            results_line.append(line)
        return "\n".join(results_line)
    except Exception as e:
        return f"Error: {str(e)}"

def get_file_content(working_directory, file_path):
    combined = os.path.join(working_directory,file_path)
    if not os.path.abspath(combined).startswith(os.path.abspath(working_directory)):
        return f'Error: Cannot read "{file_path}" as it is outside the permitted working directory'
    if not os.path.isfile(combined):
        return f'Error: File not found or is not a regular file: "{file_path}"'
    try:
        
        with open(combined,"r") as f:
            file_content = f.read(MAX_CHARS)
            one_more = f.read(1)
            if one_more:
                file_content += f'[...File "{file_path}" truncated at 10000 characters]'
            return file_content

    except Exception as e:
        return f"Error: {str(e)}"
def write_file(working_directory, file_path, content):
    combine = os.path.join(working_directory, file_path)
    if not os.path.abspath(combine).startswith(os.path.abspath(working_directory)):
        return f'Error: Cannot write to "{file_path}" as it is outside the permitted working directory'
    if not os.path.exists(combine):
        os.makedirs(os.path.dirname(combine),exist_ok=True)


    try:
        with open(combine, "w") as f:
            f.write(content)
            return f'Successfully wrote to "{file_path}" ({len(content)} characters written)'
    except Exception as e:
        return f"Error: {str(e)}"


def run_python_file(working_directory, file_path, args=[]):
    combine = os.path.join(working_directory, file_path)
    if not os.path.abspath(combine).startswith(os.path.abspath(working_directory)):
        return f'Error: Cannot execute "{file_path}" as it is outside the permitted working directory'
    if not os.path.exists(combine):
        return f'Error: File "{file_path}" not found.'
    if not combine.endswith('.py'):
        return f'Error: "{file_path}" is not a Python file.'
    try:
        command = ["python", file_path] + args
        runner =sub.run(command, capture_output=True, cwd=working_directory, timeout=30 )
        stdout_text = runner.stdout.decode() if runner.stdout else ""
        stderr_text = runner.stderr.decode() if runner.stderr else ""
        
        if not stdout_text and not stderr_text:
           return "No output produce."
        output = f"STDOUT: {stdout_text}STDERR: {stderr_text} "
        
        if runner.returncode != 0: 
           output += f"Process exited with code {runner.returncode}"

        return output 
    except Exception as e:
        return f"Error: executing Python file: {e}"
def call_function(function_call_part, verbose=False):
    function_call_part = types.FunctionCall()
    if verbose == True: 
        print(f"calling function {function_call_part.name}({function_call_part.args})")
    print(f" - Calling function: {function_call_part.name} ")
    function_name = { "function":["get_files_info","get_file_content","write_file","run_python_file"]}
    some_args = {"working_directory":"./calculator"}
    if function_call_part.name == "get_files_info":
        get_files_info(**some_args)
    if function_call_part.name == "get_file_content":
        get_file_content(**some_args)
    if function_call_part.name == "write_file":
        write_file(**some_args)
    if function_call_part.name == "run_python_file":
        run_python_file(**some_args)
    if function_call_part.name:
        return types.Content(
            role="tool",
            parts=[
                types.Part.from_function_response(
                    name=function_name, 
                    response={"error": f"Unknown function: {function_name}"}
                )
            ]
        ) 