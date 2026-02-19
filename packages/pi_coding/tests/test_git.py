import os
import subprocess
import pytest
from pi_coding.utils.git import parse_git_url, get_current_branch, get_repo_status, GitSource

def test_parse_git_url_https():
    source = parse_git_url("https://github.com/user/repo")
    assert source is not None
    assert source.repo == "https://github.com/user/repo"
    assert source.host == "github.com"
    assert source.path == "user/repo"
    assert source.ref is None
    assert source.pinned is False

def test_parse_git_url_https_with_ref():
    source = parse_git_url("https://github.com/user/repo@main")
    assert source is not None
    assert source.repo == "https://github.com/user/repo"
    assert source.host == "github.com"
    assert source.path == "user/repo"
    assert source.ref == "main"
    assert source.pinned is True

def test_parse_git_url_ssh_scp():
    source = parse_git_url("git@github.com:user/repo")
    assert source is not None
    assert source.repo == "git@github.com:user/repo"
    assert source.host == "github.com"
    assert source.path == "user/repo"
    assert source.ref is None
    assert source.pinned is False

def test_parse_git_url_invalid():
    assert parse_git_url("not-a-url") is None
    assert parse_git_url("http://github.com/only-user") is None

def test_parse_git_url_removes_git_suffix():
    source = parse_git_url("https://github.com/user/repo.git")
    assert source is not None
    assert source.path == "user/repo"

def test_git_source_dataclass():
    source = GitSource(repo="repo", host="host", path="path", ref="ref", pinned=True)
    assert source.repo == "repo"
    assert source.host == "host"
    assert source.path == "path"
    assert source.ref == "ref"
    assert source.pinned is True
    assert source.type == "git"

def test_get_current_branch_no_repo(tmp_path):
    assert get_current_branch(str(tmp_path)) is None

def test_get_repo_status_no_repo(tmp_path):
    status = get_repo_status(str(tmp_path))
    assert status["is_clean"] is False
    assert status["has_unstaged_changes"] is False
    assert status["has_staged_changes"] is False
    assert status["has_untracked_files"] is False

@pytest.fixture
def git_repo(tmp_path):
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    cwd = str(repo_dir)
    subprocess.run(["git", "init"], cwd=cwd, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=cwd, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=cwd, capture_output=True, check=True)
    return repo_dir

def test_get_current_branch_in_repo(git_repo):
    # Default branch might be master or main
    branch = get_current_branch(str(git_repo))
    assert branch in ["master", "main"]

def test_get_repo_status_clean(git_repo):
    # Need at least one commit for some git operations, but status works on empty repo
    status = get_repo_status(str(git_repo))
    assert status["is_clean"] is True

def test_get_repo_status_unstaged(git_repo):
    file = git_repo / "test.txt"
    file.write_text("hello")
    subprocess.run(["git", "add", "test.txt"], cwd=str(git_repo), check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=str(git_repo), check=True)
    
    file.write_text("modified")
    status = get_repo_status(str(git_repo))
    assert status["has_unstaged_changes"] is True
    assert status["is_clean"] is False

def test_get_repo_status_untracked(git_repo):
    file = git_repo / "untracked.txt"
    file.write_text("untracked")
    status = get_repo_status(str(git_repo))
    assert status["has_untracked_files"] is True
    assert status["is_clean"] is False

def test_get_repo_status_staged(git_repo):
    file = git_repo / "staged.txt"
    file.write_text("staged")
    subprocess.run(["git", "add", "staged.txt"], cwd=str(git_repo), check=True)
    status = get_repo_status(str(git_repo))
    assert status["has_staged_changes"] is True
    assert status["is_clean"] is False
