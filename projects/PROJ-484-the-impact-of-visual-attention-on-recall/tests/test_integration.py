"""
Integration tests for the full preprocessing pipeline (US1).
Tests T010: Full pipeline execution on sample data.
"""
import os
import sys
import tempfile
import shutil
import json
import pandas as pd
import pytest
from pathlib import Path

# Add parent directory to path to import code modules
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from preprocess import (
    load_manifest,
    validate_variables,
    extract_geometry_metadata,
    calculate_ivt_threshold,
    extract_fixations_ivt,
    map_stimulus_valence,
    merge_stai_scores,
    filter_trials,
    generate_analysis_csv,
    load_schema,
    validate_against_schema,
    main as preprocess_main
)
from config import get_config

# --- Mock Data Generators for Integration Test ---
# Since we cannot rely on the real download (T011) having run successfully in this isolated test
# without potentially failing the whole suite if the network is down, we create a minimal
# valid "sample" dataset structure in a temporary directory that mimics the expected real data format.
# This allows testing the *pipeline logic* (T012-T017) without needing the full external dataset.

def create_sample_data_structure(temp_dir: Path):
    """Creates a minimal valid directory structure and CSVs mimicking the real dataset."""
    raw_dir = temp_dir / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Create a minimal manifest
    manifest_data = {
        "participants": [
            {
                "id": "P001",
                "screen_width_px": 1920,
                "screen_height_px": 1080,
                "viewing_distance_mm": 600,
                "sampling_rate_hz": 1000,
                "trial_count": 5,
                "has_eyetracking": True,
                "has_valence": True,
                "has_recall": True,
                "has_stai": True
            }
        ],
        "stimuli": [
            {"id": "IAPS_1234", "valence": 8.5, "arousal": 5.2, "dominance": 6.0},
            {"id": "IAPS_5678", "valence": 2.1, "arousal": 7.8, "dominance": 3.0},
            {"id": "IAPS_9999", "valence": 5.0, "arousal": 3.0, "dominance": 5.0}
        ]
    }
    with open(raw_dir / "manifest.json", "w") as f:
        json.dump(manifest_data, f)

    # 2. Create participant data file (simulating eye-tracking + trial data)
    # Format: participant_id, trial_id, stimulus_id, timestamp_ms, x, y, valence, recall, stai_score
    # We include valid data and some "noise" to test filtering
    data_rows = [
        # P001, Trial 1, IAPS_1234 (Positive)
        ["P001", "T001", "IAPS_1234", 0, 960, 540, 8.5, 1, 30],
        ["P001", "T001", "IAPS_1234", 10, 960, 540, 8.5, 1, 30],
        ["P001", "T001", "IAPS_1234", 20, 960, 540, 8.5, 1, 30],
        ["P001", "T001", "IAPS_1234", 30, 960, 540, 8.5, 1, 30],
        ["P001", "T001", "IAPS_1234", 40, 960, 540, 8.5, 1, 30],
        ["P001", "T001", "IAPS_1234", 50, 960, 540, 8.5, 1, 30],
        ["P001", "T001", "IAPS_1234", 60, 960, 540, 8.5, 1, 30],
        ["P001", "T001", "IAPS_1234", 70, 960, 540, 8.5, 1, 30],
        ["P001", "T001", "IAPS_1234", 80, 960, 540, 8.5, 1, 30],
        ["P001", "T001", "IAPS_1234", 90, 960, 540, 8.5, 1, 30],
        ["P001", "T001", "IAPS_1234", 100, 960, 540, 8.5, 1, 30], # 100ms duration (10 frames * 10ms) - borderline
        
        # P001, Trial 2, IAPS_5678 (Negative) - Valid fixation
        ["P001", "T002", "IAPS_5678", 0, 960, 540, 2.1, 0, 30],
        ["P001", "T002", "IAPS_5678", 10, 961, 541, 2.1, 0, 30],
        ["P001", "T002", "IAPS_5678", 20, 959, 539, 2.1, 0, 30],
        ["P001", "T002", "IAPS_5678", 30, 960, 540, 2.1, 0, 30],
        ["P001", "T002", "IAPS_5678", 40, 960, 540, 2.1, 0, 30],
        ["P001", "T002", "IAPS_5678", 50, 960, 540, 2.1, 0, 30],
        ["P001", "T002", "IAPS_5678", 60, 960, 540, 2.1, 0, 30],
        ["P001", "T002", "IAPS_5678", 70, 960, 540, 2.1, 0, 30],
        ["P001", "T002", "IAPS_5678", 80, 960, 540, 2.1, 0, 30],
        ["P001", "T002", "IAPS_5678", 90, 960, 540, 2.1, 0, 30],
        ["P001", "T002", "IAPS_5678", 100, 960, 540, 2.1, 0, 30],
        ["P001", "T002", "IAPS_5678", 110, 960, 540, 2.1, 0, 30],
        ["P001", "T002", "IAPS_5678", 120, 960, 540, 2.1, 0, 30], # 120ms duration - valid fixation

        # P001, Trial 3, IAPS_9999 (Neutral) - Missing Recall (should be filtered or NaN handled)
        ["P001", "T003", "IAPS_9999", 0, 960, 540, 5.0, None, 30],
        ["P001", "T003", "IAPS_9999", 10, 960, 540, 5.0, None, 30],
        ["P001", "T003", "IAPS_9999", 20, 960, 540, 5.0, None, 30],
        ["P001", "T003", "IAPS_9999", 30, 960, 540, 5.0, None, 30],
        ["P001", "T003", "IAPS_9999", 40, 960, 540, 5.0, None, 30],
        ["P001", "T003", "IAPS_9999", 50, 960, 540, 5.0, None, 30],
        ["P001", "T003", "IAPS_9999", 60, 960, 540, 5.0, None, 30],
        ["P001", "T003", "IAPS_9999", 70, 960, 540, 5.0, None, 30],
        ["P001", "T003", "IAPS_9999", 80, 960, 540, 5.0, None, 30],
        ["P001", "T003", "IAPS_9999", 90, 960, 540, 5.0, None, 30],
        ["P001", "T003", "IAPS_9999", 100, 960, 540, 5.0, None, 30],
        ["P001", "T003", "IAPS_9999", 110, 960, 540, 5.0, None, 30],
        ["P001", "T003", "IAPS_9999", 120, 960, 540, 5.0, None, 30],

        # P001, Trial 4 - Invalid Stimulus ID (should be rejected by map_stimulus_valence)
        ["P001", "T004", "IAPS_INVALID", 0, 960, 540, 999, 1, 30], # 999 is not in manifest
        ["P001", "T004", "IAPS_INVALID", 10, 960, 540, 999, 1, 30],
        ["P001", "T004", "IAPS_INVALID", 20, 960, 540, 999, 1, 30],
        ["P001", "T004", "IAPS_INVALID", 30, 960, 540, 999, 1, 30],
        ["P001", "T004", "IAPS_INVALID", 40, 960, 540, 999, 1, 30],
        ["P001", "T004", "IAPS_INVALID", 50, 960, 540, 999, 1, 30],
        ["P001", "T004", "IAPS_INVALID", 60, 960, 540, 999, 1, 30],
        ["P001", "T004", "IAPS_INVALID", 70, 960, 540, 999, 1, 30],
        ["P001", "T004", "IAPS_INVALID", 80, 960, 540, 999, 1, 30],
        ["P001", "T004", "IAPS_INVALID", 90, 960, 540, 999, 1, 30],
        ["P001", "T004", "IAPS_INVALID", 100, 960, 540, 999, 1, 30],
        ["P001", "T004", "IAPS_INVALID", 110, 960, 540, 999, 1, 30],
        ["P001", "T004", "IAPS_INVALID", 120, 960, 540, 999, 1, 30],
    ]
    
    df = pd.DataFrame(data_rows, columns=[
        "participant_id", "trial_id", "stimulus_id", "timestamp_ms", 
        "x", "y", "valence", "recall", "stai_score"
    ])
    
    # Save as CSV in raw dir
    df.to_csv(raw_dir / "raw_data.csv", index=False)
    
    # 3. Create a schema file for validation
    schema = {
        "fields": [
            {"name": "participant_id", "type": "string"},
            {"name": "trial_id", "type": "string"},
            {"name": "stimulus_id", "type": "string"},
            {"name": "fixation_duration_ms", "type": "float"},
            {"name": "valence", "type": "float"},
            {"name": "recall", "type": "integer"},
            {"name": "stai_score", "type": "integer"},
            {"name": "screen_width_px", "type": "integer"},
            {"name": "screen_height_px", "type": "integer"},
            {"name": "viewing_distance_mm", "type": "float"},
            {"name": "sampling_rate_hz", "type": "integer"},
            {"name": "ivt_threshold_deg_per_sec", "type": "float"}
        ],
        "required": ["participant_id", "trial_id", "stimulus_id", "fixation_duration_ms", "valence", "recall"]
    }
    with open(raw_dir / "schema.yaml", "w") as f:
        json.dump(schema, f) # Using JSON for simplicity in test, though spec says YAML. Preprocess expects YAML but we can adapt or just test the logic.
        # Actually, let's write valid YAML to be safe
        import yaml
        with open(raw_dir / "schema.yaml", "w") as f:
            yaml.dump(schema, f)

    return temp_dir

def test_full_preprocessing_pipeline():
    """
    Integration test for T010.
    Runs the full pipeline on a sample dataset and asserts:
    1. Output CSV exists.
    2. Fixation durations are non-null and >= 100ms (or filtered correctly).
    3. Valence labels are valid (from manifest).
    4. Invalid stimuli are removed.
    5. Trials with missing recall are handled (filtered or NaN).
    """
    temp_root = Path(tempfile.mkdtemp())
    try:
        # 1. Setup sample data
        create_sample_data_structure(temp_root)
        raw_dir = temp_root / "data" / "raw"
        processed_dir = temp_root / "data" / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # 2. Run the pipeline components manually to ensure we test the logic
        # Load manifest
        manifest = load_manifest(raw_dir / "manifest.json")
        
        # Validate variables
        validate_variables(raw_dir / "raw_data.csv", manifest)
        
        # Extract geometry
        geometry = extract_geometry_metadata(manifest)
        assert geometry["screen_width_px"] == 1920
        
        # Calculate IVT threshold
        ivt_threshold = calculate_ivt_threshold(geometry)
        assert ivt_threshold > 0
        
        # Extract fixations (This is the core logic)
        # Note: The actual implementation of extract_fixations_ivt in preprocess.py
        # might expect a specific file path or handle the CSV reading internally.
        # We assume the main function or a wrapper handles the flow.
        # For this test, we will call the main function with arguments.
        
        output_csv_path = processed_dir / "analysis.csv"
        
        # Run the main preprocessing script logic via the main function
        # We need to mock sys.argv or call the logic directly.
        # Let's call the logic directly to avoid sys.argv parsing issues in test.
        
        # 1. Load raw data
        import pandas as pd
        raw_df = pd.read_csv(raw_dir / "raw_data.csv")
        
        # 2. Validate
        # (Already done by validate_variables above, but we need the data for next steps)
        
        # 3. Filter trials with missing recall? The spec says "Exclude trials with missing data".
        # Let's assume the pipeline filters out rows where recall is NaN before final output.
        
        # 4. Map Stimulus
        # We need to ensure unmapped IDs raise an error or are filtered.
        # The task says "Reject unmapped IDs".
        
        # 5. Run the full pipeline logic as if called from CLI
        # We will construct the arguments and call main
        sys.argv = [
            "preprocess.py",
            "--input", str(raw_dir / "raw_data.csv"),
            "--manifest", str(raw_dir / "manifest.json"),
            "--output", str(output_csv_path),
            "--schema", str(raw_dir / "schema.yaml"),
            "--min-fixation-duration", "100"
        ]
        
        # We need to capture logs to ensure no errors
        try:
            preprocess_main()
        except SystemExit as e:
            if e.code != 0:
                pytest.fail(f"Preprocessing pipeline exited with code {e.code}")
        
        # 6. Assertions
        assert output_csv_path.exists(), "Output CSV was not generated."
        
        result_df = pd.read_csv(output_csv_path)
        
        # Assert non-null fixation durations
        assert result_df["fixation_duration_ms"].notnull().all(), "Found null fixation durations in output."
        
        # Assert all fixation durations are >= 100ms (as per filter logic)
        # Note: The filter logic in T013 says "Enforce a minimum fixation window with a default of 100ms".
        # If the implementation filters OUT fixations < 100ms, then all remaining should be >= 100.
        # If it filters OUT trials with < 100ms total fixation, that's different.
        # Assuming it filters individual fixations.
        # Let's check if any are < 100.
        # Note: Our sample data had a 100ms fixation (10 frames * 10ms).
        # If the threshold is inclusive, 100 is okay. If exclusive, it might be dropped.
        # Let's assert that all are >= 100 (or handle the edge case if the code is strict >).
        # Given "minimum fixation window with a default of 100ms", usually means >= 100ms.
        # We will assert >= 100.
        assert (result_df["fixation_duration_ms"] >= 100).all(), f"Found fixation durations < 100ms: {result_df[result_df['fixation_duration_ms'] < 100]}"
        
        # Assert valid valence labels
        # Valid valences in manifest: 8.5, 2.1, 5.0
        valid_valences = [8.5, 2.1, 5.0]
        for val in result_df["valence"]:
            assert val in valid_valences, f"Found invalid valence {val} in output."
        
        # Assert that invalid stimulus (IAPS_INVALID) is NOT in the output
        # The manifest did not have IAPS_INVALID, so it should have been rejected.
        assert "IAPS_INVALID" not in result_df["stimulus_id"].values, "Invalid stimulus ID found in output."
        
        # Assert that trials with missing recall (T003) are handled.
        # The spec says "Exclude trials with missing data".
        # So T003 should be gone.
        # Check if any row has recall == NaN
        if "recall" in result_df.columns:
            assert result_df["recall"].notnull().all(), "Found missing recall values in output."
        
        print(f"Integration test passed. Output file: {output_csv_path}")
        print(f"Rows in output: {len(result_df)}")
        print(f"Columns: {list(result_df.columns)}")
        
    finally:
        # Cleanup
        shutil.rmtree(temp_root)

if __name__ == "__main__":
    test_full_preprocessing_pipeline()
    print("All integration tests passed.")