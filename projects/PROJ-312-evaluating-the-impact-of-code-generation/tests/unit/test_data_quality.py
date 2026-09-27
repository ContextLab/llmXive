import pytest
import json
import os
import tempfile
from pathlib import Path
from code.data_quality import calculate_success_rate, validate_and_check_quality

def test_calculate_success_rate():
    """Test success rate calculation."""
    assert calculate_success_rate(95, 100) == 0.95
    assert calculate_success_rate(0, 100) == 0.0
    assert calculate_success_rate(100, 100) == 1.0
    assert calculate_success_rate(0, 0) == 0.0  # Edge case: division by zero handled

def test_validate_and_check_quality_warning():
    """Test that warning is triggered when rate < threshold."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create mock raw data (100 PRs)
        raw_data = [{"pr_id": f"pr_{i}"} for i in range(100)]
        raw_file = tmpdir_path / "pr_data.json"
        with open(raw_file, 'w') as f:
            json.dump(raw_data, f)
        
        # Create mock processed data (90 PRs - below 95% threshold)
        processed_file = tmpdir_path / "pr_turnaround.csv"
        with open(processed_file, 'w') as f:
            f.write("pr_id,turnaround_hours,classification\n")
            for i in range(90):
                f.write(f"pr_{i},10.5,ai\n")
        
        result = validate_and_check_quality(
            processed_file=str(processed_file),
            raw_file=str(raw_file),
            output_dir=str(tmpdir_path),
            threshold=0.95
        )
        
        assert result["total_prs"] == 100
        assert result["processed_prs"] == 90
        assert result["success_rate"] == 0.90
        assert result["status"] == "warning"
        
        # Verify warning log was created
        assert (tmpdir_path / "data_quality_warning.log").exists()
        assert (tmpdir_path / "quality_status.json").exists()

def test_validate_and_check_quality_ok():
    """Test that status is 'ok' when rate >= threshold."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create mock raw data (100 PRs)
        raw_data = [{"pr_id": f"pr_{i}"} for i in range(100)]
        raw_file = tmpdir_path / "pr_data.json"
        with open(raw_file, 'w') as f:
            json.dump(raw_data, f)
        
        # Create mock processed data (96 PRs - above 95% threshold)
        processed_file = tmpdir_path / "pr_turnaround.csv"
        with open(processed_file, 'w') as f:
            f.write("pr_id,turnaround_hours,classification\n")
            for i in range(96):
                f.write(f"pr_{i},10.5,ai\n")
        
        result = validate_and_check_quality(
            processed_file=str(processed_file),
            raw_file=str(raw_file),
            output_dir=str(tmpdir_path),
            threshold=0.95
        )
        
        assert result["total_prs"] == 100
        assert result["processed_prs"] == 96
        assert result["success_rate"] == 0.96
        assert result["status"] == "ok"
        
        # Verify warning log was NOT created
        assert not (tmpdir_path / "data_quality_warning.log").exists()
        assert (tmpdir_path / "quality_status.json").exists()