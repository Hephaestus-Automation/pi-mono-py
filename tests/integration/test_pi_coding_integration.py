"""Integration tests for pi_coding module - Coding tools end-to-end."""

import os
import asyncio
import tempfile
from pathlib import Path

import pytest

from pi_coding import (
    create_read_tool,
    create_write_tool,
    create_edit_tool,
    create_bash_tool,
    create_ls_tool,
)
from pi_coding.utils import (
    parse_git_url,
    get_current_branch,
    get_repo_status,
    get_shell_config,
    sanitize_binary_output,
    GitSource,
)
from pi_coding.config import (
    get_agent_dir,
    get_sessions_dir,
    VERSION,
)


class TestCodingToolsIntegration:
    """Integration tests for coding tools."""

    @pytest.fixture
    def temp_workspace(self, tmp_path: Path) -> Path:
        """Create a temporary workspace for testing."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        return workspace

    @pytest.mark.asyncio
    async def test_write_and_read_tool(self, temp_workspace: Path):
        """Test write tool followed by read tool."""
        write_tool = create_write_tool(str(temp_workspace))
        read_tool = create_read_tool(str(temp_workspace))

        # Write a file
        write_result = await write_tool.execute(
            "test-call-1",
            {"path": "test.txt", "content": "Hello, Integration Test!"},
            None,
            None,
        )
        assert "Success" in write_result.content[0].text or "wrote" in write_result.content[0].text.lower()

        # Read it back
        read_result = await read_tool.execute(
            "test-call-2",
            {"path": "test.txt"},
            None,
            None,
        )
        assert "Hello, Integration Test!" in read_result.content[0].text

    @pytest.mark.asyncio
    async def test_edit_tool(self, temp_workspace: Path):
        """Test edit tool."""
        write_tool = create_write_tool(str(temp_workspace))
        edit_tool = create_edit_tool(str(temp_workspace))
        read_tool = create_read_tool(str(temp_workspace))

        # Write initial file
        await write_tool.execute(
            "test-call-1",
            {"path": "edit_test.txt", "content": "Hello World"},
            None,
            None,
        )

        # Edit the file
        edit_result = await edit_tool.execute(
            "test-call-2",
            {
                "path": "edit_test.txt",
                "old_text": "World",
                "new_text": "Integration",
            },
            None,
            None,
        )
        assert "Success" in edit_result.content[0].text or "replaced" in edit_result.content[0].text.lower()

        # Verify edit
        read_result = await read_tool.execute(
            "test-call-3",
            {"path": "edit_test.txt"},
            None,
            None,
        )
        assert "Hello Integration" in read_result.content[0].text

    @pytest.mark.asyncio
    async def test_bash_tool_echo(self, temp_workspace: Path):
        """Test bash tool with simple echo command."""
        bash_tool = create_bash_tool(str(temp_workspace))

        result = await bash_tool.execute(
            "test-call-1",
            {"command": "echo 'Hello from bash'"},
            None,
            None,
        )
        assert "Hello from bash" in result.content[0].text

    @pytest.mark.asyncio
    async def test_bash_tool_creates_file(self, temp_workspace: Path):
        """Test bash tool creating a file."""
        bash_tool = create_bash_tool(str(temp_workspace))
        read_tool = create_read_tool(str(temp_workspace))

        # Create file via bash
        await bash_tool.execute(
            "test-call-1",
            {"command": "echo 'Created by bash' > bash_created.txt"},
            None,
            None,
        )

        # Verify file exists
        result = await read_tool.execute(
            "test-call-2",
            {"path": "bash_created.txt"},
            None,
            None,
        )
        assert "Created by bash" in result.content[0].text

    @pytest.mark.asyncio
    async def test_ls_tool(self, temp_workspace: Path):
        """Test ls tool."""
        write_tool = create_write_tool(str(temp_workspace))
        ls_tool = create_ls_tool(str(temp_workspace))

        # Create some files
        await write_tool.execute(
            "test-call-1",
            {"path": "file1.txt", "content": "content1"},
            None,
            None,
        )
        await write_tool.execute(
            "test-call-2",
            {"path": "file2.txt", "content": "content2"},
            None,
            None,
        )

        # List directory
        result = await ls_tool.execute("test-call-3", {}, None, None)
        assert "file1.txt" in result.content[0].text
        assert "file2.txt" in result.content[0].text

    @pytest.mark.asyncio
    async def test_tool_chain_write_read_edit(self, temp_workspace: Path):
        """Test a chain of tool operations."""
        write_tool = create_write_tool(str(temp_workspace))
        read_tool = create_read_tool(str(temp_workspace))
        edit_tool = create_edit_tool(str(temp_workspace))

        # Step 1: Write
        await write_tool.execute(
            "step1",
            {"path": "chain.txt", "content": "Line 1\nLine 2\nLine 3"},
            None,
            None,
        )

        # Step 2: Read
        read_result = await read_tool.execute("step2", {"path": "chain.txt"}, None, None)
        assert "Line 1" in read_result.content[0].text

        # Step 3: Edit
        await edit_tool.execute(
            "step3",
            {"path": "chain.txt", "old_text": "Line 2", "new_text": "Modified Line 2"},
            None,
            None,
        )

        # Step 4: Verify
        final_result = await read_tool.execute("step4", {"path": "chain.txt"}, None, None)
        assert "Modified Line 2" in final_result.content[0].text
        assert "Line 1" in final_result.content[0].text
        assert "Line 3" in final_result.content[0].text


class TestGitUtilitiesIntegration:
    """Integration tests for git utilities."""

    def test_parse_git_url_github(self):
        """Test parsing GitHub URLs."""
        result = parse_git_url("https://github.com/user/repo")
        assert result is not None
        assert result.host == "github.com"
        assert result.path == "user/repo"
        assert result.type == "git"

    def test_parse_git_url_with_ref(self):
        """Test parsing git URL with ref."""
        result = parse_git_url("https://github.com/user/repo@v1.0.0")
        assert result is not None
        assert result.ref == "v1.0.0"
        assert result.pinned is True

    def test_parse_git_url_ssh(self):
        """Test parsing SSH git URL."""
        result = parse_git_url("git@github.com:user/repo")
        assert result is not None
        assert result.host == "github.com"
        assert result.path == "user/repo"

    def test_get_current_branch(self):
        """Test getting current git branch."""
        # This should work in any git repo
        branch = get_current_branch()
        # May be None if not in a git repo
        assert branch is None or isinstance(branch, str)

    def test_get_repo_status(self):
        """Test getting repo status."""
        status = get_repo_status()
        assert isinstance(status, dict)
        assert "has_unstaged_changes" in status
        assert "has_staged_changes" in status
        assert "has_untracked_files" in status
        assert "is_clean" in status


class TestShellUtilitiesIntegration:
    """Integration tests for shell utilities."""

    def test_get_shell_config(self):
        """Test getting shell config."""
        shell, args = get_shell_config()
        assert isinstance(shell, str)
        assert isinstance(args, list)
        assert len(shell) > 0
        assert "-c" in args

    def test_sanitize_binary_output(self):
        """Test sanitizing binary output."""
        # Test with control characters
        dirty = "Hello\x00\x01\x02World"
        clean = sanitize_binary_output(dirty)
        assert "\x00" not in clean
        assert "\x01" not in clean
        assert "Hello" in clean
        assert "World" in clean

    def test_sanitize_preserves_newlines(self):
        """Test that sanitization preserves newlines and tabs."""
        text = "Line1\nLine2\tTabbed\rReturn"
        clean = sanitize_binary_output(text)
        assert "\n" in clean
        assert "\t" in clean
        assert "\r" in clean


class TestConfigIntegration:
    """Integration tests for config module."""

    def test_get_agent_dir(self):
        """Test getting agent directory."""
        agent_dir = get_agent_dir()
        assert isinstance(agent_dir, Path)
        assert ".pi" in str(agent_dir)

    def test_get_sessions_dir(self):
        """Test getting sessions directory."""
        sessions_dir = get_sessions_dir()
        assert isinstance(sessions_dir, Path)
        assert "sessions" in str(sessions_dir)

    def test_version_exists(self):
        """Test that VERSION is defined."""
        assert VERSION is not None
        assert isinstance(VERSION, str)
        assert len(VERSION) > 0


class TestGitSourceDataclass:
    """Test GitSource dataclass."""

    def test_git_source_creation(self):
        """Test creating GitSource."""
        source = GitSource(
            type="git",
            repo="https://github.com/user/repo",
            host="github.com",
            path="user/repo",
            ref="main",
            pinned=True,
        )
        assert source.type == "git"
        assert source.repo == "https://github.com/user/repo"
        assert source.host == "github.com"
        assert source.path == "user/repo"
        assert source.ref == "main"
        assert source.pinned is True
