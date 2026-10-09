"""Integration test for the project .gitignore file.

This test verifies that the .gitignore file exists at the repository root
and contains the required ignore patterns:
  - data/
  - __pycache__/
  - *.pyc
  - .env (environment file)
  - venv/ (virtual environment directory)
"""

import pathlib

def test_gitignore_exists_and_contains_required_patterns():
    gitignore_path = pathlib.Path('.gitignore')
    assert gitignore_path.is_file(), ".gitignore file does not exist"

    content = gitignore_path.read_text()

    required_patterns = [
        "data/",
        "__pycache__/",
        "*.pyc",
        ".env",
        "venv/",
    ]

    for pattern in required_patterns:
        assert pattern in content, f"Required pattern '{pattern}' not found in .gitignore"