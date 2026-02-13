import pytest
import asyncio

from pi_agent.tools import (
    validate_tool_params,
    validate_tool_call,
    create_tool,
    create_read_file_tool,
    create_write_file_tool,
    create_bash_tool,
    create_grep_tool,
    get_builtin_tools,
    ToolValidationError,
    READ_FILE_SCHEMA,
    WRITE_FILE_SCHEMA,
)
from pi_agent.types import AgentTool, AgentToolResult
from pi_ai.types import TextContent


class TestValidateToolParams:
    def test_validate_valid_params(self):
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        params = {"name": "test"}
        
        errors = validate_tool_params(schema, params)
        assert errors == []

    def test_validate_missing_required(self):
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        params = {}
        
        errors = validate_tool_params(schema, params)
        assert len(errors) > 0

    def test_validate_wrong_type(self):
        schema = {
            "type": "object",
            "properties": {"count": {"type": "number"}},
            "required": ["count"],
        }
        params = {"count": "not a number"}
        
        errors = validate_tool_params(schema, params)
        assert len(errors) > 0


class TestCreateTool:
    @pytest.mark.asyncio
    async def test_create_tool_with_validation(self):
        async def execute_fn(tool_call_id, args, cancel_event, on_update):
            return AgentToolResult(
                content=[TextContent(type="text", text=f"Executed with {args}")],
                details={},
            )
        
        tool = create_tool(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object", "properties": {"input": {"type": "string"}}},
            execute_fn=execute_fn,
        )
        
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"

    @pytest.mark.asyncio
    async def test_tool_validates_params(self):
        async def execute_fn(tool_call_id, args, cancel_event, on_update):
            return AgentToolResult(
                content=[TextContent(type="text", text="Success")],
                details={},
            )
        
        schema = {
            "type": "object",
            "properties": {"required_field": {"type": "string"}},
            "required": ["required_field"],
        }
        
        tool = create_tool(
            name="validated_tool",
            description="Tool with validation",
            parameters=schema,
            execute_fn=execute_fn,
        )
        
        result = await tool.execute("call-1", {"required_field": "value"}, None, None)
        assert "Success" in result.content[0].text


class TestBuiltinTools:
    def test_get_builtin_tools(self):
        tools = get_builtin_tools()
        
        assert len(tools) == 4
        names = [t.name for t in tools]
        assert "read_file" in names
        assert "write_file" in names
        assert "bash" in names
        assert "grep" in names

    def test_create_read_file_tool(self):
        tool = create_read_file_tool()
        
        assert tool.name == "read_file"
        assert "file_path" in tool.parameters.get("properties", {})

    def test_create_write_file_tool(self):
        tool = create_write_file_tool()
        
        assert tool.name == "write_file"
        assert "file_path" in tool.parameters.get("properties", {})
        assert "content" in tool.parameters.get("properties", {})

    def test_create_bash_tool(self):
        tool = create_bash_tool()
        
        assert tool.name == "bash"
        assert "command" in tool.parameters.get("properties", {})

    def test_create_grep_tool(self):
        tool = create_grep_tool()
        
        assert tool.name == "grep"
        assert "pattern" in tool.parameters.get("properties", {})


class TestToolExecution:
    @pytest.mark.asyncio
    async def test_bash_tool_echo(self):
        tool = create_bash_tool()
        
        result = await tool.execute(
            "call-1",
            {"command": "echo 'Hello World'"},
            None,
            None,
        )
        
        assert "Hello World" in result.content[0].text

    @pytest.mark.asyncio
    async def test_read_file_not_found(self):
        tool = create_read_file_tool()
        
        result = await tool.execute(
            "call-1",
            {"file_path": "/nonexistent/path/file.txt"},
            None,
            None,
        )
        
        assert "not found" in result.content[0].text.lower() or "error" in result.content[0].text.lower()
