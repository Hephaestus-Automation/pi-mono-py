"""
Coding Agent - Example of a code-focused agent with developer tools.

This example demonstrates:
- Custom tools for code editing and file operations
- Tool validation and error handling
- Event-driven interaction
- Multi-turn conversations with code context

Usage:
    cd pi-mono-py
    uv run --directory examples python 07_coding_agent.py
"""

import asyncio
import os
from pathlib import Path
from typing import Any

from pi_agent import Agent, AgentTool, AgentToolResult
from pi_agent.tools import (
    ToolValidationError,
    validate_tool_call,
    validate_tool_params,
)
from pi_ai.types import TextContent
from pi_ai import Model, ModelCost


# =============================================================================
# Tool Implementations
# =============================================================================

async def read_file_tool(
    tool_call_id: str,
    params: dict[str, Any],
    cancel_event,
    on_update,
) -> AgentToolResult:
    """Read contents of a file."""
    file_path = params.get("path")
    
    if not file_path:
        return AgentToolResult(
            content=[TextContent(type="text", text="Error: 'path' parameter is required")],
            details={"error": "missing_parameter"}
        )
    
    path = Path(file_path)
    
    try:
        if not path.exists():
            return AgentToolResult(
                content=[TextContent(type="text", text=f"Error: File not found: {file_path}")],
                details={"error": "file_not_found", "path": str(path)}
            )
        
        if not path.is_file():
            return AgentToolResult(
                content=[TextContent(type="text", text=f"Error: Not a file: {file_path}")],
                details={"error": "not_a_file", "path": str(path)}
            )
        
        content = path.read_text()
        lines = content.split('\n')
        
        # Return with line numbers for context
        numbered_lines = [f"{i+1:4d} | {line}" for i, line in enumerate(lines)]
        preview = '\n'.join(numbered_lines[:50])  # First 50 lines
        
        if len(lines) > 50:
            preview += f"\n... ({len(lines) - 50} more lines)"
        
        return AgentToolResult(
            content=[TextContent(type="text", text=f"File: {file_path}\n\n{preview}")],
            details={
                "path": str(path),
                "line_count": len(lines),
                "preview_lines": min(50, len(lines))
            }
        )
    
    except Exception as e:
        return AgentToolResult(
            content=[TextContent(type="text", text=f"Error reading file: {e}")],
            details={"error": str(e), "path": str(path)}
        )


async def write_file_tool(
    tool_call_id: str,
    params: dict[str, Any],
    cancel_event,
    on_update,
) -> AgentToolResult:
    """Write content to a file."""
    file_path = params.get("path")
    content = params.get("content")
    
    if not file_path or content is None:
        return AgentToolResult(
            content=[TextContent(type="text", text="Error: 'path' and 'content' parameters are required")],
            details={"error": "missing_parameters"}
        )
    
    path = Path(file_path)
    
    try:
        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content
        path.write_text(content)
        
        lines = content.count('\n') + 1
        chars = len(content)
        
        return AgentToolResult(
            content=[TextContent(type="text", text=f"Written {lines} lines ({chars} chars) to {file_path}")],
            details={
                "path": str(path),
                "line_count": lines,
                "char_count": chars,
                "status": "written"
            }
        )
    
    except Exception as e:
        return AgentToolResult(
            content=[TextContent(type="text", text=f"Error writing file: {e}")],
            details={"error": str(e), "path": str(path)}
        )


async def edit_file_tool(
    tool_call_id: str,
    params: dict[str, Any],
    cancel_event,
    on_update,
) -> AgentToolResult:
    """Edit a file by replacing exact string matches."""
    file_path = params.get("path")
    old_text = params.get("old_text")
    new_text = params.get("new_text")
    replace_all = params.get("replace_all", False)
    
    if not all([file_path, old_text, new_text]):
        return AgentToolResult(
            content=[TextContent(type="text", text="Error: 'path', 'old_text', and 'new_text' parameters are required")],
            details={"error": "missing_parameters"}
        )
    
    path = Path(file_path)
    
    try:
        content = path.read_text()
        
        if old_text not in content:
            return AgentToolResult(
                content=[TextContent(type="text", text=f"Error: Text not found in file: {old_text}")],
                details={"error": "text_not_found", "search": old_text}
            )
        
        if replace_all:
            new_content = content.replace(old_text, new_text)
            occurrences = content.count(old_text)
        else:
            new_content = content.replace(old_text, new_text, 1)
            occurrences = 1
        
        path.write_text(new_content)
        
        return AgentToolResult(
            content=[TextContent(type="text", text=f"Replaced {occurrences} occurrence(s) in {file_path}")],
            details={
                "path": str(path),
                "occurrences": occurrences,
                "replace_all": replace_all,
                "status": "replaced"
            }
        )
    
    except Exception as e:
        return AgentToolResult(
            content=[TextContent(type="text", text=f"Error editing file: {e}")],
            details={"error": str(e), "path": str(path)}
        )


async def list_directory_tool(
    tool_call_id: str,
    params: dict[str, Any],
    cancel_event,
    on_update,
) -> AgentToolResult:
    """List files and directories in a given path."""
    directory = params.get("path", ".")
    
    try:
        path = Path(directory)
        
        if not path.exists():
            return AgentToolResult(
                content=[TextContent(type="text", text=f"Error: Directory not found: {directory}")],
                details={"error": "directory_not_found", "path": str(path)}
            )
        
        if not path.is_dir():
            return AgentToolResult(
                content=[TextContent(type="text", text=f"Error: Not a directory: {directory}")],
                details={"error": "not_a_directory", "path": str(path)}
            )
        
        items = []
        for item in sorted(path.iterdir()):
            item_info = {
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None
            }
            items.append(item_info)
        
        # Format output
        lines = []
        lines.append(f"Contents of {directory}:")
        lines.append("-" * 50)
        
        for item in items:
            type_char = "D" if item["type"] == "directory" else "F"
            size_info = f" ({item['size']} bytes)" if item["size"] else ""
            lines.append(f"  [{type_char}] {item['name']}{size_info}")
        
        lines.append("-" * 50)
        lines.append(f"Total: {len(items)} items")
        
        return AgentToolResult(
            content=[TextContent(type="text", text="\n".join(lines))],
            details={
                "path": str(path),
                "items": items,
                "total": len(items)
            }
        )
    
    except Exception as e:
        return AgentToolResult(
            content=[TextContent(type="text", text=f"Error listing directory: {e}")],
            details={"error": str(e), "path": directory}
        )


async def run_command_tool(
    tool_call_id: str,
    params: dict[str, Any],
    cancel_event,
    on_update,
) -> AgentToolResult:
    """Run a shell command."""
    command = params.get("command")
    
    if not command:
        return AgentToolResult(
            content=[TextContent(type="text", text="Error: 'command' parameter is required")],
            details={"error": "missing_parameter"}
        )
    
    try:
        import subprocess
        
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout
        )
        
        output = result.stdout or ""
        error = result.stderr or ""
        
        lines = []
        lines.append(f"Command: {command}")
        lines.append(f"Exit code: {result.returncode}")
        
        if output:
            lines.append("\nSTDOUT:")
            lines.append(output)
        
        if error:
            lines.append("\nSTDERR:")
            lines.append(error)
        
        return AgentToolResult(
            content=[TextContent(type="text", text="\n".join(lines))],
            details={
                "command": command,
                "exit_code": result.returncode,
                "stdout": output,
                "stderr": error
            }
        )
    
    except subprocess.TimeoutExpired:
        return AgentToolResult(
            content=[TextContent(type="text", text=f"Error: Command timed out after 30 seconds: {command}")],
            details={"error": "timeout", "command": command}
        )
    except Exception as e:
        return AgentToolResult(
            content=[TextContent(type="text", text=f"Error running command: {e}")],
            details={"error": str(e), "command": command}
        )


# =============================================================================
# Tool Definitions
# =============================================================================

read_file = AgentTool(
    name="read_file",
    label="Read File",
    description="Read the contents of a file with line numbers",
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to read (relative or absolute)"
            }
        },
        "required": ["path"]
    },
    execute=read_file_tool
)

write_file = AgentTool(
    name="write_file",
    label="Write File",
    description="Write content to a file (creates parent directories if needed)",
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to write"
            },
            "content": {
                "type": "string",
                "description": "Content to write to the file"
            }
        },
        "required": ["path", "content"]
    },
    execute=write_file_tool
)

edit_file = AgentTool(
    name="edit_file",
    label="Edit File",
    description="Edit a file by replacing exact string matches (first or all occurrences)",
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to edit"
            },
            "old_text": {
                "type": "string",
                "description": "Text to search for and replace"
            },
            "new_text": {
                "type": "string",
                "description": "New text to replace with"
            },
            "replace_all": {
                "type": "boolean",
                "description": "Replace all occurrences (default: false, replaces only first)",
                "default": False
            }
        },
        "required": ["path", "old_text", "new_text"]
    },
    execute=edit_file_tool
)

list_directory = AgentTool(
    name="list_directory",
    label="List Directory",
    description="List files and directories in a given path",
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Directory path (default: current directory)",
                "default": "."
            }
        },
        "required": []
    },
    execute=list_directory_tool
)

run_command = AgentTool(
    name="run_command",
    label="Run Command",
    description="Execute a shell command with 30 second timeout",
    parameters={
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "Shell command to execute"
            }
        },
        "required": ["command"]
    },
    execute=run_command_tool
)


# =============================================================================
# Main Example
# =============================================================================

async def main():
    """Main function demonstrating the coding agent."""
    
    print("=" * 60)
    print("Coding Agent Example")
    print("=" * 60)
    print()
    print("This agent has developer tools for:")
    print("  📄 read_file  - Read file contents")
    print("  ✏️  write_file - Write content to files")
    print("  🔧 edit_file   - Search and replace in files")
    print("  📂 list_directory - List directory contents")
    print("  💻 run_command  - Execute shell commands")
    print()
    print("Try asking the agent to:")
    print("  - Read a file: 'Read the main.py file'")
    print("  - Edit a file: 'Replace TODO with DONE in todos.txt'")
    print("  - List files: 'What files are in the examples directory?'")
    print("  - Run tests: 'Run the test suite'")
    print()
    print("-" * 60)
    print()
    
    # Create agent with developer tools
    agent = Agent(options={
        "model": Model(
            id="test-model",
            name="Test Model",
            api="openai-completions",
            provider="openai",
            base_url="https://api.openai.com/v1",
            reasoning=False,
            input=["text"],
            cost=ModelCost(
                input=0.5,
                output=1.5,
                cache_read=0.0,
                cache_write=0.0
            ),
            context_window=128000,
            max_tokens=4096,
        ),
        "tools": [read_file, write_file, edit_file, list_directory, run_command],
    })
    
    # Set a helpful system prompt
    agent.set_system_prompt(
        """You are a helpful coding assistant with access to file system tools.

When helping with code:
1. Always use tools to read files before suggesting changes
2. Be precise with text replacements - use exact string matches
3. Show previews of file contents before editing
4. Explain what changes you're making and why
5. Use list_directory to understand project structure

When running commands:
1. Show the command you're about to run
2. Explain what the command does
3. Report the results clearly
4. Handle errors gracefully and suggest solutions

Available tools:
- read_file: Read file contents with line numbers
- write_file: Create or overwrite files
- edit_file: Search and replace text in files
- list_directory: List files and directories
- run_command: Execute shell commands (30s timeout)

Focus on being accurate, clear, and helpful with code-related tasks."""
    )
    
    # Subscribe to events for monitoring
    def on_event(event):
        if event.type == "text_delta":
            print(event.delta, end="", flush=True)
        elif event.type == "tool_call_start":
            print(f"\n[Tool: {event.tool_name}]")
        elif event.type == "tool_call_end":
            print(f"[Tool Complete]")
        elif event.type == "error":
            print(f"\n[Error: {event.error}]")
        elif event.type == "done":
            print()  # End on new line
    
    agent.subscribe(on_event)
    
    # Start the agent
    print("Agent ready! Type your coding questions below.")
    print("Press Ctrl+C to exit.")
    print()
    
    # Example prompts to try:
    examples = [
        "What files are in the current directory?",
        "Read the README.md file",
        "Create a new file called hello.py with a simple greeting",
        "List the contents of the examples directory",
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example}")
    
    print()
    print("-" * 60)
    print("You can start by pressing Enter, or type your own question:")
    print()
    
    # Start with a sample prompt
    try:
        await agent.prompt("What files are in the examples directory?")
    except KeyboardInterrupt:
        print("\nExiting coding agent...")
        await agent.abort()


if __name__ == "__main__":
    asyncio.run(main())
