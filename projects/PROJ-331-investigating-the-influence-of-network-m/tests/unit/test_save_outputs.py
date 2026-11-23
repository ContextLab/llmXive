import os
import json
import tempfile
import shutil
import numpy as np
import pytest
from pathlib import Path

# Mock the config and utils if they are not fully implemented in the test environment
# But we assume they are available as per the task description
try:
    from save_outputs import compute_sha256_file, load_provenance_info, save_with_provenance
except ImportError:
    # Fallback for test environment if module not yet in path
    import sys
    sys.path.insert(0, 'code')
    from save_outputs import compute_sha256_file, load_provenance_info, save_with_provenance

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)

def test_compute_sha256_file(temp_dir):
    """Test SHA256 computation on a known file."""
    test_file = os.path.join(temp_dir, "test.txt")
    content = b"Hello, World!"
    with open(test_file, "wb") as f:
        f.write(content)

    checksum = compute_sha256_file(test_file)
    expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
    assert checksum == expected

def test_save_with_provenance_creates_files(temp_dir):
    """Test that save_with_provenance creates the required .npy and .json files."""
    # Create dummy data
    structural_data = np.random.rand(10, 10).astype(np.float32)
    rsfc_data = np.random.rand(10, 10).astype(np.float32)

    # Create dummy source files to satisfy provenance lookup
    processed_dir = os.path.join(temp_dir, "processed")
    os.makedirs(processed_dir)
    weighted_path = os.path.join(processed_dir, "weighted_adjacency.npy")
    eff_path = os.path.join(processed_dir, "global_efficiency.json")

    np.save(weighted_path, np.random.rand(10, 10))
    with open(eff_path, "w") as f:
        json.dump({"subject": "test", "efficiency": 0.5}, f)

    # Run save
    result = save_with_provenance(
        structural_data,
        rsfc_data,
        processed_dir,
        "test_subject"
    )

    # Assertions
    assert os.path.exists(result["structural_path"])
    assert os.path.exists(result["rsfc_path"])
    assert os.path.exists(result["provenance_path"])

    # Verify content
    with open(result["provenance_path"], "r") as f:
        prov = json.load(f)

    assert "sources" in prov
    assert "structural_matrix" in prov["sources"]
    assert "rsfc_matrix" in prov["sources"]
    assert "checksum_sha256" in prov["sources"]["structural_matrix"]
    assert prov["sources"]["structural_matrix"]["status"] != "missing"

def test_save_with_provenance_handles_missing_source(temp_dir):
    """Test behavior when a source file is missing."""
    structural_data = np.random.rand(5, 5).astype(np.float32)
    rsfc_data = np.random.rand(5, 5).astype(np.float32)

    processed_dir = os.path.join(temp_dir, "processed")
    os.makedirs(processed_dir)

    # Do NOT create the source files to simulate missing inputs
    result = save_with_provenance(
        structural_data,
        rsfc_data,
        processed_dir,
        "test_missing"
    )

    with open(result["provenance_path"], "r") as f:
        prov = json.load(f)

    # Should mark sources as missing but still save the new files
    assert prov["sources"]["weighted_adjacency"]["status"] == "missing"
    assert os.path.exists(result["structural_path"])
    assert os.path.exists(result["rsfc_path"])