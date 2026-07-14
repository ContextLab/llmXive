"""
Integration tests for the full data ingestion pipeline.

This module verifies that the complete download and preprocessing workflow
functions correctly end-to-end, ensuring data integrity and schema compliance.
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

import pytest
import pandas as pd
import numpy as np

# Import project utilities
import sys
from pathlib import Path as SysPath

# Add project root to path for imports
project_root = SysPath(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "code"))

from config import get_config
from utils.logging_config import get_logger, info, error
from utils.schema_validation import validate_neural_data, validate_text_data
from utils.checksums import compute_sha256, update_state_file, load_state_file

# Mock the ingestion script logic for testing without heavy downloads
# In a real CI environment, this would run the actual 01_data_ingestion.py
# but for this integration test, we simulate the pipeline's output structure
# to verify the *verification logic* and *state management* work correctly.
#
# Note: The actual download logic is in code/01_data_ingestion.py (T012),
# which is not yet implemented. This test validates the *infrastructure*
# around ingestion (logging, validation, checksums) using a controlled mock.

logger = get_logger("test_ingestion_integration")

def _create_mock_neural_data(temp_dir: Path) -> Path:
    """Create a mock neural data file that matches expected schema."""
    neural_dir = temp_dir / "neural" / "processed"
    neural_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = neural_dir / "roi_timecourses.csv"
    
    # Create a small valid dataset: 2 subjects, 3 ROIs, 5 timepoints
    data = {
        "subject_id": ["sub-01", "sub-01", "sub-01", "sub-01", "sub-01",
                       "sub-02", "sub-02", "sub-02", "sub-02", "sub-02"],
        "roi": ["L_Hipp", "R_Hipp", "DLPFC"] * 2 + ["L_Hipp", "R_Hipp", "DLPFC"], # Actually 3*2=6, need 10 rows? Let's fix structure
        # Correct structure: 2 subjects * 3 ROIs * 5 timepoints = 30 rows
    }
    
    rows = []
    for subj in ["sub-01", "sub-02"]:
        for roi in ["L_Hipp", "R_Hipp", "DLPFC"]:
            for t in range(5):
                rows.append({
                    "subject_id": subj,
                    "roi": roi,
                    "timepoint": t,
                    "bold_signal": np.random.normal(1000, 50)
                })
    
    df = pd.DataFrame(rows)
    df.to_csv(file_path, index=False)
    return file_path

def _create_mock_text_data(temp_dir: Path) -> Path:
    """Create a mock text data file matching JSONL schema."""
    text_dir = temp_dir / "text"
    text_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = text_dir / "rocstories_sample.jsonl"
    
    stories = [
        {"story_id": 1, "text": "John went to the park.", "source": "rocstories"},
        {"story_id": 2, "text": "It was a sunny day.", "source": "rocstories"},
        {"story_id": 3, "text": "He saw a dog.", "source": "rocstories"}
    ]
    
    with open(file_path, "w") as f:
        for story in stories:
            f.write(json.dumps(story) + "\n")
    
    return file_path

def _run_mock_pipeline(temp_dir: Path) -> Dict[str, Any]:
    """Simulate the ingestion pipeline steps: create data, validate, checksum."""
    info("Starting mock ingestion pipeline integration test")
    
    # 1. Generate Mock Data
    neural_file = _create_mock_neural_data(temp_dir)
    text_file = _create_mock_text_data(temp_dir)
    
    # 2. Validate Data
    info("Validating neural data schema...")
    is_neural_valid = validate_neural_data(str(neural_file))
    assert is_neural_valid, "Neural data validation failed"
    
    info("Validating text data schema...")
    is_text_valid = validate_text_data(str(text_file))
    assert is_text_valid, "Text data validation failed"
    
    # 3. Compute Checksums and Update State
    info("Computing checksums and updating state file...")
    state_file = temp_dir / "state" / "pipeline_state.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing state or create new
    try:
        state = load_state_file(str(state_file))
    except FileNotFoundError:
        state = {"files": {}, "last_run": None}
    
    # Update state with new files
    update_state_file(str(state_file), "neural_roi_timecourses", str(neural_file))
    update_state_file(str(state_file), "text_rocstories", str(text_file))
    
    # 4. Verify Integrity
    info("Verifying file integrity from state...")
    if os.path.exists(str(state_file)):
        state_after = load_state_file(str(state_file))
        assert "neural_roi_timecourses" in state_after["files"]
        assert "text_rocstories" in state_after["files"]
    
    info("Mock ingestion pipeline completed successfully")
    
    return {
        "neural_file": str(neural_file),
        "text_file": str(text_file),
        "state_file": str(state_file)
    }

@pytest.fixture
def temp_project_dir():
    """Create a temporary directory structure mimicking the project."""
    temp_dir = Path(tempfile.mkdtemp(prefix="nnn_test_"))
    # Create standard directories
    (temp_dir / "data" / "raw").mkdir(parents=True)
    (temp_dir / "data" / "processed").mkdir(parents=True)
    (temp_dir / "data" / "results").mkdir(parents=True)
    (temp_dir / "state").mkdir(parents=True)
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir)

def test_full_ingestion_pipeline_integration(temp_project_dir):
    """
    Integration test: Verify the full download/processing pipeline logic.
    
    Since T012 (actual download) is not yet implemented, this test mocks
    the data generation step to verify the downstream validation, checksum,
    and state management logic works correctly with real data structures.
    
    This ensures that when T012 is implemented, the pipeline infrastructure
    is ready to handle the real data.
    """
    # Change to temp dir to simulate project root
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_project_dir)
        
        # Run the mock pipeline
        results = _run_mock_pipeline(temp_project_dir)
        
        # Assertions
        assert os.path.exists(results["neural_file"]), "Neural file not created"
        assert os.path.exists(results["text_file"]), "Text file not created"
        assert os.path.exists(results["state_file"]), "State file not created"
        
        # Verify content of state file
        state = load_state_file(results["state_file"])
        assert "neural_roi_timecourses" in state["files"]
        assert "text_rocstories" in state["files"]
        
        # Verify checksums are stored
        assert state["files"]["neural_roi_timecourses"]["checksum"] is not None
        assert state["files"]["text_rocstories"]["checksum"] is not None

    finally:
        os.chdir(original_cwd)

def test_schema_validation_with_corrupted_data(temp_project_dir):
    """
    Test that the pipeline correctly identifies and rejects corrupted data.
    """
    # Create a file that violates the schema (e.g., missing required columns)
    bad_file = temp_project_dir / "data" / "processed" / "bad_neural.csv"
    bad_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write CSV missing 'roi' column
    with open(bad_file, "w") as f:
        f.write("subject_id,timepoint,signal\n")
        f.write("sub-01,0,100\n")
    
    # Validation should return False or raise an error depending on implementation
    # Based on T006, validate_neural_data returns a boolean
    is_valid = validate_neural_data(str(bad_file))
    assert not is_valid, "Corrupted data should fail validation"

def test_state_file_persistence(temp_project_dir):
    """
    Verify that state files persist correctly across operations.
    """
    state_path = temp_project_dir / "state" / "test_state.json"
    
    # Initial update
    update_state_file(str(state_path), "key1", "value1")
    state1 = load_state_file(str(state_path))
    assert state1["files"]["key1"]["path"] == "value1"
    
    # Second update (should not overwrite unrelated keys if logic supports it,
    # but here we just verify the file exists and is readable)
    update_state_file(str(state_path), "key2", "value2")
    state2 = load_state_file(str(state_path))
    
    assert "key1" in state2["files"]
    assert "key2" in state2["files"]