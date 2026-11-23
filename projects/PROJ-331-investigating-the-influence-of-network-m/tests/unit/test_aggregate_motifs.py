import os
import json
import numpy as np
import pytest
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from motifs import aggregate_motif_profiles
from utils import safe_write_json, load_npy

@pytest.fixture
def temp_processed_dir(tmp_path):
    """Create a temporary data/processed directory with mock motif z-score files."""
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Create mock motif z-score files for 10p, 20p, 30p
    motif_z_10p = {
        "0,0,0,0,0,0,0,0,0": 1.5,
        "0,0,0,0,0,0,0,1,0": 2.0,
        "1,0,0,0,0,0,0,0,0": -1.0
    }
    
    motif_z_20p = {
        "0,0,0,0,0,0,0,0,0": 1.6,
        "0,0,0,0,0,0,0,1,0": 1.8,
        "1,0,0,0,0,0,0,0,0": -0.9,
        "0,1,0,0,0,0,0,0,0": 0.5
    }
    
    motif_z_30p = {
        "0,0,0,0,0,0,0,0,0": 1.4,
        "0,0,0,0,0,0,0,1,0": 2.2,
        "1,0,0,0,0,0,0,0,0": -1.1
    }
    
    # Write files
    safe_write_json(str(processed_dir / "motif_z_10p.json"), motif_z_10p)
    safe_write_json(str(processed_dir / "motif_z_20p.json"), motif_z_20p)
    safe_write_json(str(processed_dir / "motif_z_30p.json"), motif_z_30p)
    
    return processed_dir

def test_aggregate_motif_profiles_creates_output(temp_processed_dir, tmp_path):
    """Test that aggregate_motif_profiles creates the output file with correct structure."""
    # Change to temp directory to simulate project root
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Run aggregation
        result = aggregate_motif_profiles()
        
        # Check output file exists
        output_path = tmp_path / "data" / "processed" / "motif_profiles.json"
        assert output_path.exists(), "motif_profiles.json was not created"
        
        # Load and verify content
        with open(output_path) as f:
            profiles = json.load(f)
        
        # Verify metadata
        assert "metadata" in profiles
        assert profiles["metadata"]["aggregation_method"] == "median"
        assert "motifs" in profiles
        
        # Verify specific motif calculations
        # Motif "0,0,0,0,0,0,0,0,0": [1.5, 1.6, 1.4] -> median 1.5
        motif_0 = profiles["motifs"]["0,0,0,0,0,0,0,0,0"]
        assert abs(motif_0["median_z"] - 1.5) < 1e-6
        assert motif_0["z_10p"] == 1.5
        assert motif_0["z_20p"] == 1.6
        assert motif_0["z_30p"] == 1.4
        assert motif_0["count_thresholds"] == 3
        
        # Motif "0,0,0,0,0,0,0,1,0": [2.0, 1.8, 2.2] -> median 2.0
        motif_1 = profiles["motifs"]["0,0,0,0,0,0,0,1,0"]
        assert abs(motif_1["median_z"] - 2.0) < 1e-6
        
        # Motif "1,0,0,0,0,0,0,0,0": [-1.0, -0.9, -1.1] -> median -1.0
        motif_2 = profiles["motifs"]["1,0,0,0,0,0,0,0,0"]
        assert abs(motif_2["median_z"] - (-1.0)) < 1e-6
        
        # Motif "0,1,0,0,0,0,0,0,0": only in 20p -> median 0.5
        motif_3 = profiles["motifs"]["0,1,0,0,0,0,0,0,0"]
        assert abs(motif_3["median_z"] - 0.5) < 1e-6
        assert motif_3["count_thresholds"] == 1
        
    finally:
        os.chdir(original_cwd)

def test_aggregate_motif_profiles_missing_input():
    """Test that aggregate_motif_profiles raises FileNotFoundError for missing input."""
    # Create a temp dir without the required files
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        os.chdir(tmp_dir)
        os.makedirs("data/processed", exist_ok=True)
        
        with pytest.raises(FileNotFoundError):
            aggregate_motif_profiles()
