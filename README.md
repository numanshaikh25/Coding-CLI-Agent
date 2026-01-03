# Coding Agent

An AI coding assistant that uses explicit **Chain-of-Thought (CoT)** reasoning with structured outputs.

## How It Works

The agent uses a loop-based architecture where the LLM explicitly outputs its reasoning steps in structured JSON format. This makes the model's thought process transparent and debuggable.

### Step Types

| Step | Purpose | Output |
|------|---------|--------|
| `START` | Echo the user's query | Content |
| `PLAN` | Reasoning/thinking steps | Content |
| `TOOL` | Request to call a tool | Tool name + input |
| `OBSERVE` | Tool execution result (injected by system) | Tool output |
| `OUTPUT` | Final response to user | Content |

### Available Tools

| Tool | Purpose | Input Format |
|------|---------|--------------|
| `read_file` | Read file contents | `file_path` |
| `write_file` | Create or overwrite a file | `file_path\|\|\|content` |
| `create_directory` | Create a new directory | `directory_path` |
| `list_files` | List directory contents | `directory_path` (default: `.`) |
| `execute_command` | Run shell commands | `command` |
| `search_code` | Search for patterns in code | `pattern\|\|\|directory\|\|\|extension` |

**Project Organization:** The agent automatically creates dedicated directories for new projects, keeping your workspace organized.

### Flow Example - Building a Project

```
You: Build a landing page for a bakery website

🔥 START: User wants to build a bakery landing page
🧠 PLAN: I need to create a dedicated directory first
🔧 TOOL: create_directory(bakery-website)
🔧 OBSERVE: Successfully created directory 'bakery-website'
🧠 PLAN: Now I'll create index.html inside bakery-website/
🔧 TOOL: write_file(bakery-website/index.html|||<!DOCTYPE html>...)
🔧 OBSERVE: Successfully wrote 2500 characters to 'bakery-website/index.html'
🧠 PLAN: Now I'll create styles.css
🔧 TOOL: write_file(bakery-website/styles.css|||/* Modern styles */...)
🔧 OBSERVE: Successfully wrote 1800 characters to 'bakery-website/styles.css'
🧠 PLAN: Finally, I'll create script.js
🔧 TOOL: write_file(bakery-website/script.js|||// Interactive features...)
🔧 OBSERVE: Successfully wrote 950 characters to 'bakery-website/script.js'
🤖 OUTPUT: Created a beautiful bakery landing page in bakery-website/ directory!
```

## Tech Stack

- **Python 3.12+**
- **OpenAI GPT-4o** - LLM with structured outputs
- **Pydantic** - Response validation and type safety
- **httpx** - HTTP client (inherited from weather agent)
- **python-dotenv** - Environment variable management
- **uv** - Modern Python package manager

## Setup

1. Clone or navigate to the repository

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Create a `.env` file:
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

4. Run the agent:
   ```bash
   uv run python main.py
   ```

## Project Structure

```
coding-agent/
├── main.py          # Agent loop and Pydantic models
├── tools.py         # Tool implementations
├── pyproject.toml   # Dependencies
├── .env.example     # Environment template
├── .gitignore       # Git ignore rules
└── README.md        # This file
```

## Usage Examples

### Example 1: List Files
```
You: What files are in the current directory?

🔥 START: User wants to see files in current directory
🧠 PLAN: I need to use list_files tool
🔧 TOOL: list_files(.)
🔧 OBSERVE: [FILE] main.py (4818 bytes)
             [FILE] tools.py (5124 bytes)
             [DIR]  src/
🤖 OUTPUT: The current directory contains:
- main.py (4818 bytes)
- tools.py (5124 bytes)
- src/ (directory)
```

### Example 2: Search Code
```
You: Find all TODO comments in Python files

🔥 START: User wants to find TODO comments
🧠 PLAN: I'll search for "TODO" in .py files
🔧 TOOL: search_code(TODO|||.|||.py)
🔧 OBSERVE: main.py:10: # TODO: Add error handling
             utils.py:25: # TODO: Optimize this function
🤖 OUTPUT: Found 2 TODO comments:
- main.py:10: Add error handling
- utils.py:25: Optimize this function
```

### Example 3: Create and Test Code
```
You: Create a function to calculate fibonacci numbers

🔥 START: User wants a fibonacci function
🧠 PLAN: I'll create a Python file with the function
🔧 TOOL: write_file(fibonacci.py|||def fibonacci(n):...)
🔧 OBSERVE: Successfully wrote 125 characters to 'fibonacci.py'
🧠 PLAN: Now let me test it
🔧 TOOL: execute_command(python fibonacci.py)
🔧 OBSERVE: STDOUT: 0 1 1 2 3 5 8 13 21 34
🤖 OUTPUT: Created fibonacci.py and tested it successfully!
```

## Adding New Tools

1. Implement the tool function in `tools.py`:
   ```python
   def analyze_code(file_path: str) -> str:
       """Analyze code structure and complexity."""
       # Implementation
       return analysis_result
   ```

2. Add to `available_tools` in `main.py`:
   ```python
   available_tools = {
       "read_file": read_file,
       "write_file": lambda args: write_file(*args.split("|||", 1)),
       "analyze_code": analyze_code,  # New tool
       # ... other tools
   }
   ```

3. Update the system prompt to describe the new tool:
   ```python
   SYSTEM_PROMPT = """...
   Available tools:
   - analyze_code: Analyze code structure. Input: file_path (string)
   ...
   """
   ```

## Architecture Notes

### Chain-of-Thought Pattern
The explicit CoT pattern makes the agent's reasoning visible at each step:
- **START**: Confirms understanding of user request
- **PLAN**: Shows internal reasoning before actions
- **TOOL**: Executes actions when needed
- **OBSERVE**: Receives feedback from tools
- **OUTPUT**: Delivers final response

### Structured Outputs
Using Pydantic with OpenAI's structured output API ensures:
- Type safety at runtime
- Consistent response format
- Easier debugging and logging
- Validation of tool inputs




