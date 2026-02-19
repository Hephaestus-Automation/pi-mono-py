from dataclasses import dataclass
import subprocess
import re
from urllib.parse import urlparse
from typing import Optional

@dataclass
class GitSource:
    """Parsed git URL information."""
    repo: str
    host: str
    path: str
    type: str = "git"
    ref: Optional[str] = None
    pinned: bool = False

def split_ref(url: str) -> dict:
    """Split a git URL into repo and ref parts."""
    # Handle SCP-like URLs: git@github.com:user/repo@ref
    scp_match = re.match(r"^git@([^:]+):(.+)$", url)
    if scp_match:
        host = scp_match.group(1)
        path_with_maybe_ref = scp_match.group(2)
        if "@" in path_with_maybe_ref:
            repo_path, ref = path_with_maybe_ref.split("@", 1)
            if repo_path and ref:
                return {
                    "repo": f"git@{host}:{repo_path}",
                    "ref": ref
                }
        return {"repo": url}

    # Handle URLs with protocols: https://github.com/user/repo@ref
    if "://" in url:
        try:
            parsed = urlparse(url)
            path_with_maybe_ref = parsed.path.lstrip("/")
            if "@" in path_with_maybe_ref:
                repo_path, ref = path_with_maybe_ref.split("@", 1)
                if repo_path and ref:
                    # Reconstruct URL without ref
                    new_path = f"/{repo_path}"
                    new_url = parsed._replace(path=new_path).geturl()
                    return {
                        "repo": new_url.rstrip("/"),
                        "ref": ref
                    }
            return {"repo": url}
        except Exception:
            return {"repo": url}

    # Handle shorthand: github.com/user/repo@ref
    if "/" in url:
        host, path_with_maybe_ref = url.split("/", 1)
        if "@" in path_with_maybe_ref:
            repo_path, ref = path_with_maybe_ref.split("@", 1)
            if repo_path and ref:
                return {
                    "repo": f"{host}/{repo_path}",
                    "ref": ref
                }
    
    return {"repo": url}

def parse_generic_git_url(url: str) -> Optional[GitSource]:
    """Parse a git URL that doesn't match hosted patterns."""
    split = split_ref(url)
    repo_without_ref = split["repo"]
    ref = split.get("ref")
    
    repo = repo_without_ref
    host = ""
    path = ""

    scp_match = re.match(r"^git@([^:]+):(.+)$", repo_without_ref)
    if scp_match:
        host = scp_match.group(1)
        path = scp_match.group(2)
    elif any(repo_without_ref.startswith(p) for p in ["https://", "http://", "ssh://", "git://"]):
        try:
            parsed = urlparse(repo_without_ref)
            host = parsed.hostname or ""
            path = parsed.path.lstrip("/")
        except Exception:
            return None
    else:
        if "/" not in repo_without_ref:
            return None
        host, path = repo_without_ref.split("/", 1)
        if "." not in host and host != "localhost":
            return None
        repo = f"https://{repo_without_ref}"

    normalized_path = path.replace(".git", "").lstrip("/")
    if not host or not normalized_path or len(normalized_path.split("/")) < 2:
        return None

    return GitSource(
        repo=repo,
        host=host,
        path=normalized_path,
        ref=ref,
        pinned=bool(ref)
    )

def parse_git_url(source: str) -> Optional[GitSource]:
    """
    Parse git source into a GitSource.
    
    Supports:
    - git@github.com:user/repo
    - https://github.com/user/repo
    - git:github.com/user/repo
    - Any of the above with @ref suffix
    """
    trimmed = source.strip()
    has_git_prefix = trimmed.startswith("git:")
    url = trimmed[4:].strip() if has_git_prefix else trimmed

    # Without git: prefix, only accept explicit protocol URLs or SCP-like
    if not has_git_prefix and not re.match(r"^(https?|ssh|git)://", url, re.I) and not url.startswith("git@"):
        return None

    # The TS implementation uses hosted-git-info which handles many shorthands.
    # For this Python port, we'll focus on the core requirements and generic parsing.
    # Since we don't have a direct equivalent of hosted-git-info in stdlib,
    # and the task asks for a port of the logic, we'll use parse_generic_git_url
    # which covers the requested formats.
    
    return parse_generic_git_url(url)

def get_current_branch(cwd: Optional[str] = None) -> Optional[str]:
    """Get current git branch."""
    try:
        result = subprocess.run(
            ["git", "symbolic-ref", "--short", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()
            
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()
            
        return None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

def get_repo_status(cwd: Optional[str] = None) -> dict[str, bool]:
    """Get repo status."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        output = result.stdout
        lines = output.splitlines()
        
        has_unstaged_changes = False
        has_staged_changes = False
        has_untracked_files = False
        
        for line in lines:
            if len(line) < 2:
                continue
            index_status = line[0]
            worktree_status = line[1]
            
            if index_status == "?":
                has_untracked_files = True
            if index_status not in (" ", "?"):
                has_staged_changes = True
            if worktree_status not in (" ", "?"):
                has_unstaged_changes = True
                
        is_clean = not (has_unstaged_changes or has_staged_changes or has_untracked_files)
        
        return {
            "has_unstaged_changes": has_unstaged_changes,
            "has_staged_changes": has_staged_changes,
            "has_untracked_files": has_untracked_files,
            "is_clean": is_clean
        }
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {
            "has_unstaged_changes": False,
            "has_staged_changes": False,
            "has_untracked_files": False,
            "is_clean": False
        }
