"""
Tests to verify the project structure was created correctly.
"""
import os
from pathlib import Path

def test_project_root_exists():
    """Test that the project root directory exists."""
    project_root = Path("projects/PROJ-188-evaluating-the-impact-of-llm-generated-c")
    assert project_root.exists(), f"Project root {project_root} does not exist"
    assert project_root.is_dir(), f"{project_root} is not a directory"

def test_code_directory_exists():
    """Test that the code/ subdirectory exists."""
    code_dir = Path("projects/PROJ-188-evaluating-the-impact-of-llm-generated-c/code")
    assert code_dir.exists(), f"Code directory {code_dir} does not exist"
    assert code_dir.is_dir(), f"{code_dir} is not a directory"

def test_tests_directory_exists():
    """Test that the tests/ subdirectory exists."""
    tests_dir = Path("projects/PROJ-188-evaluating-the-impact-of-llm-generated-c/tests")
    assert tests_dir.exists(), f"Tests directory {tests_dir} does not exist"
    assert tests_dir.is_dir(), f"{tests_dir} is not a directory"

def test_data_directories_exist():
    """Test that data/ subdirectories exist."""
    data_dir = Path("projects/PROJ-188-evaluating-the-impact-of-llm-generated-c/data")
    raw_dir = data_dir / "raw"
    intermediate_dir = data_dir / "intermediate"
    processed_dir = data_dir / "processed"
    
    assert data_dir.exists(), f"Data directory {data_dir} does not exist"
    assert raw_dir.exists(), f"Raw directory {raw_dir} does not exist"
    assert intermediate_dir.exists(), f"Intermediate directory {intermediate_dir} does not exist"
    assert processed_dir.exists(), f"Processed directory {processed_dir} does not exist"

def test_init_files_exist():
    """Test that __init__.py files exist in code/ and tests/."""
    code_init = Path("projects/PROJ-188-evaluating-the-impact-of-llm-generated-c/code/__init__.py")
    tests_init = Path("projects/PROJ-188-evaluating-the-impact-of-llm-generated-c/tests/__init__.py")
    
    assert code_init.exists(), f"__init__.py not found in code directory"
    assert tests_init.exists(), f"__init__.py not found in tests directory"
    
    # Verify they are files
    assert code_init.is_file(), f"{code_init} is not a file"
    assert tests_init.is_file(), f"{tests_init} is not a file"