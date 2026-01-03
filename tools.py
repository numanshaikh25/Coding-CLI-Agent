import os
import subprocess
from pathlib import Path
from typing import Any


def read_file(file_path: str) -> str:
    """Read the contents of a file.

    Args:
        file_path: Path to the file to read (relative or absolute)

    Returns:
        File contents as a string, or error message
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return f"Error: File '{file_path}' does not exist"

        if not path.is_file():
            return f"Error: '{file_path}' is not a file"

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        return content if content else "(Empty file)"
    except Exception as e:
        return f"Error reading file: {str(e)}"


def write_file(file_path: str, content: str) -> str:
    """Write content to a file (creates or overwrites).

    Args:
        file_path: Path to the file to write
        content: Content to write to the file

    Returns:
        Success message or error
    """
    try:
        path = Path(file_path)

        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

        return f"Successfully wrote {len(content)} characters to '{file_path}'"
    except Exception as e:
        return f"Error writing file: {str(e)}"


def create_directory(directory_path: str) -> str:
    """Create a new directory (and parent directories if needed).

    Args:
        directory_path: Path to the directory to create

    Returns:
        Success message or error
    """
    try:
        path = Path(directory_path)

        if path.exists():
            if path.is_dir():
                return f"Directory '{directory_path}' already exists"
            else:
                return f"Error: '{directory_path}' exists but is not a directory"

        # Create directory and all parent directories
        path.mkdir(parents=True, exist_ok=True)

        return f"Successfully created directory '{directory_path}'"
    except Exception as e:
        return f"Error creating directory: {str(e)}"


def list_files(directory_path: str = ".") -> str:
    """List files and directories in a given path.

    Args:
        directory_path: Path to the directory to list (default: current directory)

    Returns:
        Formatted list of files and directories, or error message
    """
    try:
        path = Path(directory_path)

        if not path.exists():
            return f"Error: Directory '{directory_path}' does not exist"

        if not path.is_dir():
            return f"Error: '{directory_path}' is not a directory"

        items = []
        for item in sorted(path.iterdir()):
            if item.is_dir():
                items.append(f"[DIR]  {item.name}/")
            else:
                size = item.stat().st_size
                items.append(f"[FILE] {item.name} ({size} bytes)")

        if not items:
            return f"Directory '{directory_path}' is empty"

        return "\n".join(items)
    except Exception as e:
        return f"Error listing directory: {str(e)}"


def execute_command(command: str) -> str:
    """Execute a shell command safely.

    Args:
        command: Shell command to execute

    Returns:
        Command output (stdout + stderr) or error message
    """
    try:
        # Security: Block potentially dangerous commands
        dangerous_keywords = ['rm -rf /', 'dd', 'mkfs', 'format', ':(){:|:&};:']
        if any(keyword in command.lower() for keyword in dangerous_keywords):
            return "Error: Command blocked for safety reasons"

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )

        output = []
        if result.stdout:
            output.append(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            output.append(f"STDERR:\n{result.stderr}")
        if result.returncode != 0:
            output.append(f"Exit code: {result.returncode}")

        return "\n".join(output) if output else "(No output)"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds"
    except Exception as e:
        return f"Error executing command: {str(e)}"


def search_code(pattern: str, directory_path: str = ".", file_extension: str = "") -> str:
    """Search for a pattern in code files.

    Args:
        pattern: Text pattern to search for
        directory_path: Directory to search in (default: current directory)
        file_extension: Filter by file extension (e.g., '.py', '.js')

    Returns:
        List of matches with file paths and line numbers
    """
    try:
        path = Path(directory_path)

        if not path.exists():
            return f"Error: Directory '{directory_path}' does not exist"

        matches = []
        search_count = 0

        # Search recursively
        for file_path in path.rglob('*'):
            # Skip directories and hidden files
            if file_path.is_dir() or file_path.name.startswith('.'):
                continue

            # Filter by extension if specified
            if file_extension and not file_path.name.endswith(file_extension):
                continue

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        if pattern.lower() in line.lower():
                            matches.append(
                                f"{file_path.relative_to(path)}:{line_num}: {line.strip()}"
                            )
                search_count += 1
            except Exception:
                # Skip files that can't be read
                continue

        if not matches:
            return f"No matches found for '{pattern}' in {search_count} files"

        # Limit results to avoid overwhelming output
        if len(matches) > 50:
            return "\n".join(matches[:50]) + f"\n... ({len(matches) - 50} more matches)"

        return "\n".join(matches)
    except Exception as e:
        return f"Error searching code: {str(e)}"
