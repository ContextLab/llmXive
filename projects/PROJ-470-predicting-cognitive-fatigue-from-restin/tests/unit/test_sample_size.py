import os
import sys
import json
import tempfile
import pytest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.check_sample_size import check_sample_size, load_config, write_validation_report

@pytest.fixture
def temp_manifest_dir(tmp_path):
    """Create a temporary directory structure for testing."""
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    return raw_dir

@pytest.fixture
def valid_manifest(temp_manifest_dir):
    """Create a valid manifest with N >= 30."""
    manifest = {
        "variables": ["eeg_data", "fatigue_rating"],
        "participants": [{"id": f"sub-{i:03d}"} for i in range(35)]
    }
    manifest_path = temp_manifest_dir / "download_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f)
    return str(manifest_path)

@pytest.fixture
def insufficient_manifest(temp_manifest_dir):
    """Create a manifest with N < 30."""
    manifest = {
        "variables": ["eeg_data", "fatigue_rating"],
        "participants": [{"id": f"sub-{i:03d}"} for i in range(15)]
    }
    manifest_path = temp_manifest_dir / "download_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f)
    return str(manifest_path)

@pytest.fixture
def missing_vars_manifest(temp_manifest_dir):
    """Create a manifest with N >= 30 but missing required variables."""
    manifest = {
        "variables": ["eeg_data"], # Missing fatigue_rating
        "participants": [{"id": f"sub-{i:03d}"} for i in range(35)]
    }
    manifest_path = temp_manifest_dir / "download_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f)
    return str(manifest_path)

def test_sample_size_sufficient(valid_manifest, tmp_path):
    """Test that check_sample_size returns True when N >= 30."""
    # Mock the global PROJECT_ROOT path for the function
    import code.check_sample_size as cs
    original_root = cs.PROJECT_ROOT
    cs.PROJECT_ROOT = tmp_path / "data" # Set base to tmp_path/data so raw is tmp_path/data/raw
    
    # We need to adjust the path logic inside the function or mock the file existence
    # Since the function hardcodes PROJECT_ROOT / "data" / "raw" / "download_manifest.json"
    # We'll create the structure accordingly
    (tmp_path / "data" / "raw").mkdir(parents=True)
    import shutil
    shutil.copy(valid_manifest, tmp_path / "data" / "raw" / "download_manifest.json")
    
    result = check_sample_size({})
    
    # Restore
    cs.PROJECT_ROOT = original_root
    
    assert result is True
    assert os.path.exists(tmp_path / "data" / "processed" / "sample_size_validation.json")
    
    with open(tmp_path / "data" / "processed" / "sample_size_validation.json", 'r') as f:
        report = json.load(f)
    assert report["valid"] is True

def test_sample_size_insufficient(insufficient_manifest, tmp_path):
    """Test that check_sample_size returns False when N < 30."""
    import code.check_sample_size as cs
    original_root = cs.PROJECT_ROOT
    cs.PROJECT_ROOT = tmp_path / "data"
    
    (tmp_path / "data" / "raw").mkdir(parents=True)
    import shutil
    shutil.copy(insufficient_manifest, tmp_path / "data" / "raw" / "download_manifest.json")
    
    result = check_sample_size({})
    
    cs.PROJECT_ROOT = original_root
    
    assert result is False
    assert os.path.exists(tmp_path / "data" / "processed" / "sample_size_validation.json")
    
    with open(tmp_path / "data" / "processed" / "sample_size_validation.json", 'r') as f:
        report = json.load(f)
    assert report["valid"] is False
    assert "Sample size constraint failed" in report["message"]

def test_missing_required_variables(missing_vars_manifest, tmp_path):
    """Test that check_sample_size fails if required variables are missing."""
    import code.check_sample_size as cs
    original_root = cs.PROJECT_ROOT
    cs.PROJECT_ROOT = tmp_path / "data"
    
    (tmp_path / "data" / "raw").mkdir(parents=True)
    import shutil
    shutil.copy(missing_vars_manifest, tmp_path / "data" / "raw" / "download_manifest.json")
    
    result = check_sample_size({})
    
    cs.PROJECT_ROOT = original_root
    
    # Even if N >= 30, missing variables should cause failure per FR-001 logic
    assert result is False
    
    with open(tmp_path / "data" / "processed" / "sample_size_validation.json", 'r') as f:
        report = json.load(f)
    assert report["valid"] is False
    assert "fatigue_rating" in str(report.get("missing_variables", []))

def test_manifest_not_found(tmp_path):
    """Test that check_sample_size fails if manifest is missing."""
    import code.check_sample_size as cs
    original_root = cs.PROJECT_ROOT
    cs.PROJECT_ROOT = tmp_path / "data"
    
    # Ensure raw directory exists but manifest does not
    (tmp_path / "data" / "raw").mkdir(parents=True)
    
    result = check_sample_size({})
    
    cs.PROJECT_ROOT = original_root
    
    assert result is False
    assert os.path.exists(tmp_path / "data" / "processed" / "sample_size_validation.json")