import os
import sys
import json
import pytest
from pathlib import Path
import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analysis.pilot_runner import run_pilot
from config import ensure_directories

@pytest.fixture
def temp_test_dirs(tmp_path):
    """Create temporary directories for test data."""
    interim_dir = tmp_path / "data" / "interim"
    interim_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a minimal valid manifest for testing
    test_manifest = [
        {
            "stimulus_id": "test_001",
            "filename": "test_001.png",
            "emotion": "happy",
            "flanker_count": 3,
            "eccentricity": 2.0
        },
        {
            "stimulus_id": "test_002",
            "filename": "test_002.png",
            "emotion": "sad",
            "flanker_count": 5,
            "eccentricity": 4.0
        },
        {
            "stimulus_id": "test_003",
            "filename": "test_003.png",
            "emotion": "angry",
            "flanker_count": 4,
            "eccentricity": 3.0
        }
    ]
    
    manifest_path = interim_dir / "stimuli_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(test_manifest, f)
    
    return {
        "manifest": manifest_path,
        "output_dir": interim_dir
    }

def test_pilot_execution_creates_output(temp_test_dirs):
    """Test that pilot execution creates the expected output files."""
    manifest_path = temp_test_dirs["manifest"]
    output_dir = temp_test_dirs["output_dir"]
    
    # Run pilot with 3 participants
    stats = run_pilot(
        manifest_path=manifest_path,
        output_dir=output_dir,
        num_participants=3,
        seed=12345
    )
    
    # Verify stats
    assert stats["num_stimuli"] == 3
    assert stats["num_participants"] == 3
    assert stats["total_responses"] == 9  # 3 stimuli * 3 participants
    
    # Verify output file exists
    output_file = output_dir / "raw_synthetic_responses.csv"
    assert output_file.exists()
    
    # Verify CSV content
    df = pd.read_csv(output_file)
    assert len(df) == 9
    assert "participant_id" in df.columns
    assert "stimulus_id" in df.columns
    assert "true_label" in df.columns
    assert "response_label" in df.columns
    assert "accuracy" in df.columns
    
    # Verify accuracy values are 0 or 1
    assert df["accuracy"].isin([0, 1]).all()
    
    # Verify unique participants
    assert df["participant_id"].nunique() == 3

def test_pilot_execution_handles_empty_manifest(tmp_path):
    """Test that pilot execution handles empty manifest gracefully."""
    interim_dir = tmp_path / "data" / "interim"
    interim_dir.mkdir(parents=True, exist_ok=True)
    
    # Create empty manifest
    manifest_path = interim_dir / "empty_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump([], f)
    
    # Should raise ValueError for empty stimuli
    with pytest.raises(ValueError, match="Manifest contains no stimuli"):
        run_pilot(
            manifest_path=manifest_path,
            output_dir=interim_dir,
            num_participants=3,
            seed=42
        )

def test_pilot_execution_reproducibility(temp_test_dirs):
    """Test that pilot execution is reproducible with same seed."""
    manifest_path = temp_test_dirs["manifest"]
    output_dir = temp_test_dirs["output_dir"]
    
    # Run twice with same seed
    stats1 = run_pilot(
        manifest_path=manifest_path,
        output_dir=output_dir,
        num_participants=3,
        seed=99999
    )
    
    output_file1 = output_dir / "raw_synthetic_responses.csv"
    df1 = pd.read_csv(output_file1)
    
    # Run again with same seed
    stats2 = run_pilot(
        manifest_path=manifest_path,
        output_dir=output_dir,
        num_participants=3,
        seed=99999
    )
    
    output_file2 = output_dir / "raw_synthetic_responses.csv"
    df2 = pd.read_csv(output_file2)
    
    # Results should be identical
    assert stats1 == stats2
    assert df1.equals(df2)

def test_pilot_execution_various_participant_counts(temp_test_dirs):
    """Test pilot execution with different participant counts."""
    manifest_path = temp_test_dirs["manifest"]
    output_dir = temp_test_dirs["output_dir"]
    
    for num_participants in [1, 5, 10]:
        stats = run_pilot(
            manifest_path=manifest_path,
            output_dir=output_dir,
            num_participants=num_participants,
            seed=42
        )
        
        assert stats["num_participants"] == num_participants
        assert stats["total_responses"] == 3 * num_participants  # 3 stimuli