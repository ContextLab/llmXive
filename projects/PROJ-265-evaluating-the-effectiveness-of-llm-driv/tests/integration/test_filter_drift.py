"""
Integration test for T026b: Filter Drifted Pairs.
Verifies that the filtering logic correctly removes drifted/unverifiable pairs
and preserves valid ones, producing the expected output file.
"""

import json
import os
import tempfile
import shutil
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from main_filter_drift import load_jsonl, load_drift_log, filter_pairs, run_filter_drift
from utils.logger import get_logger

logger = get_logger(__name__)

def test_filter_logic():
    """Test the core filtering logic with mock data."""
    
    # Mock simplified data
    mock_simplified = [
        {"id": "pair_1", "stratum": "small", "original": "def a(): return 1", "simplified": "def a(): return 1"},
        {"id": "pair_2", "stratum": "medium", "original": "def b(): return 2", "simplified": "def b(): return 2"},
        {"id": "pair_3", "stratum": "large", "original": "def c(): return 3", "simplified": "def c(): return 3"},
        {"id": "pair_4", "stratum": "small", "original": "def d(): return 4", "simplified": "def d(): return 4"},
    ]

    # Mock drift log
    mock_drift_log = {
        "drifted_pairs": [{"id": "pair_2"}],
        "unverifiable_pairs": [{"id": "pair_3"}]
    }

    valid, excluded = filter_pairs(mock_simplified, mock_drift_log)

    assert len(valid) == 2, f"Expected 2 valid pairs, got {len(valid)}"
    assert len(excluded) == 2, f"Expected 2 excluded pairs, got {len(excluded)}"

    valid_ids = [p["id"] for p in valid]
    assert "pair_1" in valid_ids
    assert "pair_4" in valid_ids

    excluded_reasons = [e["reason"] for e in excluded]
    assert "drift_detected" in excluded_reasons
    assert "equivalence_unverifiable" in excluded_reasons

    logger.info("Core filtering logic test passed.")

def test_end_to_end():
    """Test the full script execution with temporary files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Setup paths
        input_simplified = tmp_path / "simplified_functions.jsonl"
        input_drift = tmp_path / "simplification_log.json"
        output_valid = tmp_path / "valid_pairs.jsonl"
        
        # Create mock input files
        mock_data = [
            {"id": "v1", "stratum": "small", "code": "x=1"},
            {"id": "v2", "stratum": "medium", "code": "y=2"},
            {"id": "v3", "stratum": "large", "code": "z=3"},
            {"id": "v4", "stratum": "small", "code": "w=4"},
        ]
        
        with open(input_simplified, 'w') as f:
            for item in mock_data:
                f.write(json.dumps(item) + '\n')
        
        mock_drift = {
            "drifted_pairs": [{"id": "v2"}],
            "unverifiable_pairs": [{"id": "v3"}]
        }
        with open(input_drift, 'w') as f:
            json.dump(mock_drift, f)

        # Temporarily override global paths for the test
        import main_filter_drift as module
        original_simplified = module.INPUT_SIMPLIFIED_PATH
        original_drift = module.INPUT_DRIFT_LOG_PATH
        original_output = module.OUTPUT_VALID_PAIRS_PATH

        module.INPUT_SIMPLIFIED_PATH = input_simplified
        module.INPUT_DRIFT_LOG_PATH = input_drift
        module.OUTPUT_VALID_PAIRS_PATH = output_valid

        try:
            success = run_filter_drift()
            assert success, "run_filter_drift returned False"
            assert output_valid.exists(), "Output file was not created"

            with open(output_valid, 'r') as f:
                results = [json.loads(line) for line in f if line.strip()]
            
            assert len(results) == 2, f"Expected 2 valid pairs in output, got {len(results)}"
            ids = [r["id"] for r in results]
            assert "v1" in ids and "v4" in ids
            
            logger.info("End-to-end test passed.")
        finally:
            # Restore original paths
            module.INPUT_SIMPLIFIED_PATH = original_simplified
            module.INPUT_DRIFT_LOG_PATH = original_drift
            module.OUTPUT_VALID_PAIRS_PATH = original_output

if __name__ == "__main__":
    test_filter_logic()
    test_end_to_end()
    logger.info("All T026b integration tests passed.")