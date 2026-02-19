import os
import platform
from pathlib import Path
from pi_coding.utils.shell import (
    get_shell_config,
    get_shell_env,
    sanitize_binary_output,
    kill_process_tree,
)
from pi_coding.config import get_bin_dir

def test_get_shell_config_returns_tuple():
    config = get_shell_config()
    assert isinstance(config, tuple)
    assert len(config) == 2
    assert isinstance(config[0], str)
    assert isinstance(config[1], list)
    assert config[1] == ["-c"]

def test_get_shell_env_includes_bin_dir():
    env = get_shell_env()
    bin_dir = str(get_bin_dir())
    
    path_key = "PATH"
    for key in env:
        if key.upper() == "PATH":
            path_key = key
            break
            
    assert bin_dir in env[path_key]

def test_sanitize_binary_output_removes_control_chars():
    # \x00 is null, \x1f is unit separator
    input_text = "hello\x00world\x1f!"
    expected = "helloworld!"
    assert sanitize_binary_output(input_text) == expected

def test_sanitize_binary_output_preserves_newlines_tabs():
    input_text = "line1\nline2\ttab\rreturn"
    assert sanitize_binary_output(input_text) == input_text

def test_sanitize_binary_output_removes_unicode_format_chars():
    # \ufff9, \ufffa, \ufffb are unicode format characters
    input_text = "text\ufff9format\ufffa!"
    expected = "textformat!"
    assert sanitize_binary_output(input_text) == expected

def test_kill_process_tree_nonexistent_pid():
    # Should not raise any exception
    kill_process_tree(999999)
