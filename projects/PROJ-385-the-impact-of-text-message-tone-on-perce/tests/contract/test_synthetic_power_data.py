import os
import zipfile
import csv
import pytest
from pathlib import Path
import sys

# Add code directory to path for imports if running standalone
code_dir = Path(__file__).parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from config import get_processed_data_dir

@pytest.fixture
def zip_path():
    processed_dir = get_processed_data_dir()
    return processed_dir / "synthetic_power_datasets.zip"

def test_zip_exists(zip_path):
    """Verify the zip file was created."""
    assert zip_path.exists(), f"Zip file {zip_path} does not exist"

def test_zip_contents(zip_path):
    """Verify the zip contains the expected CSV files."""
    expected_files = [
        "synthetic_power_equal.csv",
        "synthetic_power_emoji_dominant.csv",
        "synthetic_power_punctuation_dominant.csv"
    ]
    
    with zipfile.ZipFile(zip_path, 'r') as zf:
        names = zf.namelist()
        for expected in expected_files:
            assert expected in names, f"Missing file in zip: {expected}"

def test_csv_structure(zip_path):
    """Verify the structure and content of the generated datasets."""
    required_columns = [
        'participant_id', 'stimulus_id', 'relationship_type',
        'emoji_count', 'punctuation_type', 'length', 'cue_intensity', 'rating'
    ]
    
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for csv_name in zf.namelist():
            with zf.open(csv_name) as f:
                # Decode bytes to string for csv.reader
                content = f.read().decode('utf-8')
                reader = csv.DictReader(content.splitlines())
                headers = reader.fieldnames
                
                # Check all required columns exist
                for col in required_columns:
                    assert col in headers, f"Missing column {col} in {csv_name}"
                
                # Verify data types and ranges
                rows = list(reader)
                assert len(rows) > 0, f"CSV {csv_name} is empty"
                
                # Check N=60 participants logic (60 participants * 20 stimuli * 2 contexts = 2400 rows)
                # We expect 2400 rows per file
                expected_rows = 60 * 20 * 2
                assert len(rows) == expected_rows, f"Expected {expected_rows} rows, got {len(rows)} in {csv_name}"
                
                # Check relationship types
                for row in rows:
                    assert row['relationship_type'] in ['friend', 'acquaintance']
                    assert row['rating'] >= 1.0 and row['rating'] <= 5.0

def test_effect_size_structure(zip_path):
    """
    Verify that the data structure supports the effect size of 0.25.
    We check that cue_intensity is calculated and present.
    """
    with zipfile.ZipFile(zip_path, 'r') as zf:
        # Check the 'equal' scheme file specifically
        csv_name = "synthetic_power_equal.csv"
        with zf.open(csv_name) as f:
            content = f.read().decode('utf-8')
            reader = csv.DictReader(content.splitlines())
            rows = list(reader)
            
            intensities = [float(r['cue_intensity']) for r in rows]
            
            # Ensure variance in cue intensity exists
            assert max(intensities) > min(intensities), "Cue intensity must vary"
            
            # Ensure values are normalized (roughly 0-1)
            assert all(0.0 <= i <= 1.0 for i in intensities), "Cue intensity should be normalized"

def test_random_effects_structure(zip_path):
    """
    Verify the presence of Participant and Stimulus random effects structure.
    Check that every participant sees multiple stimuli and vice versa.
    """
    with zipfile.ZipFile(zip_path, 'r') as zf:
        csv_name = zf.namelist()[0]
        with zf.open(csv_name) as f:
            content = f.read().decode('utf-8')
            reader = csv.DictReader(content.splitlines())
            rows = list(reader)
            
            participants = set(r['participant_id'] for r in rows)
            stimuli = set(r['stimulus_id'] for r in rows)
            
            # Verify 60 participants
            assert len(participants) == 60, f"Expected 60 participants, got {len(participants)}"
            
            # Verify 20 stimuli
            assert len(stimuli) == 20, f"Expected 20 stimuli, got {len(stimuli)}"
            
            # Verify fully within-subjects: each participant sees all stimuli
            # (in this specific design, 20 stimuli * 2 contexts = 40 rows per participant)
            participant_counts = {}
            for r in rows:
                pid = r['participant_id']
                participant_counts[pid] = participant_counts.get(pid, 0) + 1
            
            for pid, count in participant_counts.items():
                assert count == 40, f"Participant {pid} has {count} rows, expected 40 (20 stimuli * 2 contexts)"
