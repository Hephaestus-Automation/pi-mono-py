"""
pi_coding - Coding Agent Package

A full-featured coding agent with file system tools, code editing,
and shell command execution.

This package provides:
- AgentTools for common coding operations
- Tool validation and error handling
- Event-driven architecture
- Integration with pi_agent runtime

Usage:
    from pi_coding import get_coding_tools, create_coding_agent
    
    # Get all coding tools
    tools = get_coding_tools()
    
    # Create a pre-configured coding agent
    agent = create_coding_agent(model=your_model)
    
    # Use the agent
    await agent.prompt("Read the main.py file")
"""

from __future__ import annotations

import asyncio
import os
import subprocess
from pathlib import Path
from typing import Any

from pi_agent import Agent, AgentTool, AgentToolResult
from pi_agent.types import AgentContext
from pi_ai.types import TextContent

__all__ = [
    "get_coding_tools",
    "create_coding_agent",
    "CodingAgentConfig",
]


# =============================================================================
# Tool Implementations
# =============================================================================

async def read_file(
    tool_call_id: str,
    params: dict[str, Any],
    cancel_event: asyncio.Event | None,
    on_update,
) -> AgentToolResult:
    """Read contents of a file with line numbers."""
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
        preview = '\n'.join(numbered_lines[:100])  # First 100 lines
        
        if len(lines) > 100:
            preview += f"\n... ({len(lines) - 100} more lines)"
        
        return AgentToolResult(
            content=[TextContent(type="text", text=f"File: {file_path}\n\n{preview}")],
            details={
                "path": str(path),
                "line_count": len(lines),
                "preview_lines": min(100, len(lines))
            }
        )
    
    except Exception as e:
        return AgentToolResult(
            content=[TextContent(type="text", text=f"Error reading file: {e}")],
            details={"error": str(e), "path": str(path)}
        )


async def write_file(
    tool_call_id: str,
    params: dict[str, Any],
    cancel_event: asyncio.Event | None,
    on_update,
) -> AgentToolResult:
    """Write content to a file (creates parent directories)."""
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
            content=[TextContent(type="text", text=f"✓ Written {lines} lines ({chars} chars) to {file_path}")],
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


async def edit_file(
    tool_call_id: str,
    params: dict[str, Any],
    cancel_event: asyncio.Event | None,
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
                content=[TextContent(type="text", text=f"Error: Text not found in file: '{old_text}'")],
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
            content=[TextContent(type="text", text=f"✓ Replaced {occurrences} occurrence(s) in {file_path}")],
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


async def list_directory(
    tool_call_id: str,
    params: dict[str, Any],
    cancel_event: asyncio.Event | None,
    on_update,
) -> AgentToolResult:
    """List files and directories with type and size info."""
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
            stat = item.stat()
            items.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size": stat.st_size if item.is_file() else None
            })
        
        # Format output
        lines = []
        lines.append(f"📁 {directory}")
        lines.append("-" * 60)
        
        for item in items:
            type_emoji = "📂" if item["type"] == "directory" else "📄"
            size_info = f" ({item['size']} bytes)" if item["size"] else ""
            lines.append(f"  {type_emoji} {item['name']}{size_info}")
        
        lines.append("-" * 60)
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


async def run_command(
    tool_call_id: str,
    params: dict[str, Any],
    cancel_event: asyncio.Event | None,
    on_update,
) -> AgentToolResult:
    """Run a shell command with timeout."""
    command = params.get("command")
    timeout = params.get("timeout", 30)
    
    if not command:
        return AgentToolResult(
            content=[TextContent(type="text", text="Error: 'command' parameter is required")],
            details={"error": "missing_parameter"}
        )
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        output = result.stdout or ""
        error = result.stderr or ""
        
        lines = []
        lines.append(f"💻 Command: {command}")
        lines.append(f"📤 Exit code: {result.returncode}")
        
        if output:
            lines.append("\n📤 STDOUT:")
            lines.append(output)
        
        if error:
            lines.append("\n⚠️  STDERR:")
            lines.append(error)
        
        if result.returncode == 0:
            lines.append("\n✅ Command executed successfully")
        else:
            lines.append("\n❌ Command failed")
        
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
            content=[TextContent(type="text", text=f"⏱️  Error: Command timed out after {timeout} seconds: {command}")],
            details={"error": "timeout", "command": command}
        )
    except Exception as e:
        return AgentToolResult(
            content=[TextContent(type="text", text=f"Error running command: {e}")],
            details={"error": str(e), "command": command}
        )


async def grep_search(
    tool_call_id: str,
    params: dict[str, Any],
    cancel_event: asyncio.Event | None,
    on_update,
) -> AgentToolResult:
    """Search for text in files using grep."""
    pattern = params.get("pattern")
    file_path = params.get("path", ".")
    case_sensitive = params.get("case_sensitive", False)
    
    if not pattern:
        return AgentToolResult(
            content=[TextContent(type="text", text="Error: 'pattern' parameter is required")],
            details={"error": "missing_parameter"}
        )
    
    try:
        cmd = ["grep"]
        if not case_sensitive:
            cmd.append("-i")
        cmd.extend(["-r", pattern, file_path])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            preview = '\n'.join(lines[:20])
            if len(lines) > 20:
                preview += f"\n... ({len(lines) - 20} more matches)"
            
            return AgentToolResult(
                content=[TextContent(type="text", text=f"Found {len(lines)} matches:\n\n{preview}")],
                details={
                    "pattern": pattern,
                    "matches": lines,
                    "total": len(lines)
                }
            )
        else:
            return AgentToolResult(
                content=[TextContent(type="text", text=f"No matches found for pattern: {pattern}")],
                details={"pattern": pattern, "total": 0}
            )
    
    except Exception as e:
        return AgentToolResult(
            content=[TextContent(type="text", text=f"Error running grep: {e}")],
            details={"error": str(e)}
        )


# =============================================================================
# Tool Definitions
# =============================================================================

read_file_tool = AgentTool(
    name="read_file",
    label="Read File",
    description="Read the contents of a file with line numbers (max 100 lines shown)",
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
    execute=read_file
)

write_file_tool = AgentTool(
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
    execute=write_file
)

edit_file_tool = AgentTool(
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
                "description": "Replace all occurrences (default: false)",
                "default": False
            }
        },
        "required": ["path", "old_text", "new_text"]
    },
    execute=edit_file
)

list_directory_tool = AgentTool(
    name="list_directory",
    label="List Directory",
    description="List files and directories with type and size information",
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
    execute=list_directory
)

run_command_tool = AgentTool(
    name="run_command",
    label="Run Command",
    description="Execute a shell command (default timeout: 30 seconds)",
    parameters={
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "Shell command to execute"
            },
            "timeout": {
                "type": "number",
                "description": "Command timeout in seconds (default: 30)",
                "default": 30
            }
        },
        "required": ["command"]
    },
    execute=run_command
)

grep_search_tool = AgentTool(
    name="grep_search",
    label="Grep Search",
    description="Search for text in files using grep (recursive search)",
    parameters={
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Search pattern (supports regex)"
            },
            "path": {
                "type": "string",
                "description": "Directory to search in (default: current directory)",
                "default": "."
            },
            "case_sensitive": {
                "type": "boolean",
                "description": "Case-sensitive search (default: false)",
                "default": False
            }
        },
        "required": ["pattern"]
    },
    execute=grep_search
)


# =============================================================================
# Public API
# =============================================================================

def get_coding_tools() -> list[AgentTool]:
    """
    Get all coding agent tools.
    
    Returns:
        List of AgentTool instances for common coding operations.
    """
    return [
        read_file_tool,
        write_file_tool,
        edit_file_tool,
        list_directory_tool,
        run_command_tool,
        grep_search_tool,
    ]


class CodingAgentConfig:
    """Configuration for creating a coding agent."""
    
    def __init__(
        self,
        model=None,
        system_prompt=None,
        working_dir=None,
        command_timeout=30,
    ):
        self.model = model
        self.system_prompt = system_prompt
        self.working_dir = working_dir
        self.command_timeout = command_timeout


def create_coding_agent(
    config: CodingAgentConfig | None = None,
    **kwargs
) -> Agent:
    """
    Create a pre-configured coding agent.
    
    Args:
        config: CodingAgentConfig instance or None
        **kwargs: Additional options passed to Agent
        
    Returns:
        Configured Agent instance with coding tools.
    """
    cfg = config or CodingAgentConfig()
    
    # Default system prompt for coding
    system_prompt = cfg.system_prompt or """You are an expert coding assistant with access to file system tools.

## Core Principles

1. **Read before writing**: Always read files before suggesting changes
2. **Be precise**: Use exact string matches when editing
3. **Show context**: Display file previews before editing
4. **Explain changes**: Clearly describe what you're changing and why
5. **Handle errors**: Gracefully report errors and suggest solutions

## Available Tools

### File Operations
- **read_file**: Read file contents (max 100 lines shown)
  - Use for: Reviewing code, understanding file structure
- **write_file**: Create or overwrite files (creates directories)
  - Use for: Creating new files, writing code snippets
- **edit_file**: Search and replace text in files
  - Use for: Fixing bugs, refactoring, quick changes
- **list_directory**: List files with type and size
  - Use for: Exploring project structure, finding files

### Search & Execute
- **grep_search**: Search text in files (recursive)
  - Use for: Finding patterns, searching for functions
- **run_command**: Execute shell commands (timeout: {cfg.command_timeout}s)
  - Use for: Running tests, building, installing packages

## Workflow

When asked to make code changes:
1. List directory to understand structure
2. Read relevant files
3. Explain what you're going to do
4. Make changes with edit_file or write_file
5. Verify changes by reading back

When asked to run commands:
1. Show the command you're about to run
2. Explain what it does
3. Report results clearly
4. Handle errors and suggest fixes

## Best Practices

- Use relative paths when possible
- Check if files exist before editing
- Be conservative with replacements (replace_all=false by default)
- List files before running commands on directories
- Provide clear, concise explanations"""
    
    # Set working directory
    if cfg.working_dir:
        os.chdir(cfg.working_dir)
    
    # Create agent with coding tools
    agent = Agent(options={
        "model": cfg.model,
        "tools": get_coding_tools(),
        **kwargs
    })
    
    # Set system prompt
    agent.set_system_prompt(system_prompt)
    
    return agent
