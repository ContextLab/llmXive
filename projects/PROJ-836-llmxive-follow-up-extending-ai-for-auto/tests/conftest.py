"""
Base fixtures for pytest in the llmXive project.

This module provides shared fixtures for unit and integration tests,
including temporary directories, mock data paths, and configuration helpers.
"""
import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for test artifacts.

    Yields:
        Path: A temporary directory path.
    """
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)


@pytest.fixture
def project_root() -> Path:
    """
    Return the project root directory.

    Assumes the project structure is:
    repo_root/
      code/
      data/
      tests/
      ...

    Returns:
        Path: The path to the project root.
    """
    # Assuming tests/ is at the root of the project
    return Path(__file__).parent.parent


@pytest.fixture
def data_dir(project_root: Path) -> Path:
    """
    Return the path to the data directory.

    Args:
        project_root (Path): The project root directory.

    Returns:
        Path: The path to the data directory.
    """
    return project_root / "data"


@pytest.fixture
def code_dir(project_root: Path) -> Path:
    """
    Return the path to the code directory.

    Args:
        project_root (Path): The project root directory.

    Returns:
        Path: The path to the code directory.
    """
    return project_root / "code"


@pytest.fixture
def config_dir(project_root: Path) -> Path:
    """
    Return the path to the config directory.

    Args:
        project_root (Path): The project root directory.

    Returns:
        Path: The path to the config directory.
    """
    return project_root / "config"


@pytest.fixture
def sample_text() -> str:
    """
    Provide a sample text string for testing text processing functions.

    Returns:
        str: A sample text string.
    """
    return (
        "Recent studies have shown that citation isolation in literature reviews "
        "can lead to hallucinated claims. For example, Smith et al. (2023) found "
        "that 40% of ungrounded claims were not supported by external references. "
        "This phenomenon is particularly prevalent in automated systems."
    )


@pytest.fixture
def empty_text() -> str:
    """
    Provide an empty string for testing edge cases.

    Returns:
        str: An empty string.
    """
    return ""


@pytest.fixture
def short_text() -> str:
    """
    Provide a very short text string for testing edge cases.

    Returns:
        str: A short string.
    """
    return "Short text."


@pytest.fixture
def mock_feature_matrix_path(temp_dir: Path) -> Path:
    """
    Create a mock feature matrix CSV file for testing.

    Args:
        temp_dir (Path): A temporary directory.

    Returns:
        Path: The path to the mock feature matrix file.
    """
    file_path = temp_dir / "mock_feature_matrix.csv"
    content = (
        "cycle_density,citation_isolation,semantic_distance,label\n"
        "0.15,0.45,0.32,1\n"
        "0.00,0.10,0.85,0\n"
        "0.22,0.60,0.15,1\n"
        "0.05,0.05,0.50,0\n"
    )
    file_path.write_text(content)
    return file_path


@pytest.fixture
def mock_metadata_path(temp_dir: Path) -> Path:
    """
    Create a mock metadata JSON file for testing.

    Args:
        temp_dir (Path): A temporary directory.

    Returns:
        Path: The path to the mock metadata file.
    """
    file_path = temp_dir / "mock_metadata.json"
    content = (
        '[{"id": "1", "label": 1, "source_type": "wet-lab"}, '
        '{"id": "2", "label": 0, "source_type": "simulation"}]'
    )
    file_path.write_text(content)
    return file_path