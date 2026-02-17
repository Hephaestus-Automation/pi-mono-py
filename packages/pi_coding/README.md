# pi-coding - Coding Agent Package

A full-featured coding agent with file system tools, code editing, and shell command execution for pi-mono-py.

## Overview

`pi-coding` provides a ready-to-use coding agent with common developer tools:

- **File Operations**: Read, write, edit, and list files
- **Search**: Grep-based text search in files
- **Execution**: Run shell commands with timeout
- **Integration**: Seamless integration with pi_agent runtime

## Installation

```bash
cd pi-mono-py
uv sync
```

## Quick Start

### Option 1: Use Pre-configured Agent

```python
import asyncio
from pi_coding import create_coding_agent
from pi_ai import Model, ModelCost

agent = create_coding_agent(
    model=Model(
        id="your-model",
        name="Your Model",
        api="openai-completions",
        provider="openai",
        base_url="https://api.openai.com/v1",
        reasoning=False,
        input=["text"],
        cost=ModelCost(input=0.5, output=1.5, cache_read=0.0, cache_write=0.0),
        context_window=128000,
        max_tokens=4096,
    )
)

await agent.prompt("Read the main.py file and tell me what it does")
```

### Option 2: Get Tools Only

```python
import asyncio
from pi_coding import get_coding_tools
from pi_agent import Agent

# Get all coding tools
tools = get_coding_tools()

# Create custom agent with tools
agent = Agent(options={
    "model": your_model,
    "tools": tools,
    "system_prompt": "You are a helpful coding assistant."
})
```

## Available Tools

### read_file

Read the contents of a file with line numbers.

```python
# Tool call
{
    "name": "read_file",
    "args": {
        "path": "main.py"
    }
}

# Parameters
- path: Path to the file (relative or absolute)

# Output
- First 100 lines with line numbers
- Total line count
- File path
```

### write_file

Write content to a file (creates parent directories if needed).

```python
# Tool call
{
    "name": "write_file",
    "args": {
        "path": "hello.py",
        "content": "print('Hello, World!')"
    }
}

# Parameters
- path: Path to the file to write
- content: Content to write

# Output
- Line count and character count
- Success confirmation
```

### edit_file

Edit a file by replacing exact string matches.

```python
# Tool call
{
    "name": "edit_file",
    "args": {
        "path": "config.py",
        "old_text": "DEBUG = True",
        "new_text": "DEBUG = False",
        "replace_all": true
    }
}

# Parameters
- path: Path to the file to edit
- old_text: Text to search for
- new_text: New text to replace with
- replace_all: Replace all occurrences (default: false)

# Output
- Number of occurrences replaced
- Success confirmation
```

### list_directory

List files and directories with type and size information.

```python
# Tool call
{
    "name": "list_directory",
    "args": {
        "path": "src"
    }
}

# Parameters
- path: Directory path (default: current directory)

# Output
- File/directory type
- Size (for files)
- Total item count
```

### run_command

Execute a shell command with timeout.

```python
# Tool call
{
    "name": "run_command",
    "args": {
        "command": "pytest tests/",
        "timeout": 60
    }
}

# Parameters
- command: Shell command to execute
- timeout: Timeout in seconds (default: 30)

# Output
- Exit code
- stdout
- stderr
```

### grep_search

Search for text in files using grep (recursive search).

```python
# Tool call
{
    "name": "grep_search",
    "args": {
        "pattern": "def main",
        "path": "src",
        "case_sensitive": false
    }
}

# Parameters
- pattern: Search pattern (supports regex)
- path: Directory to search (default: current directory)
- case_sensitive: Case-sensitive search (default: false)

# Output
- Matched lines
- Total match count
```

## Examples

### Example 1: Read and Edit File

```python
import asyncio
from pi_coding import create_coding_agent

agent = create_coding_agent()

# Read a file
await agent.prompt("Read the README.md file")

# Edit it
await agent.prompt("Replace 'TODO' with 'DONE' in README.md")
```

### Example 2: Create New File

```python
import asyncio
from pi_coding import create_coding_agent

agent = create_coding_agent()

await agent.prompt("""
Create a new file called hello.py with this content:

def greet(name):
    return f'Hello, {name}!'

if __name__ == '__main__':
    print(greet('World'))
""")
```

### Example 3: Explore Project

```python
import asyncio
from pi_coding import create_coding_agent

agent = create_coding_agent()

await agent.prompt("List the files in the src directory")

await agent.prompt("What Python files are in the examples directory?")
```

### Example 4: Run Tests

```python
import asyncio
from pi_coding import create_coding_agent

agent = create_coding_agent()

await agent.prompt("Run pytest on the tests directory")

await agent.prompt("Run the test suite and show me the results")
```

### Example 5: Search and Fix

```python
import asyncio
from pi_coding import create_coding_agent

agent = create_coding_agent()

# Search for TODOs
await agent.prompt("Search for 'TODO' in all Python files")

# Fix them
await agent.prompt("Replace all TODO comments with DONE")
```

## Advanced Usage

### Custom System Prompt

```python
from pi_coding import CodingAgentConfig

config = CodingAgentConfig(
    system_prompt="""You are a security-focused code reviewer.
Always check for:
- SQL injection vulnerabilities
- Missing input validation
- Hardcoded credentials
- Insecure dependencies"""
)

agent = create_coding_agent(config=config)
```

### Custom Working Directory

```python
from pi_coding import CodingAgentConfig

config = CodingAgentConfig(
    working_dir="/path/to/project",
    command_timeout=60
)

agent = create_coding_agent(config=config)
```

### Custom Model

```python
from pi_coding import CodingAgentConfig
from pi_ai import Model, ModelCost

config = CodingAgentConfig(
    model=Model(
        id="claude-3.5-sonnet",
        name="Claude 3.5 Sonnet",
        api="anthropic-messages",
        provider="anthropic",
        base_url="https://api.anthropic.com",
        reasoning=True,
        input=["text", "image"],
        cost=ModelCost(
            input=3.0,
            output=15.0,
            cache_read=0.3,
            cache_write=0.3
        ),
        context_window=200000,
        max_tokens=8192,
    )
)

agent = create_coding_agent(config=config)
```

## Tool Design Philosophy

All tools follow these principles:

1. **Parameter Validation**: JSON Schema with required fields
2. **Error Handling**: Try-catch with meaningful error messages
3. **Rich Output**: Detailed results with context and metadata
4. **Safety**: Timeouts, path validation, permission checks
5. **User-Friendly**: Clear success/failure indicators with emojis

## API Reference

### `get_coding_tools() -> list[AgentTool]`

Get all coding agent tools.

**Returns:**
- List of 6 AgentTool instances

**Example:**
```python
from pi_coding import get_coding_tools

tools = get_coding_tools()
for tool in tools:
    print(f"{tool.name}: {tool.description}")
```

### `create_coding_agent(config=None, **kwargs) -> Agent`

Create a pre-configured coding agent.

**Parameters:**
- config: CodingAgentConfig instance (optional)
- **kwargs: Additional options passed to Agent

**Returns:**
- Configured Agent instance

**Example:**
```python
from pi_coding import CodingAgentConfig, create_coding_agent

config = CodingAgentConfig(
    system_prompt="You are a Python expert.",
    command_timeout=60
)

agent = create_coding_agent(config=config)
```

### `CodingAgentConfig`

Configuration class for coding agent.

**Attributes:**
- model: Model instance (optional)
- system_prompt: System prompt string (optional)
- working_dir: Working directory path (optional)
- command_timeout: Command timeout in seconds (default: 30)

## Testing

```bash
# Run tests
cd packages/pi_coding
uv run pytest

# Run with coverage
uv run pytest --cov=pi_coding --cov-report=html
```

## Troubleshooting

### Permission Denied Errors

If you get permission errors:
```bash
# Check file permissions
ls -la <file>

# Run with appropriate permissions
sudo python your_script.py
```

### Command Not Found

If commands fail:
```bash
# Check if command is installed
which <command>

# Install if needed
apt install <package>  # Debian/Ubuntu
# or
brew install <package>  # macOS
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Related Packages

- [pi-agent](../pi_agent/README.md) - Agent runtime
- [pi-ai](../pi_ai/README.md) - Multi-provider LLM API
- [pi-tui](../pi_tui/README.md) - Terminal UI library
