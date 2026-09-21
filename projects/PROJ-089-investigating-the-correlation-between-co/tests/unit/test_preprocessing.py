import pytest
import pandas as pd
import json
import os
import shutil
from pathlib import Path
from preprocessing import is_source_file, should_exclude_dir, filter_non_source_files

def test_is_source_file():
    assert is_source_file("main.py") is True
    assert is_source_file("script.js") is True
    assert is_source_file("app.tsx") is True
    assert is_source_file("server.go") is True
    assert is_source_file("lib.rs") is True
    assert is_source_file("index.html") is True
    assert is_source_file("style.css") is True
    assert is_source_file("readme.md") is False
    assert is_source_file("data.json") is False
    assert is_source_file("config.yaml") is False
    assert is_source_file("archive.tar.gz") is False
    assert is_source_file("") is False

def test_should_exclude_dir():
    assert should_exclude_dir("node_modules/pkg") is True
    assert should_exclude_dir("src/node_modules/lib") is True
    assert should_exclude_dir("venv/bin") is True
    assert should_exclude_dir("build/dist") is True
    assert should_exclude_dir("src/main") is False
    assert should_exclude_dir("tests/unit") is True
    assert should_exclude_dir("docs/api") is True
    assert should_exclude_dir("src/utils") is False

def test_filter_non_source_files_integration(tmp_path):
    # Setup test data
    git_dir = tmp_path / "data" / "raw" / "git_history"
    semgrep_dir = tmp_path / "data" / "raw" / "static_analysis"
    output_dir = tmp_path / "data" / "processed"
    
    git_dir.mkdir(parents=True)
    semgrep_dir.mkdir(parents=True)
    output_dir.mkdir(parents=True)
    
    repo_git = git_dir / "test_repo"
    repo_semgrep = semgrep_dir / "test_repo"
    repo_git.mkdir()
    repo_semgrep.mkdir()
    
    # Create fake git history
    git_df = pd.DataFrame({
        'file_path': [
            'src/main.py',
            'src/utils.py',
            'tests/test_main.py',
            'docs/readme.md',
            'node_modules/lib.js'
        ],
        'total_lines_changed': [100, 50, 20, 10, 500],
        'commit_count': [5, 2, 3, 1, 1]
    })
    git_df.to_csv(repo_git / "commits.csv", index=False)
    
    # Create fake semgrep results
    semgrep_data = {
        "results": [
            {"path": "src/main.py", "code_smells": 2, "cc": 5},
            {"path": "src/utils.py", "code_smells": 1, "cc": 3},
            {"path": "tests/test_main.py", "code_smells": 0, "cc": 2},
            {"path": "docs/readme.md", "code_smells": 0, "cc": 0},
            {"path": "node_modules/lib.js", "code_smells": 50, "cc": 100}
        ]
    }
    with open(repo_semgrep / "semgrep_results.json", 'w') as f:
        json.dump(semgrep_data, f)
    
    # Run filter
    output_file = output_dir / "filtered_metrics.csv"
    result_df = filter_non_source_files(git_dir, semgrep_dir, output_file)
    
    # Assertions
    assert output_file.exists()
    assert len(result_df) == 3 # src/main.py, src/utils.py, tests/test_main.py (tests are source code)
    
    # Verify excluded files are gone
    assert 'docs/readme.md' not in result_df['file_path'].values
    assert 'node_modules/lib.js' not in result_df['file_path'].values
    
    # Verify included files
    assert 'src/main.py' in result_df['file_path'].values
    assert 'src/utils.py' in result_df['file_path'].values
    assert 'tests/test_main.py' in result_df['file_path'].values
    
    # Verify numeric columns are present
    assert 'total_lines_changed' in result_df.columns
    assert 'code_smells' in result_df.columns