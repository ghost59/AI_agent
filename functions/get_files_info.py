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
    description="Reads and returns the content of a specified file, constrained to the working directory.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "directory": types.Schema(
                type=types.Type.STRING,
                description="The file path to read from, relative to the working directory.",
            ),
        },
        required=["directory"],  # Make it required
    ),
)

schema_write_file = types.FunctionDeclaration(
    name="write_file",
    description="Writes content to a file in the specified path, constrained to the working directory.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "directory": types.Schema(
                type=types.Type.STRING,
                description="The file path to write to, relative to the working directory.",
            ),
            "content": types.Schema(
                type=types.Type.STRING,
                description="The content to write to the file.",
            ),
        },
        required=["directory", "content"],  # Both parameters are required
    ),
)

schema_run_python_file = types.FunctionDeclaration(
    name="run_python_file",
    description="Executes a Python file in the specified working directory.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "directory": types.Schema(
                type=types.Type.STRING,
                description="The Python file path to execute, relative to the working directory.",
            ),
            "args": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(type=types.Type.STRING),
                description="Optional command line arguments to pass to the Python script.",
            ),
        },
        required=["directory"],  # Only file path is required, args are optional
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
    function_map = {
        "get_files_info": get_files_info,
        "get_file_content" : get_file_content,
        "write_file": write_file, 
        "run_python_file": run_python_file
    }
    # Fix arguments for each function
    fixed_args = function_call_part.args.copy()

    if function_call_part.name == "get_files_info":
    # This function actually expects 'directory' - don't change it
        pass

    elif function_call_part.name in ["get_file_content", "write_file", "run_python_file"]:
        # These functions expect 'file_path' but LLM provides 'directory'
        if 'directory' in fixed_args:
            fixed_args['file_path'] = fixed_args.pop('directory')

    # Remove any remaining 'directory' key (shouldn't be needed now)
    if 'directory' in fixed_args:
        fixed_args.pop('directory')

    combined_args = {**{"working_directory": "./calculator"}, **fixed_args}
    
    if verbose == True: 
        print(f"Calling function: {function_call_part.name}({function_call_part.args})")
    else: 
        print(f" - Calling function: {function_call_part.name}")
        
    if function_call_part.name not in function_map: 
        return types.Content(
            role="tool",
            parts=[
                types.Part.from_function_response(
                    name=function_call_part.name,
                    response={"error": f"Unknown function: {function_call_part.name}"},
                )
            ],
        )
    
    # Use the combined_args you already created - don't recreate them!
    func = function_map[function_call_part.name]
    function_result = func(**combined_args)  # Use the fixed combined_args

    return types.Content(
        role="tool",
        parts=[
            types.Part.from_function_response(
                name=function_call_part.name,
                response={"result": function_result},
            )
        ],
    )
    