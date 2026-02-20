"""Integration tests configuration and fixtures."""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Generator

import pytest


def load_env_file() -> dict[str, str]:
    """Load environment variables from .env file."""
    env_vars = {}
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars


@pytest.fixture(scope="session")
def env_vars() -> dict[str, str]:
    """Load and return environment variables from .env file."""
    return load_env_file()


@pytest.fixture(scope="session")
def zhipu_api_key(env_vars: dict[str, str]) -> str | None:
    """Get Zhipu API key from environment."""
    return env_vars.get("ZHIPU_API_KEY") or os.environ.get("ZHIPU_API_KEY")


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files. Cleans up after test."""
    dir_path = Path(tempfile.mkdtemp(prefix="pi_integration_test_"))
    yield dir_path
    # Cleanup
    if dir_path.exists():
        shutil.rmtree(dir_path, ignore_errors=True)


@pytest.fixture
def temp_file(temp_dir: Path) -> Generator[Path, None, None]:
    """Create a temporary file for testing."""
    file_path = temp_dir / "test_file.txt"
    file_path.write_text("Hello, World!")
    yield file_path
    # Cleanup handled by temp_dir fixture


# Track all created temp directories for cleanup
_created_temp_dirs: list[Path] = []


def pytest_sessionstart(session):
    """Called at the start of the test session."""
    global _created_temp_dirs
    _created_temp_dirs = []


def pytest_sessionfinish(session, exitstatus):
    """Called at the end of the test session. Cleanup any remaining temp dirs."""
    global _created_temp_dirs
    for dir_path in _created_temp_dirs:
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path, ignore_errors=True)
            except Exception:
                pass
