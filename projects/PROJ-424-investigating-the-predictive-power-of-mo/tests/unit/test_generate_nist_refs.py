import json
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.raw.generate_nist_refs import generate_nist_refs, init_manifest, compute_file_hash

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_generate_nist_refs_creates_file(temp_dir):
    """Test that generate_nist_refs creates a valid JSON file."""
    output_path = os.path.join(temp_dir, "nist_refs.json")
    
    result = generate_nist_refs(output_path)
    
    assert os.path.exists(result)
    assert result == output_path
    
    with open(result, 'r') as f:
        data = json.load(f)
    
    assert "metadata" in data
    assert "references" in data
    assert data["metadata"]["count"] == 3
    assert "water" in data["references"]
    assert "ethanol" in data["references"]
    assert "acetone" in data["references"]

def test_generate_nist_refs_has_real_ids(temp_dir):
    """Test that the generated file contains real NIST Accession IDs (no placeholders)."""
    output_path = os.path.join(temp_dir, "nist_refs.json")
    
    generate_nist_refs(output_path)
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    refs = data["references"]
    
    # Check that Accession IDs are present and not placeholders
    for solvent, info in refs.items():
        assert "accession_id" in info, f"Missing accession_id for {solvent}"
        assert not info["accession_id"].startswith("[Insert"), f"Placeholder ID found for {solvent}"
        assert len(info["accession_id"]) > 10, f"Accession ID too short for {solvent}"
        
        assert "url" in info
        assert "https" in info["url"]

def test_init_manifest_creates_checksum(temp_dir):
    """Test that init_manifest creates a valid manifest with checksum."""
    nist_path = os.path.join(temp_dir, "nist_refs.json")
    manifest_path = os.path.join(temp_dir, "manifest.json")
    
    # First generate the NIST file
    generate_nist_refs(nist_path)
    
    # Then generate manifest
    result = init_manifest(nist_path, manifest_path)
    
    assert os.path.exists(result)
    assert result == manifest_path
    
    with open(result, 'r') as f:
        manifest = json.load(f)
    
    assert "files" in manifest
    assert len(manifest["files"]) == 1
    
    file_entry = manifest["files"][0]
    assert "checksum_sha256" in file_entry
    assert len(file_entry["checksum_sha256"]) == 64  # SHA256 is 64 hex chars
    
    # Verify checksum matches actual file
    actual_checksum = compute_file_hash(nist_path)
    assert file_entry["checksum_sha256"] == actual_checksum

def test_diffusion_coefficients_are_realistic(temp_dir):
    """Test that the hardcoded diffusion coefficients are in realistic ranges."""
    output_path = os.path.join(temp_dir, "nist_refs.json")
    
    generate_nist_refs(output_path)
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    refs = data["references"]
    
    # Typical diffusion coefficients for small molecules in liquids are 1e-9 to 1e-8 m²/s
    expected_ranges = {
        "water": (1.0e-9, 3.0e-9),
        "ethanol": (0.8e-9, 2.0e-9),
        "acetone": (3.0e-9, 6.0e-9)
    }
    
    for solvent, (low, high) in expected_ranges.items():
        assert solvent in refs
        d_value = refs[solvent]["diffusion_coefficient_m2_s"]
        assert low <= d_value <= high, f"{solvent} diffusion coefficient {d_value} out of expected range [{low}, {high}]"

def test_metadata_has_required_fields(temp_dir):
    """Test that metadata contains required fields."""
    output_path = os.path.join(temp_dir, "nist_refs.json")
    
    generate_nist_refs(output_path)
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    meta = data["metadata"]
    assert "generated_at" in meta
    assert "version" in meta
    assert "description" in meta
    assert "count" in meta