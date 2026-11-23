"""
Pytest configuration and shared fixtures for the llmXive RAG Code Search project.

This module provides:
- Temporary project directory management
- Mocked data paths for unit/integration tests
- Deterministic seed resetting
- Sample data fixtures (snippets, queries, embeddings)
"""

import os
import sys
import tempfile
import shutil
import random
import numpy as np
import pytest
from pathlib import Path
from typing import Generator, Dict, List, Any

# Add project root to path if not already present
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the root path of the project."""
    return PROJECT_ROOT


@pytest.fixture(scope="function")
def temp_project_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory mimicking the project structure for testing.
    Yields the path and cleans up after the test.
    """
    temp_dir = tempfile.mkdtemp(prefix="llmxive_test_")
    temp_path = Path(temp_dir)

    # Create expected directory structure
    dirs = [
        "src/data", "src/models", "src/analysis", "src/cli", "src/lib",
        "data/raw", "data/processed", "results",
        "tests/unit", "tests/integration", "tests/contract"
    ]
    for d in dirs:
        (temp_path / d).mkdir(parents=True, exist_ok=True)

    yield temp_path

    # Cleanup
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture(scope="function")
def mocked_data_paths(temp_project_dir: Path) -> Dict[str, Path]:
    """
    Create and return paths for mocked data files within the temp directory.
    This allows tests to run without needing the full CodeSearchNet dataset.
    """
    train_dir = temp_project_dir / "data" / "processed" / "train"
    test_dir = temp_project_dir / "data" / "processed" / "test"
    train_dir.mkdir(parents=True, exist_ok=True)
    test_dir.mkdir(parents=True, exist_ok=True)

    # Create dummy files to satisfy existence checks
    (train_dir / "snippets.jsonl").touch()
    (test_dir / "snippets.jsonl").touch()
    (train_dir / "queries.jsonl").touch()
    (test_dir / "queries.jsonl").touch()

    return {
        "train_dir": train_dir,
        "test_dir": test_dir,
        "train_snippets": train_dir / "snippets.jsonl",
        "test_snippets": test_dir / "snippets.jsonl",
        "train_queries": train_dir / "queries.jsonl",
        "test_queries": test_dir / "queries.jsonl",
    }


@pytest.fixture(scope="function")
def reset_seeds() -> None:
    """
    Fixture to ensure deterministic behavior by resetting random seeds.
    Should be used at the start of tests that rely on randomness.
    """
    seed = 42
    random.seed(seed)
    np.random.seed(seed)
    if "torch" in sys.modules:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)


@pytest.fixture(scope="function")
def sample_code_snippet() -> Dict[str, Any]:
    """Return a sample code snippet dictionary matching the expected schema."""
    return {
        "code": "def add(a, b):\n    return a + b",
        "docstring": "Adds two numbers together.",
        "lang": "python",
        "repo": "test/repo",
        "path": "math_utils.py",
        "function_name": "add",
        "idx": 0
    }


@pytest.fixture(scope="function")
def sample_query() -> Dict[str, Any]:
    """Return a sample query dictionary matching the expected schema."""
    return {
        "query": "function to add two numbers",
        "docstring": "Adds two numbers together.",
        "lang": "python",
        "repo": "test/repo",
        "path": "math_utils.py",
        "function_name": "add",
        "idx": 0,
        "gold_idx": [0]
    }


@pytest.fixture(scope="function")
def sample_embeddings() -> np.ndarray:
    """Return a small array of dummy embeddings for testing retrieval logic."""
    # 3 snippets, 10 dimensions (simulating a small embedding size)
    np.random.seed(42)
    return np.random.rand(3, 10).astype(np.float32)


@pytest.fixture(scope="function")
def setup_path(temp_project_dir: Path) -> Path:
    """
    Helper fixture to ensure a specific path exists within the temp directory.
    Useful for tests that need to write to a specific subdirectory.
    """
    def _ensure_path(sub_path: str) -> Path:
        p = temp_project_dir / sub_path
        p.mkdir(parents=True, exist_ok=True)
        return p
    return _ensure_path