import os
import sys
import tempfile
import json
import pytest
from pathlib import Path

@pytest.fixture
def add_code_root_to_path():
    """Add code root to sys.path for imports."""
    code_root = Path(__file__).parent.parent
    if str(code_root) not in sys.path:
        sys.path.insert(0, str(code_root))
    return code_root

@pytest.fixture
def project_root(add_code_root_to_path):
    """Get the project root directory."""
    return add_code_root_to_path.parent

@pytest.fixture
def code_root_dir(project_root):
    """Get the code directory."""
    return project_root / "code"

@pytest.fixture
def temp_dir():
    """Create a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_jsonl_file(temp_dir):
    """Create a sample JSONL file."""
    file_path = temp_dir / "sample.jsonl"
    data = [
        {"text": "Hello world", "id": 1},
        {"text": "Test data", "id": 2},
        {"text": "More text", "id": 3}
    ]
    with open(file_path, 'w') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')
    return file_path

@pytest.fixture
def sample_config_file(temp_dir):
    """Create a sample config file."""
    file_path = temp_dir / "config.yaml"
    config = {
        "model": {
            "embed_dim": 128,
            "num_heads": 2
        },
        "training": {
            "learning_rate": 0.001
        }
    }
    import yaml
    with open(file_path, 'w') as f:
        yaml.dump(config, f)
    return file_path
