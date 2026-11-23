import json
import os
import tempfile
from pathlib import Path
import pytest
import sys
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from scripts.download_gold_standard import download_gold_standard, compute_sha256

@pytest.fixture
def temp_output_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@patch('scripts.download_gold_standard.load_dataset')
def test_download_gold_standard_creates_file(mock_load_dataset, temp_output_dir):
    """Test that a successful download creates the JSON file and checksum."""
    mock_dataset = [
        {"character": "Scrooge", "probe": "Test Probe", "label": 1, "rationale": "Because."},
        {"character": "Bennet", "probe": "Test Probe 2", "label": 0, "rationale": "Reason."}
    ]
    mock_load_dataset.return_value = mock_dataset

    output_file = download_gold_standard(temp_output_dir)

    assert output_file.exists()
    assert output_file.name == "human_annotations.json"
    
    # Check content
    with open(output_file) as f:
        data = json.load(f)
    assert len(data) == 2
    assert data[0]["character"] == "Scrooge"

    # Check checksum file exists
    checksum_file = temp_output_dir / "human_annotations.json.sha256"
    assert checksum_file.exists()

@patch('scripts.download_gold_standard.load_dataset')
def test_download_fails_loudly_on_error(mock_load_dataset, temp_output_dir):
    """Test that a fetch failure raises RuntimeError."""
    mock_load_dataset.side_effect = Exception("Dataset not found")

    with pytest.raises(RuntimeError) as excinfo:
        download_gold_standard(temp_output_dir)
    
    assert "Gold Standard dataset not found" in str(excinfo.value)

def test_compute_sha256(temp_output_dir):
    """Test SHA256 computation."""
    test_file = temp_output_dir / "test.txt"
    test_content = b"Hello World"
    test_file.write_bytes(test_content)
    
    checksum = compute_sha256(test_file)
    
    # Known SHA256 for "Hello World"
    expected = "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"
    assert checksum == expected
