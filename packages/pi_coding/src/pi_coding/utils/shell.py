import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pi_coding.config import get_bin_dir

_cached_shell_config: Optional[Tuple[str, List[str]]] = None


def find_bash_on_path() -> Optional[str]:
    """Find bash executable on PATH (cross-platform)."""
    return shutil.which("bash")


def get_shell_config() -> Tuple[str, List[str]]:
    """
    Get shell configuration based on platform.
    Resolution order:
    1. On Windows: Git Bash in known locations, then bash on PATH
    2. On Unix: /bin/bash, then bash on PATH, then fallback to sh
    """
    global _cached_shell_config
    if _cached_shell_config:
        return _cached_shell_config

    # Note: SettingsManager port is not requested yet, so we skip custom shellPath for now
    # as per the instructions to port shell.ts but with specific Python differences.

    if platform.system() == "Windows":
        # Try Git Bash in known locations
        paths = []
        program_files = os.environ.get("ProgramFiles")
        if program_files:
            paths.append(Path(program_files) / "Git" / "bin" / "bash.exe")
        
        program_files_x86 = os.environ.get("ProgramFiles(x86)")
        if program_files_x86:
            paths.append(Path(program_files_x86) / "Git" / "bin" / "bash.exe")

        for path in paths:
            if path.exists():
                _cached_shell_config = (str(path), ["-c"])
                return _cached_shell_config

        # Fallback: search bash.exe on PATH
        bash_on_path = find_bash_on_path()
        if bash_on_path:
            _cached_shell_config = (bash_on_path, ["-c"])
            return _cached_shell_config

        raise RuntimeError(
            "No bash shell found. Please install Git for Windows or add bash to your PATH."
        )

    # Unix: try /bin/bash, then bash on PATH, then fallback to sh
    if Path("/bin/bash").exists():
        _cached_shell_config = ("/bin/bash", ["-c"])
        return _cached_shell_config

    bash_on_path = find_bash_on_path()
    if bash_on_path:
        _cached_shell_config = (bash_on_path, ["-c"])
        return _cached_shell_config

    _cached_shell_config = ("sh", ["-c"])
    return _cached_shell_config


def get_shell_env() -> Dict[str, str]:
    """Get environment with bin_dir added to PATH."""
    bin_dir = str(get_bin_dir())
    env = os.environ.copy()
    
    # Find PATH key case-insensitively (Windows uses Path, Unix uses PATH)
    path_key = "PATH"
    for key in env:
        if key.upper() == "PATH":
            path_key = key
            break
            
    current_path = env.get(path_key, "")
    path_entries = [p for p in current_path.split(os.pathsep) if p]
    
    if bin_dir not in path_entries:
        updated_path = os.pathsep.join([bin_dir] + path_entries)
        env[path_key] = updated_path
        
    return env


def sanitize_binary_output(text: str) -> str:
    """
    Sanitize binary output for display/storage.
    Removes characters that cause display issues:
    - Control characters (except tab, newline, carriage return)
    - Unicode Format characters
    """
    result = []
    for char in text:
        code = ord(char)
        
        # Allow tab (0x09), newline (0x0a), carriage return (0x0d)
        if code in (0x09, 0x0a, 0x0d):
            result.append(char)
            continue
            
        # Filter out control characters (0x00-0x1F)
        if code <= 0x1f:
            continue
            
        # Filter out Unicode format characters (0xFFF9-0xFFFB)
        if 0xfff9 <= code <= 0xfffb:
            continue
            
        result.append(char)
        
    return "".join(result)


def kill_process_tree(pid: int) -> None:
    """Kill a process and all its children (cross-platform)."""
    if platform.system() == "Windows":
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                capture_output=True,
                check=False
            )
        except Exception:
            pass
    else:
        try:
            # Kill process group
            os.killpg(os.getpgid(pid), 9)
        except Exception:
            try:
                # Fallback to killing just the process
                os.kill(pid, 9)
            except Exception:
                pass
