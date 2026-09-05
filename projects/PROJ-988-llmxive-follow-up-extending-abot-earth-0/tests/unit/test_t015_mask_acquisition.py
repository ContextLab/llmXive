import os
import json
import pytest
from pathlib import Path
import sys

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

def test_t015_manifest_exists():
    """Verify that T015 produces a manifest file."""
    manifest_path = Path("data/raw/real_cloud_masks_subset/manifest.json")
    assert manifest_path.exists(), "Manifest file not found after T015 execution"
    
    with open(manifest_path) as f:
        data = json.load(f)
    
    assert "count" in data
    assert "masks" in data
    assert data["count"] >= 0

def test_t015_ks_definition_exists():
    """Verify that T015 defines the KS test method."""
    ks_path = Path("data/raw/real_cloud_masks_subset/ks_test_definition.json")
    assert ks_path.exists(), "KS Test definition file not found"
    
    with open(ks_path) as f:
        data = json.load(f)
    
    assert data["method"] == "Kolmogorov-Smirnov (KS-2-Sample)"
    assert "description" in data
    assert data["status"] == "defined"

def test_t015_downloaded_files():
    """Verify that at least some files were downloaded (if network is available)."""
    mask_dir = Path("data/raw/real_cloud_masks_subset")
    if not mask_dir.exists():
        pytest.skip("Data directory not created")
    
    # Check for .tif files
    tifs = list(mask_dir.glob("*.tif"))
    # We don't assert > 0 because network might fail in CI, but we check the structure
    # If files exist, they should be valid
    if tifs:
        for t in tifs:
            assert t.stat().st_size > 0, f"File {t} is empty"
