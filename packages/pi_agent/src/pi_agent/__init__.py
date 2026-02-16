from __future__ import annotations

# Re-export stream_proxy from pi_ai for convenience
from pi_ai.stream_proxy import ProxyConfig, stream_proxy

from pi_agent.agent import Agent
from pi_agent.loop import agent_loop, agent_loop_continue
from pi_agent.tools import (
    ToolValidationError,
    create_bash_tool,
    create_edit_file_tool,
    create_grep_tool,
    create_read_file_tool,
    create_tool,
    create_write_file_tool,
    get_builtin_tools,
    validate_tool_call,
    validate_tool_params,
)
from pi_agent.types import (
    AgentContext,
    AgentEvent,
    AgentLoopConfig,
    AgentMessage,
    AgentState,
    AgentTool,
    AgentToolResult,
    StreamFn,
    ThinkingLevel,
)

__all__ = [
    "Agent",
    "AgentContext",
    "AgentEvent",
    "AgentLoopConfig",
    "AgentMessage",
    "AgentState",
    "AgentTool",
    "AgentToolResult",
    "StreamFn",
    "ThinkingLevel",
    "agent_loop",
    "agent_loop_continue",
    "create_tool",
    "create_read_file_tool",
    "create_write_file_tool",
    "create_edit_file_tool",
    "create_bash_tool",
    "create_grep_tool",
    "get_builtin_tools",
    "validate_tool_params",
    "validate_tool_call",
    "ToolValidationError",
    "stream_proxy",
    "ProxyConfig",
]
