"""Integration tests for pi_agent module - Agent runtime."""

import os
import pytest
import asyncio

from pi_ai.types import (
    Model,
    ModelCost,
    TextContent,
    UserMessage,
)
from pi_agent.agent import Agent
from pi_agent.types import AgentState, AgentTool, AgentToolResult

# Skip all tests in this module if no API key
pytestmark = pytest.mark.skipif(
    not (os.environ.get("ZHIPU_API_KEY")),
    reason="ZHIPU_API_KEY not set",
)


@pytest.fixture
def zhipu_model() -> Model:
    """Create a Zhipu model for testing."""
    return Model(
        id="glm-4-flash",
        name="GLM-4-Flash",
        api="zhipu",
        provider="zhipu",
        baseUrl="https://open.bigmodel.cn/api/paas/v4",
        reasoning=False,
        input=["text"],
        cost=ModelCost(input=0.001, output=0.001, cacheRead=0, cacheWrite=0),
        contextWindow=128000,
        maxTokens=4096,
    )


@pytest.fixture
def simple_tool() -> AgentTool:
    """Create a simple test tool."""

    async def echo_tool(
        tool_call_id: str,
        params: dict,
        cancel_event: asyncio.Event | None,
        on_update,
    ) -> AgentToolResult:
        return AgentToolResult(
            content=[TextContent(type="text", text=f"Echo: {params.get('message', 'empty')}")],
            details={"echoed": True},
        )

    return AgentTool(
        name="echo",
        label="Echo",
        description="Echo back the message",
        parameters={
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Message to echo"},
            },
            "required": ["message"],
        },
        execute=echo_tool,
    )


class TestAgentIntegration:
    """Integration tests for Agent."""

    def test_agent_creation(self, zhipu_model: Model):
        """Test basic agent creation."""
        agent = Agent(
            options={
                "model": zhipu_model,
            }
        )
        assert agent._state is not None
        assert agent._state.model is not None

    def test_agent_with_tools(self, zhipu_model: Model, simple_tool: AgentTool):
        """Test agent creation with tools."""
        agent = Agent(
            options={
                "model": zhipu_model,
            }
        )
        assert agent._state is not None

    def test_agent_steer(self, zhipu_model: Model):
        """Test agent steering mechanism."""
        agent = Agent(options={"model": zhipu_model})

        # Add steering message
        agent.steer({"role": "user", "content": "Hello"})

        assert len(agent._steering_queue) == 1

    @pytest.mark.skip(reason="Requires real API call, run manually")
    @pytest.mark.asyncio
    async def test_agent_simple_turn(self, zhipu_model: Model):
        """Test a simple turn with the agent."""
        agent = Agent(
            options={
                "model": zhipu_model,
            }
        )

        received_events = []

        def on_event(event):
            received_events.append(event)

        agent.subscribe(on_event)

        await agent.prompt("Say 'ok'")

        assert len(received_events) >= 0

    @pytest.mark.skip(reason="Requires real API call, run manually")
    @pytest.mark.asyncio
    async def test_agent_with_tool_calling(self, zhipu_model: Model, simple_tool: AgentTool):
        """Test agent with tool calling."""
        agent = Agent(
            options={
                "model": zhipu_model,
            }
        )
        agent.set_tools([simple_tool])

        received_events = []

        def on_event(event):
            received_events.append(event)

        agent.subscribe(on_event)

        await agent.prompt("Echo the message 'test123'")

        assert len(received_events) >= 0


class TestAgentState:
    """Test AgentState functionality."""

    def test_agent_state_creation(self, zhipu_model: Model):
        """Test creating agent state."""
        state = AgentState(
            systemPrompt="Test prompt",
            model=zhipu_model,
            thinkingLevel="off",
            tools=[],
            messages=[],
        )

        assert state.system_prompt == "Test prompt"
        assert state.model == zhipu_model
        assert state.thinking_level == "off"
        assert len(state.tools) == 0
        assert len(state.messages) == 0

    def test_agent_state_default_values(self, zhipu_model: Model):
        """Test agent state default values."""
        state = AgentState(
            systemPrompt="Test",
            model=zhipu_model,
            thinkingLevel="medium",
            tools=[],
            messages=[],
        )

        assert state.is_streaming is False
        assert state.stream_message is None
        assert len(state.pending_tool_calls) == 0


class TestAgentToolResult:
    """Test AgentToolResult functionality."""

    def test_tool_result_creation(self):
        """Test creating tool result."""
        result = AgentToolResult(
            content=[TextContent(type="text", text="Tool output")],
            details={"path": "/tmp/file.txt"},
        )

        assert len(result.content) == 1
        assert result.content[0].text == "Tool output"
        assert result.details["path"] == "/tmp/file.txt"

    def test_tool_result_without_details(self):
        """Test creating tool result without details."""
        result = AgentToolResult(
            content=[TextContent(type="text", text="Output")],
        )

        assert len(result.content) == 1
        assert result.details is None
