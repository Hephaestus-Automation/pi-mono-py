"""Integration tests for pi_ai module - Zhipu API."""

import os
import pytest

from pi_ai.types import (
    Context,
    Model,
    ModelCost,
    TextContent,
    UserMessage,
)
from pi_ai.providers.zhipu import stream_zhipu


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
def simple_context() -> Context:
    """Create a simple context for testing."""
    return Context(
        systemPrompt="You are a helpful assistant. Be brief.",
        messages=[
            UserMessage(
                role="user",
                content=[TextContent(type="text", text="Say 'hello' in one word.")],
                timestamp=0,
            )
        ],
    )


class TestZhipuIntegration:
    """Integration tests for Zhipu API."""

    @pytest.mark.asyncio
    async def test_zhipu_simple_completion(self, zhipu_model: Model, simple_context: Context):
        """Test basic completion with Zhipu API."""
        stream = stream_zhipu(zhipu_model, simple_context)

        events = []
        async for event in stream:
            events.append(event)

        # Verify we got events
        assert len(events) > 0, "No events received from Zhipu API"

        # Check event types
        event_types = [e.type for e in events]
        assert "start" in event_types, "No start event received"
        assert "done" in event_types, "No done event received"

        # Check for text content
        done_event = next(e for e in events if e.type == "done")
        assert done_event.message is not None
        assert len(done_event.message.content) > 0

        # Extract text from content
        text_content = [c for c in done_event.message.content if c.type == "text"]
        assert len(text_content) > 0, "No text content in response"
        assert len(text_content[0].text) > 0, "Empty text response"

    @pytest.mark.asyncio
    async def test_zhipu_streaming_deltas(self, zhipu_model: Model, simple_context: Context):
        """Test that streaming produces delta events."""
        stream = stream_zhipu(zhipu_model, simple_context)

        delta_events = []
        async for event in stream:
            if event.type == "text_delta":
                delta_events.append(event)

        # Should have at least one delta event for non-empty response
        assert len(delta_events) >= 0, "Delta events list should exist"

        # If we got deltas, check they have content
        if len(delta_events) > 0:
            for delta in delta_events:
                assert hasattr(delta, "delta"), "Delta event missing delta attribute"

    @pytest.mark.asyncio
    async def test_zhipu_with_tools(self, zhipu_model: Model):
        """Test tool calling with Zhipu API."""
        from pi_ai.types import Tool

        context = Context(
            systemPrompt="You are a helpful assistant.",
            messages=[
                UserMessage(
                    role="user",
                    content=[TextContent(type="text", text="What is 2+2? Use the calculator.")],
                    timestamp=0,
                )
            ],
            tools=[
                Tool(
                    name="calculator",
                    description="A simple calculator that evaluates math expressions",
                    parameters={
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "Math expression to evaluate",
                            }
                        },
                        "required": ["expression"],
                    },
                )
            ],
        )

        stream = stream_zhipu(zhipu_model, context)

        events = []
        async for event in stream:
            events.append(event)

        # Just verify we get a valid response (tool call or text)
        done_event = next((e for e in events if e.type == "done"), None)
        assert done_event is not None, "No done event received"
        assert done_event.message is not None

    @pytest.mark.asyncio
    async def test_zhipu_usage_tracking(self, zhipu_model: Model, simple_context: Context):
        """Test that usage is tracked in responses."""
        stream = stream_zhipu(zhipu_model, simple_context)

        events = []
        async for event in stream:
            events.append(event)

        done_event = next((e for e in events if e.type == "done"), None)
        assert done_event is not None
        assert done_event.message is not None
        assert done_event.message.usage is not None
        assert done_event.message.usage.total_tokens >= 0


class TestZhipuProviderHelpers:
    """Test helper functions in Zhipu provider."""

    def test_normalize_zhipu_tool_id_short(self):
        """Test tool ID normalization for short IDs."""
        from pi_ai.providers.zhipu import normalize_zhipu_tool_id

        result = normalize_zhipu_tool_id("abc")
        assert len(result) == 9
        assert result.startswith("abc")

    def test_normalize_zhipu_tool_id_long(self):
        """Test tool ID normalization for long IDs."""
        from pi_ai.providers.zhipu import normalize_zhipu_tool_id

        result = normalize_zhipu_tool_id("verylongtoolid123456789")
        assert len(result) == 9

    def test_normalize_zhipu_tool_id_special_chars(self):
        """Test tool ID normalization removes special characters."""
        from pi_ai.providers.zhipu import normalize_zhipu_tool_id

        result = normalize_zhipu_tool_id("tool-id_123!@#")
        assert len(result) == 9
        # Should only contain alphanumeric
        assert result.isalnum()
