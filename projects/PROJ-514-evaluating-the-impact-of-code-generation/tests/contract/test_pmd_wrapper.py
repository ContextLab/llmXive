"""
Contract tests for the PMD CLI wrapper (run_pmd.py).

These tests define the expected interface and behavior of the PMD wrapper
before implementation is complete. They must pass once the implementation is correct.
"""

import os
import sys
import json
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest

# We will import the module once implemented
# from code.02_static_analysis.run_pmd import run_pmd_on_file, run_pmd_batch

# Constants for test data
TEST_PYTHON_CODE_CLEAN = """
def add(a, b):
    return a + b
"""

TEST_PYTHON_CODE_SMELL = """
def long_function_with_too_many_lines(a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t, u, v, w, x, y, z):
    # This is a very long function that should trigger LongMethod
    result = a + b + c + d + e + f + g + h + i + j + k + l + m + n + o + p + q + r + s + t + u + v + w + x + y + z
    result = result * 2
    result = result + 10
    result = result - 5
    result = result / 2
    result = result ** 2
    result = result % 3
    result = result & 1
    result = result | 2
    result = result ^ 3
    result = result << 1
    result = result >> 1
    result = result // 2
    result = result + a
    result = result + b
    result = result + c
    result = result + d
    result = result + e
    result = result + f
    result = result + g
    result = result + h
    result = result + i
    result = result + j
    result = result + k
    result = result + l
    result = result + m
    result = result + n
    result = result + o
    result = result + p
    result = result + q
    result = result + r
    result = result + s
    result = result + t
    result = result + u
    result = result + v
    result = result + w
    result = result + x
    result = result + y
    result = result + z
    return result
"""

@pytest.fixture
def temp_clean_file():
    """Create a temporary clean Python file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(TEST_PYTHON_CODE_CLEAN)
        path = Path(f.name)
    yield path
    path.unlink()

@pytest.fixture
def temp_smell_file():
    """Create a temporary file with code smells."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(TEST_PYTHON_CODE_SMELL)
        path = Path(f.name)
    yield path
    path.unlink()

@pytest.fixture
def temp_invalid_file():
    """Create a temporary file with invalid Python syntax."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("def invalid(\n")  # Missing closing parenthesis
        path = Path(f.name)
    yield path
    path.unlink()

@pytest.mark.skip(reason="Implementation pending - defines interface for T021")
def test_run_pmd_on_file_clean_code(temp_clean_file):
    """
    Test that run_pmd_on_file returns success and no violations for clean code.
    
    Interface:
        def run_pmd_on_file(file_path: Path, ruleset_path: Path, timeout: int = 120) -> Dict[str, Any]
    
    Expected:
        - exit_code == 0
        - violations == []
        - success == True
    """
    # from code.02_static_analysis.run_pmd import run_pmd_on_file
    # result = run_pmd_on_file(temp_clean_file, Path("code/utils/pmd_rulesets/python-smells.xml"))
    # assert result["success"] is True
    # assert result["exit_code"] == 0
    # assert len(result.get("violations", [])) == 0
    pass

@pytest.mark.skip(reason="Implementation pending - defines interface for T021")
def test_run_pmd_on_file_with_smells(temp_smell_file):
    """
    Test that run_pmd_on_file detects smells in code with violations.
    
    Interface:
        def run_pmd_on_file(file_path: Path, ruleset_path: Path, timeout: int = 120) -> Dict[str, Any]
    
    Expected:
        - exit_code == 0 (PMD runs successfully, even if it finds issues)
        - violations list is not empty
        - success == True
    """
    # from code.02_static_analysis.run_pmd import run_pmd_on_file
    # result = run_pmd_on_file(temp_smell_file, Path("code/utils/pmd_rulesets/python-smells.xml"))
    # assert result["success"] is True
    # assert result["exit_code"] == 0
    # assert len(result.get("violations", [])) > 0
    pass

@pytest.mark.skip(reason="Implementation pending - defines interface for T021")
def test_run_pmd_on_file_invalid_syntax(temp_invalid_file):
    """
    Test that run_pmd_on_file handles invalid syntax gracefully.
    
    Interface:
        def run_pmd_on_file(file_path: Path, ruleset_path: Path, timeout: int = 120) -> Dict[str, Any]
    
    Expected:
        - success == False (or handled gracefully)
        - error message present
    """
    # from code.02_static_analysis.run_pmd import run_pmd_on_file
    # result = run_pmd_on_file(temp_invalid_file, Path("code/utils/pmd_rulesets/python-smells.xml"))
    # assert result["success"] is False
    # assert "error" in result or "exception" in result
    pass

@pytest.mark.skip(reason="Implementation pending - defines interface for T021")
def test_run_pmd_on_file_timeout():
    """
    Test that run_pmd_on_file handles timeout correctly.
    
    Interface:
        def run_pmd_on_file(file_path: Path, ruleset_path: Path, timeout: int = 120) -> Dict[str, Any]
    
    Expected:
        - success == False
        - error message indicates timeout
    """
    # This would require a file that causes PMD to hang, which is hard to create
    # We can mock the subprocess call to test the timeout logic
    pass

@pytest.mark.skip(reason="Implementation pending - defines interface for T021")
def test_run_pmd_batch():
    """
    Test that run_pmd_batch processes multiple files correctly.
    
    Interface:
        def run_pmd_batch(
            files: List[Path], 
            ruleset_paths: List[Path], 
            timeout_per_file: int = 120,
            max_workers: int = 4
        ) -> Dict[str, Dict[str, Any]]
    
    Expected:
        - Returns a dict mapping file paths to results
        - Each result follows the same structure as run_pmd_on_file
    """
    # from code.02_static_analysis.run_pmd import run_pmd_batch
    # files = [temp_clean_file, temp_smell_file]
    # results = run_pmd_batch(files, [Path("code/utils/pmd_rulesets/python-smells.xml")])
    # assert len(results) == 2
    # assert str(temp_clean_file) in results
    # assert str(temp_smell_file) in results
    pass