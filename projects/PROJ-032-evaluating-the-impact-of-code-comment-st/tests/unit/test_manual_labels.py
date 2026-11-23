import os
import pytest
import csv
from pathlib import Path
from manual_labels_generator import (
    get_repos_with_git_history,
    get_commits_for_repo,
    is_bug_fix_heuristic,
    stratified_sample_commits,
    generate_labels,
    save_labels
)

@pytest.fixture
def sample_repo(tmp_path):
    """Create a temporary git repo with sample commits for testing."""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()
    os.system(f"cd {repo_path} && git init")
    
    # Create a file
    test_file = repo_path / "test.py"
    test_file.write_text("print('hello')")
    
    # Commit 1: Bug fix
    os.system(f"cd {repo_path} && git add . && git commit -m 'Fix: resolve crash in module'")
    
    # Commit 2: Feature
    test_file.write_text("print('hello world')")
    os.system(f"cd {repo_path} && git add . && git commit -m 'Add new feature'")
    
    # Commit 3: Another bug fix
    test_file.write_text("print('fixed')")
    os.system(f"cd {repo_path} && git add . && git commit -m 'Fix typo in variable name'")
    
    return repo_path

def test_get_repos_with_git_history(tmp_path):
    # Create a fake repo structure
    valid_repo = tmp_path / "valid_repo"
    valid_repo.mkdir()
    (valid_repo / ".git").mkdir()
    
    invalid_repo = tmp_path / "invalid_repo"
    invalid_repo.mkdir()
    
    repos = get_repos_with_git_history(str(tmp_path))
    assert len(repos) == 1
    assert repos[0].name == "valid_repo"

def test_is_bug_fix_heuristic():
    assert is_bug_fix_heuristic("Fix crash") == True
    assert is_bug_fix_heuristic("fix: resolve issue") == True
    assert is_bug_fix_heuristic("Add feature") == False
    assert is_bug_fix_heuristic("Update docs") == False
    assert is_bug_fix_heuristic("Revert bad commit") == True

def test_stratified_sample_commits():
    commits = [
        ("hash1", "Fix bug"),
        ("hash2", "Feature"),
        ("hash3", "Fix crash"),
        ("hash4", "Refactor"),
        ("hash5", "Fix typo"),
        ("hash6", "Add test")
    ]
    sampled = stratified_sample_commits(commits, target_per_repo=3)
    
    # Should have 3 items
    assert len(sampled) == 3
    
    # Check that labels are present
    for item in sampled:
        assert len(item) == 3
        assert item[2] in ["bug_fix", "not_bug_fix"]

def test_save_labels(tmp_path):
    labels = [
        {"repo_id": "repo1", "commit_hash": "abc123", "message": "Fix bug", "label": "bug_fix"},
        {"repo_id": "repo1", "commit_hash": "def456", "message": "Feature", "label": "not_bug_fix"}
    ]
    output_path = tmp_path / "test_labels.csv"
    
    save_labels(labels, str(output_path))
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]["label"] == "bug_fix"
        assert rows[1]["label"] == "not_bug_fix"
