"""
Pytest configuration and shared fixtures for the llmXive research pipeline.

This module provides:
- Automatic fixture registration for shared resources.
- Temporary directories for isolated test execution.
- Mocked data paths pointing to realistic but temporary structures.
- Seed enforcement helpers for reproducibility.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Dict, Any

import pytest

# Ensure the project root (code/) is in the path for imports during tests
# The runner usually executes from the project root, but we ensure it here.
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import project utilities if available (optional, for seed setting)
try:
    from src.lib.utils import set_seed
except ImportError:
    # Fallback if utils isn't fully implemented yet, though T003 should be done
    def set_seed(seed: int = 42) -> None:
        import random
        import numpy as np
        try:
            import torch
            torch.manual_seed(seed)
        except ImportError:
            pass
        random.seed(seed)
        np.random.seed(seed)


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the path to the project root directory."""
    return PROJECT_ROOT


@pytest.fixture
def temp_project_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """
    Create a temporary directory structure mimicking the project layout.
    
    This fixture provides an isolated environment for tests that need to
    write files (e.g., data preprocessing, model outputs) without polluting
    the real project data or results directories.
    
    Structure created:
    - data/raw
    - data/processed
    - results
    - tests/unit (for nested test artifacts if needed)
    
    Yields:
        Path: The root of the temporary directory.
    """
    # Define subdirectories
    dirs = [
        "data/raw",
        "data/processed",
        "results",
        "tests/unit",
        "src/models",
        "src/analysis",
        "src/cli",
    ]
    
    for d in dirs:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)
    
    # Yield the temp root
    yield tmp_path
    
    # Cleanup happens automatically by pytest tmp_path fixture, 
    # but we can add specific teardown logic here if needed.


@pytest.fixture
def mocked_data_paths(temp_project_dir: Path) -> Dict[str, Path]:
    """
    Return a dictionary of mocked data paths within the temp directory.
    
    These paths are ready to be used by functions expecting to read/write
    raw or processed data, ensuring tests are isolated.
    
    Returns:
        Dict containing keys: 'raw', 'processed', 'results', 'state_file'
    """
    raw_dir = temp_project_dir / "data" / "raw"
    processed_dir = temp_project_dir / "data" / "processed"
    results_dir = temp_project_dir / "results"
    state_file = temp_project_dir / "data" / "state.json"
    
    return {
        "raw": raw_dir,
        "processed": processed_dir,
        "results": results_dir,
        "state_file": state_file,
        "checksum_file": temp_project_dir / "data" / "checksums.json"
    }


@pytest.fixture(autouse=True)
def reset_seeds() -> Generator[None, None, None]:
    """
    Automatically reset random seeds before each test to ensure reproducibility.
    
    This runs automatically for every test function in the project.
    """
    set_seed(42)
    yield
    # Optional: cleanup or logging after test


@pytest.fixture
def sample_code_snippet() -> Dict[str, Any]:
    """
    Provide a minimal valid code snippet dictionary for testing data models.
    
    Matches the expected schema for CodeSearchNet subsets.
    """
    return {
        "repo": "test/repo",
        "path": "src/test.py",
        "language": "python",
        "code": "def hello():\n    print('world')",
        "code_tokens": ["def", "hello", "(", ")", ":", "\n", "    ", "print", "(", "'world'", ")"],
        "docstring": "Prints hello world",
        "docstring_tokens": ["Prints", "hello", "world"]
    }


@pytest.fixture
def sample_query() -> Dict[str, Any]:
    """
    Provide a minimal valid query dictionary for testing retrieval.
    """
    return {
        "query": "function to print hello world",
        "query_tokens": ["function", "to", "print", "hello", "world"],
        "ground_truth": ["test/repo/src/test.py"]
    }