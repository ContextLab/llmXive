"""
Pytest configuration and fixtures for the llmXive project.

Provides shared fixtures for project paths, temporary directories, and sample data.
"""
import os
import sys
import tempfile
import json
import pytest
from pathlib import Path

# Add code root to path for imports
@pytest.fixture(autouse=True)
def add_code_root_to_path():
    """Automatically add the code root to sys.path for all tests."""
    code_root = Path(__file__).parent.parent
    if str(code_root) not in sys.path:
        sys.path.insert(0, str(code_root))
    yield
    # Cleanup if needed
    if str(code_root) in sys.path:
        sys.path.remove(str(code_root))

@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent.parent.parent

@pytest.fixture(scope="session")
def code_root_dir() -> Path:
    """Return the code root directory."""
    return Path(__file__).parent.parent

@pytest.fixture(scope="function")
def temp_dir() -> Path:
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture(scope="function")
def sample_jsonl_file(temp_dir: Path) -> Path:
    """Create a sample JSONL file for testing."""
    file_path = temp_dir / "sample_data.jsonl"
    sample_data = [
        {"id": 1, "text": "Sample text 1", "tokens": 10},
        {"id": 2, "text": "Sample text 2", "tokens": 15},
        {"id": 3, "text": "Sample text 3", "tokens": 8},
    ]
    with open(file_path, "w", encoding="utf-8") as f:
        for item in sample_data:
            f.write(json.dumps(item) + "\n")
    return file_path

@pytest.fixture(scope="function")
def sample_config_file(temp_dir: Path) -> Path:
    """Create a sample configuration file for testing."""
    file_path = temp_dir / "sample_config.yaml"
    config_data = {
        "model": {
            "embed_dim": 768,
            "num_heads": 12,
            "num_layers": 6,
            "vocab_size": 50257,
            "max_seq_length": 1024
        },
        "training": {
            "learning_rate": 1e-4,
            "batch_size": 8,
            "num_epochs": 10,
            "dropout": 0.1
        }
    }
    import yaml
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f)
    return file_path
