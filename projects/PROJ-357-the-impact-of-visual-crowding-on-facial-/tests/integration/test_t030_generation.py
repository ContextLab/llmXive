"""
Integration test for T030: Generate human_judgments.csv
This test verifies that the script runs, produces the correct file, and the data has the required schema.
"""
import os
import sys
import json
import tempfile
import shutil
import pandas as pd
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import ensure_directories, set_all_seeds
from utils.stimuli_manifest import generate_manifest as gen_manifest
from analysis.pilot_runner import run_pilot
from analysis.generate_human_judgments import main as generate_judgments_main

@pytest.fixture(scope="module")
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = Path(tempfile.mkdtemp())
    # Create necessary subdirectories
    (temp_dir / "interim" / "stimuli").mkdir(parents=True)
    (temp_dir / "interim" / "raw_judgments").mkdir(parents=True)
    (temp_dir / "processed").mkdir(parents=True)
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_t030_pipeline(temp_data_dir):
    """
    End-to-end test for T030:
    1. Create a minimal manifest (simulating T014)
    2. Run pilot runner to generate raw judgments (simulating T027)
    3. Run T030 script to generate human_judgments.csv
    4. Verify output schema and content
    """
    set_all_seeds()
    
    # 1. Setup minimal manifest
    manifest_path = temp_data_dir / "interim" / "stimuli_manifest.json"
    mock_stimuli = [
        {
            "file_path": "stim_001.png",
            "emotion_label": "happy",
            "flanker_count": 4,
            "eccentricity": 2.5
        },
        {
            "file_path": "stim_002.png",
            "emotion_label": "sad",
            "flanker_count": 8,
            "eccentricity": 5.0
        }
    ]
    with open(manifest_path, 'w') as f:
        json.dump(mock_stimuli, f)

    # Create dummy stimulus files (needed for pilot runner to find them)
    for stim in mock_stimuli:
        (temp_data_dir / "interim" / "stimuli" / stim["file_path"]).touch()

    # 2. Run pilot runner to generate raw judgments
    # We call the underlying logic directly to avoid CLI overhead in tests
    from analysis.synthetic_data_generator import load_manifest, generate_synthetic_responses, save_responses
    
    manifest = load_manifest(manifest_path)
    raw_judgments_dir = temp_data_dir / "interim" / "raw_judgments"
    
    # Generate synthetic responses
    responses = generate_synthetic_responses(manifest, num_participants=3)
    save_responses(responses, raw_judgments_dir)

    # 3. Run T030 generation script
    output_path = temp_data_dir / "processed" / "human_judgments.csv"
    
    # Mock command line arguments
    sys.argv = [
        'test',
        '--manifest', str(manifest_path),
        '--raw-data', str(raw_judgments_dir),
        '--output', str(output_path)
    ]
    
    generate_judgments_main()

    # 4. Verify output
    assert output_path.exists(), "Output file human_judgments.csv was not created"
    
    df = pd.read_csv(output_path)
    
    # Check required columns
    required_cols = ['participant_id', 'stimulus_id', 'emotion_label', 'response_label', 'accuracy', 'flanker_count', 'eccentricity']
    for col in required_cols:
        assert col in df.columns, f"Missing required column: {col}"
    
    # Check data integrity
    assert len(df) > 0, "Output dataframe is empty"
    assert df['participant_id'].nunique() >= 3, "Should have at least 3 participants"
    assert df['accuracy'].isin([0, 1]).all(), "Accuracy should be binary (0 or 1)"
    assert df['flanker_count'].notna().all(), "flanker_count should not be null"
    assert df['eccentricity'].notna().all(), "eccentricity should not be null"

    # Check that values match the mock data
    assert 'happy' in df['emotion_label'].values
    assert 'sad' in df['emotion_label'].values
    assert 4 in df['flanker_count'].values
    assert 8 in df['flanker_count'].values
    
    print("T030 Integration Test Passed")
