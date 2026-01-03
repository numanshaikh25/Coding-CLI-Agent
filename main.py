import json
import os
from enum import Enum
from typing import Literal

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

from tools import (
    create_directory,
    execute_command,
    list_files,
    read_file,
    search_code,
    write_file,
)

load_dotenv()

client = OpenAI()


class StepType(str, Enum):
    START = "START"
    PLAN = "PLAN"
    TOOL = "TOOL"
    OUTPUT = "OUTPUT"


class StartStep(BaseModel):
    step: Literal["START"]
    content: str


class PlanStep(BaseModel):
    step: Literal["PLAN"]
    content: str


class ToolStep(BaseModel):
    step: Literal["TOOL"]
    tool: str
    input: str


class OutputStep(BaseModel):
    step: Literal["OUTPUT"]
    content: str


class AgentResponse(BaseModel):
    step: StepType
    content: str | None = None
    tool: str | None = None
    input: str | None = None


available_tools = {
    "read_file": read_file,
    "write_file": lambda args: write_file(*args.split("|||", 1)),  # file_path|||content
    "create_directory": create_directory,
    "list_files": list_files,
    "execute_command": execute_command,
    "search_code": lambda args: search_code(
        *args.split("|||")
    ),  # pattern|||directory|||extension
}

SYSTEM_PROMPT = """You are a helpful coding assistant with access to file system and code execution tools.
You must respond in JSON format with a "step" field and additional fields based on the step type.

Available tools:
- read_file: Read the contents of a file. Input: file_path (string)
- write_file: Write content to a file (creates or overwrites). Input: file_path|||content (separated by |||)
- create_directory: Create a new directory (and parent directories). Input: directory_path (string)
- list_files: List files and directories. Input: directory_path (string, default ".")
- execute_command: Execute a shell command. Input: command (string)
- search_code: Search for a pattern in code files. Input: pattern|||directory_path|||file_extension (separated by |||, last two are optional)

IMPORTANT: When creating new projects (websites, apps, etc.), ALWAYS:
1. First create a dedicated directory for the project using create_directory
2. Then create all project files inside that directory using proper paths
3. Use descriptive directory names (e.g., "bakery-website", "todo-app", "portfolio-site")

Step types:
- START: Echo the user's query. Fields: step, content
- PLAN: Your reasoning/thinking process. Fields: step, content
- TOOL: Call a tool. Fields: step, tool, input
- OUTPUT: Final response to user. Fields: step, content

You will receive OBSERVE messages with tool results after TOOL steps.

Rules:
1. Always start with a START step
2. Use PLAN steps to reason through the problem
3. Use TOOL step when you need to call a tool
4. After receiving OBSERVE, continue with PLAN or OUTPUT
5. End with OUTPUT step containing your final response
6. For write_file, use ||| to separate file_path and content
7. For search_code, use ||| to separate pattern, directory, and extension

Example 1:
User: What files are in the current directory?
START: { "step": "START", "content": "User wants to see files in current directory" }
PLAN: { "step": "PLAN", "content": "I need to use list_files tool" }
TOOL: { "step": "TOOL", "tool": "list_files", "input": "." }
OBSERVE: { "step": "OBSERVE", "tool": "list_files", "output": "[FILE] main.py\\n[DIR] src/" }
OUTPUT: { "step": "OUTPUT", "content": "The current directory contains:\\n- main.py (file)\\n- src/ (directory)" }

Example 2:
User: Create a hello.py file that prints Hello World
START: { "step": "START", "content": "User wants to create a hello.py file" }
PLAN: { "step": "PLAN", "content": "I need to write Python code to hello.py" }
TOOL: { "step": "TOOL", "tool": "write_file", "input": "hello.py|||print('Hello World')" }
OBSERVE: { "step": "OBSERVE", "tool": "write_file", "output": "Successfully wrote 20 characters to 'hello.py'" }
OUTPUT: { "step": "OUTPUT", "content": "Created hello.py with a simple print statement!" }

Example 3:
User: Find all TODO comments in Python files
START: { "step": "START", "content": "User wants to find TODO comments in Python files" }
PLAN: { "step": "PLAN", "content": "I'll use search_code to find TODO in .py files" }
TOOL: { "step": "TOOL", "tool": "search_code", "input": "TODO|||.|||.py" }
OBSERVE: { "step": "OBSERVE", "tool": "search_code", "output": "main.py:10: # TODO: Add error handling" }
OUTPUT: { "step": "OUTPUT", "content": "Found 1 TODO comment:\\n- main.py:10" }

Example 4 - Creating a new project:
User: Build a landing page for a bakery website
START: { "step": "START", "content": "User wants to build a bakery landing page" }
PLAN: { "step": "PLAN", "content": "I need to create a dedicated directory first, then create HTML, CSS, and JS files" }
TOOL: { "step": "TOOL", "tool": "create_directory", "input": "bakery-website" }
OBSERVE: { "step": "OBSERVE", "tool": "create_directory", "output": "Successfully created directory 'bakery-website'" }
PLAN: { "step": "PLAN", "content": "Now I'll create index.html inside bakery-website/" }
TOOL: { "step": "TOOL", "tool": "write_file", "input": "bakery-website/index.html|||<!DOCTYPE html>..." }
OBSERVE: { "step": "OBSERVE", "tool": "write_file", "output": "Successfully wrote 2500 characters to 'bakery-website/index.html'" }
PLAN: { "step": "PLAN", "content": "Now I'll create styles.css" }
TOOL: { "step": "TOOL", "tool": "write_file", "input": "bakery-website/styles.css|||/* Modern bakery styles */..." }
OBSERVE: { "step": "OBSERVE", "tool": "write_file", "output": "Successfully wrote 1800 characters to 'bakery-website/styles.css'" }
PLAN: { "step": "PLAN", "content": "Finally, I'll create script.js" }
TOOL: { "step": "TOOL", "tool": "write_file", "input": "bakery-website/script.js|||// Interactive features..." }
OBSERVE: { "step": "OBSERVE", "tool": "write_file", "output": "Successfully wrote 950 characters to 'bakery-website/script.js'" }
OUTPUT: { "step": "OUTPUT", "content": "Created a beautiful bakery landing page in the bakery-website/ directory with:\\n- index.html (hero, menu, about, contact sections)\\n- styles.css (modern gradients, animations, responsive design)\\n- script.js (smooth scrolling, form validation)\\n\\nOpen bakery-website/index.html in a browser to view it!" }
"""


def run_agent(user_query: str) -> str:
    """Run the coding agent with explicit chain of thought reasoning."""
    print(f"\n{'='*50}")
    print(f"User Query: {user_query}")
    print(f"{'='*50}\n")

    message_history = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query},
    ]

    while True:
        try:
            response = client.beta.chat.completions.parse(
                model="gpt-5-mini",
                response_format=AgentResponse,
                messages=message_history,
            )
        except Exception as e:
            print(f"❌ Error calling LLM: {str(e)}")
            return "Error: Failed to get response from LLM"

        parsed_result = response.choices[0].message.parsed
        raw_result = response.choices[0].message.content
        message_history.append({"role": "assistant", "content": raw_result})

        if parsed_result.step == StepType.START:
            print(f"🔥 {parsed_result.content}")
            continue

        if parsed_result.step == StepType.PLAN:
            print(f"🧠 {parsed_result.content}")
            continue

        if parsed_result.step == StepType.TOOL:
            tool_to_call = parsed_result.tool
            tool_input = parsed_result.input
            print(
                f"🔧 Calling: {tool_to_call}({tool_input[:50]}...)"
                if len(tool_input) > 50
                else f"🔧 Calling: {tool_to_call}({tool_input})"
            )

            try:
                tool_response = available_tools[tool_to_call](tool_input)
                print(
                    f"🔧 Result: {tool_response[:200]}..."
                    if len(tool_response) > 200
                    else f"🔧 Result: {tool_response}"
                )
            except Exception as e:
                tool_response = f"Error executing tool: {str(e)}"
                print(f"❌ Error: {tool_response}")

            message_history.append(
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "step": "OBSERVE",
                            "tool": tool_to_call,
                            "input": tool_input,
                            "output": tool_response,
                        }
                    ),
                }
            )
            continue

        if parsed_result.step == StepType.OUTPUT:
            print(f"🤖 {parsed_result.content}")
            return parsed_result.content

    return "No response generated"


def main():
    print("Coding Agent (type 'quit' to exit)")
    print("-" * 40)

    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        if not user_input:
            continue

        run_agent(user_input)


if __name__ == "__main__":
    main()
