import pytest
import json
import pandas as pd
from pathlib import Path
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock, mock_open

import code.data_loader as data_loader_module
import code.config as config_module


@pytest.fixture
def temp_data_dir():
    temp_dir = tempfile.mkdtemp()
    os.makedirs(temp_dir, exist_ok=True)
    with patch.object(config_module, 'get_data_dir', return_value=temp_dir):
        with patch.object(config_module, 'get_sample_limit', return_value=100):
            yield temp_dir
    shutil.rmtree(temp_dir)


def test_filter_pairable_samples_creates_log(temp_data_dir):
    # Setup: Create mock coverage_metrics.csv
    coverage_path = Path(temp_data_dir) / "coverage_metrics.csv"
    data = {
        "project_id": ["p1", "p1", "p2", "p3", "p4"],
        "bug_id": ["b1", "b2", "b1", "b1", "b5"],
        "test_type": ["manual", "generated", "manual", "generated", "generated"],
        "coverage_percentage": [40.0, 45.0, 50.0, 55.0, None]
    }
    df = pd.DataFrame(data)
    df.to_csv(coverage_path, index=False)

    # Setup: Create mock changed_lines.json
    changed_lines_path = Path(temp_data_dir) / "changed_lines.json"
    changed_lines_data = {
        "p1": {"b1": [10, 20], "b2": [30]},
        "p2": {"b1": [40]}
    }
    with open(changed_lines_path, 'w') as f:
        json.dump(changed_lines_data, f)

    # Execute
    result = data_loader_module.filter_pairable_samples()

    # Verify
    assert result["total_samples"] == 5
    # p1/b1 (manual) -> pairable
    # p1/b2 (generated) -> pairable (has changed lines)
    # p2/b1 (manual) -> pairable
    # p3/b1 (generated) -> excluded (no changed lines for p3)
    # p4/b5 (generated) -> excluded (no changed lines for p4, also null coverage)
    # Wait, p4/b5 has null coverage, so excluded.
    # p3/b1 has changed lines? No, p3 is not in changed_lines_data. So excluded.
    # Total excluded: 2 (p3/b1, p4/b5)
    # Total pairable: 3 (p1/b1, p1/b2, p2/b1)

    assert result["excluded_count"] == 2
    assert result["pairable_count"] == 3
    assert result["exclusion_rate"] == 0.4

    # Verify file creation
    exclusion_log_path = Path(temp_data_dir) / "exclusion_log.json"
    assert exclusion_log_path.exists()
    with open(exclusion_log_path, 'r') as f:
        log_data = json.load(f)
    assert log_data["total_samples"] == 5
    assert log_data["excluded_count"] == 2
    assert log_data["pairable_count"] == 3


def test_filter_pairable_samples_missing_coverage_file(temp_data_dir):
    # Setup: Do not create coverage_metrics.csv
    changed_lines_path = Path(temp_data_dir) / "changed_lines.json"
    with open(changed_lines_path, 'w') as f:
        json.dump({}, f)

    # Execute & Verify
    with pytest.raises(FileNotFoundError):
        data_loader_module.filter_pairable_samples()


def test_filter_pairable_samples_missing_changed_lines_file(temp_data_dir):
    # Setup: Create coverage_metrics.csv but no changed_lines.json
    coverage_path = Path(temp_data_dir) / "coverage_metrics.csv"
    pd.DataFrame({"project_id": ["p1"], "bug_id": ["b1"], "test_type": ["manual"], "coverage_percentage": [40.0]}).to_csv(coverage_path, index=False)

    # Execute & Verify
    with pytest.raises(FileNotFoundError):
        data_loader_module.filter_pairable_samples()


def test_log_fallback_prompt_usage(temp_data_dir):
    # Setup: Mock the metrics file path
    metrics_path = Path(temp_data_dir) / "metrics.json"
    
    # Execute
    data_loader_module.log_fallback_prompt_usage("test_bug_desc", "test_prompt")

    # Verify
    assert metrics_path.exists()
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    assert "ambiguous_prompt_count" in metrics
    assert metrics["ambiguous_prompt_count"] > 0
    assert "fallback_prompts" in metrics
    assert len(metrics["fallback_prompts"]) > 0
    last_entry = metrics["fallback_prompts"][-1]
    assert last_entry["bug_description"] == "test_bug_desc"
    assert last_entry["prompt_used"] == "test_prompt"


def test_log_fallback_prompt_usage_multiple(temp_data_dir):
    # Setup
    metrics_path = Path(temp_data_dir) / "metrics.json"
    
    # Execute multiple times
    data_loader_module.log_fallback_prompt_usage("desc1", "prompt1")
    data_loader_module.log_fallback_prompt_usage("desc2", "prompt2")
    data_loader_module.log_fallback_prompt_usage("desc3", "prompt3")

    # Verify
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    assert metrics["ambiguous_prompt_count"] == 3
    assert len(metrics["fallback_prompts"]) == 3


def test_log_fallback_prompt_usage_file_not_found_handling(temp_data_dir):
    # Setup: Ensure the directory exists but we mock a permission error scenario
    # by temporarily changing the path to a non-writable location if possible,
    # but for this test we just verify the function handles the file creation gracefully.
    # The function should create the file if it doesn't exist.
    
    # Execute
    data_loader_module.log_fallback_prompt_usage("test_desc", "test_prompt")
    
    # Verify file was created
    metrics_path = Path(temp_data_dir) / "metrics.json"
    assert metrics_path.exists()


def test_load_state_creates_default(temp_data_dir):
    # Setup: No state file exists
    state_path = Path(temp_data_dir) / "state.yaml"
    
    # Execute: load_state should create a default state if not found
    state = data_loader_module.load_state(state_path)
    
    # Verify
    assert state is not None
    assert "runs" in state or "artifact_hashes" in state or state == {}
    # The function should return a dict representing the state
    assert isinstance(state, dict)


def test_save_state_writes_yaml(temp_data_dir):
    # Setup
    state_path = Path(temp_data_dir) / "state.yaml"
    test_state = {"key": "value", "count": 1}
    
    # Execute
    data_loader_module.save_state(state_path, test_state)
    
    # Verify
    assert state_path.exists()
    with open(state_path, 'r') as f:
        content = f.read()
    assert "key: value" in content or "count: 1" in content


def test_compute_sha256_on_string():
    # Execute
    result = data_loader_module.compute_sha256("test string")
    
    # Verify
    assert isinstance(result, str)
    assert len(result) == 64  # SHA256 hex length
    # Verify it's actually a hash
    expected = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08" # SHA256("test string")
    assert result == expected


def test_compute_sha256_on_bytes():
    # Execute
    result = data_loader_module.compute_sha256(b"test bytes")
    
    # Verify
    assert isinstance(result, str)
    assert len(result) == 64


def test_verify_data_integrity_false(temp_data_dir):
    # Setup: Create a state file with a checksum, but no matching data
    state_path = Path(temp_data_dir) / "state.yaml"
    test_state = {"artifact_hashes": {"data_loader": "wrong_hash_123"}}
    data_loader_module.save_state(state_path, test_state)
    
    # Mock the data file to return a different hash
    data_path = Path(temp_data_dir) / "data.json"
    with open(data_path, 'w') as f:
        json.dump({"data": "test"}, f)
    
    # We need to patch the load function to return the wrong hash or check logic
    # Since verify_data_integrity reads the actual file, let's create a scenario
    # where the stored hash doesn't match the computed one.
    
    # Actually, let's just test the logic path where it returns False
    # by ensuring the stored hash is different from what would be computed.
    # Since we can't easily predict the hash of the file we just wrote without importing hashlib again,
    # we rely on the fact that "wrong_hash_123" is unlikely to be the real hash.
    
    # Execute
    result = data_loader_module.verify_data_integrity(state_path, str(data_path))
    
    # Verify
    assert result is False


def test_verify_data_integrity_true(temp_data_dir):
    # Setup: Create a data file
    data_path = Path(temp_data_dir) / "data.json"
    with open(data_path, 'w') as f:
        json.dump({"data": "test"}, f)
    
    # Compute the real hash
    real_hash = data_loader_module.compute_sha256(json.dumps({"data": "test"}).encode('utf-8'))
    
    # Create state with correct hash
    state_path = Path(temp_data_dir) / "state.yaml"
    test_state = {"artifact_hashes": {"data_loader": real_hash}}
    data_loader_module.save_state(state_path, test_state)
    
    # Execute
    result = data_loader_module.verify_data_integrity(state_path, str(data_path))
    
    # Verify
    assert result is True