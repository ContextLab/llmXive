"""
Pytest configuration and fixtures for llmXive project tests.

Provides shared fixtures for all test modules including:
- project_root: Path to the project root directory
- code_root: Path to the code directory
- temp_dir: Temporary directory for test artifacts
- sample_jsonl_file: Path to a sample JSONL file for testing
- sample_config_file: Path to a sample configuration file for testing
"""

import os
import sys
import tempfile
import json
import pytest
from pathlib import Path

# Ensure code root is in path
code_root = Path(__file__).parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

@pytest.fixture(scope="session")
def project_root() -> Path:
    """Get the project root directory."""
    return code_root.parent

@pytest.fixture(scope="session")
def code_root() -> Path:
    """Get the code root directory."""
    return code_root

@pytest.fixture(scope="function")
def temp_dir() -> Path:
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture(scope="function")
def sample_jsonl_file(temp_dir: Path) -> Path:
    """Create a sample JSONL file for testing."""
    file_path = temp_dir / "sample.jsonl"
    sample_data = [
        {"text": "Sample text 1", "id": "1"},
        {"text": "Sample text 2", "id": "2"},
        {"text": "Sample text 3", "id": "3"},
    ]
    with open(file_path, "w", encoding="utf-8") as f:
        for item in sample_data:
            f.write(json.dumps(item) + "\n")
    return file_path

@pytest.fixture(scope="function")
def sample_config_file(temp_dir: Path) -> Path:
    """Create a sample configuration file for testing."""
    file_path = temp_dir / "config.yaml"
    sample_config = {
        "project": {
            "name": "test_project",
            "version": "0.1.0"
        },
        "data": {
            "token_limit": 1000000,
            "max_ram_gb": 8.0,
            "train_split_ratio": 0.8
        },
        "model": {
            "embed_dim": 768,
            "num_heads": 12,
            "num_layers": 12,
            "vocab_size": 50257,
            "max_seq_length": 1024
        },
        "training": {
            "learning_rate": 1e-4,
            "batch_size": 32,
            "num_epochs": 10,
            "dropout": 0.1,
            "weight_decay": 0.01,
            "warmup_steps": 100
        }
    }
    import yaml
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.dump(sample_config, f)
    return file_path
