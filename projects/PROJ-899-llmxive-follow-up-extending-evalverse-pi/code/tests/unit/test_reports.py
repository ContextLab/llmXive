"""
Unit tests for report generation module.
"""
import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.reports.generate import (
    generate_profiling_report,
    generate_viability_report,
    generate_sensitivity_report,
    load_profiling_data,
    load_timing_profile,
    load_feasibility_gate_result,
    load_dimension_viability,
    load_sensitivity_matrix
)

@pytest.fixture
def temp_data_dirs():
    """Create temporary directories for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create directory structure
        data_root = Path(tmpdir) / "data"
        data_root.mkdir()
        (data_root / "processed").mkdir()
        (data_root / "results").mkdir()
        reports_root = Path(tmpdir) / "reports"
        reports_root.mkdir()
        state_root = Path(tmpdir) / "state"
        state_root.mkdir()

        # Create mock data files
        profiling_data = [
            {"clip_id": "clip_001", "cpu_time_sec": 1.5, "peak_memory_mb": 512, "status": "success"},
            {"clip_id": "clip_002", "cpu_time_sec": 2.0, "peak_memory_mb": 600, "status": "success"},
            {"clip_id": "clip_003", "cpu_time_sec": 0.0, "peak_memory_mb": 0, "status": "failed"}
        ]
        with open(data_root / "profiling_logs.json", "w") as f:
            json.dump(profiling_data, f)

        timing_data = [
            {"mean_time_per_clip_sec": 1.8, "projected_total_hours": 5.0}
        ]
        with open(data_root / "timing_profile.csv", "w") as f:
            f.write("mean_time_per_clip_sec,projected_total_hours\n")
            for row in timing_data:
                f.write(f"{row['mean_time_per_clip_sec']},{row['projected_total_hours']}\n")

        feasibility_data = {
            "status": "pass",
            "memory_limit_gb": 7,
            "time_limit_hours": 6,
            "within_memory_limit": True,
            "within_time_limit": True
        }
        with open(state_root / "feasibility_gate.json", "w") as f:
            json.dump(feasibility_data, f)

        viability_data = [
            {"dimension": "dimension_1", "pearson_r": 0.90, "lower_ci": 0.85, "upper_ci": 0.95, "status": "feature-sufficient", "adjusted_p": 0.01},
            {"dimension": "dimension_2", "pearson_r": 0.60, "lower_ci": 0.50, "upper_ci": 0.70, "status": "VLM-required", "adjusted_p": 0.05}
        ]
        with open(data_root / "dimension_viability.csv", "w") as f:
            f.write("dimension,pearson_r,lower_ci,upper_ci,status,adjusted_p\n")
            for row in viability_data:
                f.write(f"{row['dimension']},{row['pearson_r']},{row['lower_ci']},{row['upper_ci']},{row['status']},{row['adjusted_p']}\n")

        sensitivity_data = [
            {"dimension": "dimension_1", "status_0.80": "feature-sufficient", "status_0.85": "feature-sufficient", "status_0.90": "VLM-required"},
            {"dimension": "dimension_2", "status_0.80": "VLM-required", "status_0.85": "VLM-required", "status_0.90": "VLM-required"}
        ]
        with open(data_root / "sensitivity_matrix_full.csv", "w") as f:
            f.write("dimension,status_0.80,status_0.85,status_0.90\n")
            for row in sensitivity_data:
                f.write(f"{row['dimension']},{row['status_0.80']},{row['status_0.85']},{row['status_0.90']}\n")

        yield {
            "data_root": str(data_root),
            "reports_root": str(reports_root),
            "state_root": str(state_root)
        }

@patch('src.reports.generate.get_data_root')
@patch('src.reports.generate.get_reports_root')
@patch('src.reports.generate.get_project_root')
def test_generate_profiling_report(mock_project_root, mock_reports_root, mock_data_root, temp_data_dirs):
    """Test profiling report generation."""
    mock_data_root.return_value = temp_data_dirs["data_root"]
    mock_reports_root.return_value = temp_data_dirs["reports_root"]
    mock_project_root.return_value = str(Path(temp_data_dirs["state_root"]).parent)

    report = generate_profiling_report()

    assert report is not None
    assert report["report_type"] == "profiling"
    assert report["summary"]["total_clips_processed"] == 3
    assert report["summary"]["successful_clips"] == 2
    assert "timing_metrics" in report
    assert "memory_metrics" in report
    assert "feasibility_status" in report

    # Check file was written
    output_path = Path(temp_data_dirs["reports_root"]) / "profiling_report.json"
    assert output_path.exists()

@patch('src.reports.generate.get_data_root')
@patch('src.reports.generate.get_reports_root')
def test_generate_viability_report(mock_reports_root, mock_data_root, temp_data_dirs):
    """Test viability report generation."""
    mock_data_root.return_value = temp_data_dirs["data_root"]
    mock_reports_root.return_value = temp_data_dirs["reports_root"]

    report = generate_viability_report()

    assert report is not None
    assert report["report_type"] == "viability"
    assert report["total_dimensions"] == 2
    assert report["feature_sufficient_count"] == 1
    assert report["vlm_required_count"] == 1

    # Check file was written
    output_path = Path(temp_data_dirs["reports_root"]) / "viability_report.json"
    assert output_path.exists()

@patch('src.reports.generate.get_data_root')
@patch('src.reports.generate.get_reports_root')
def test_generate_sensitivity_report(mock_reports_root, mock_data_root, temp_data_dirs):
    """Test sensitivity report generation."""
    mock_data_root.return_value = temp_data_dirs["data_root"]
    mock_reports_root.return_value = temp_data_dirs["reports_root"]

    report = generate_sensitivity_report()

    assert report is not None
    assert report["report_type"] == "sensitivity"
    assert len(report["thresholds_tested"]) == 3
    assert report["dimensions_analyzed"] == 2

    # Check file was written
    output_path = Path(temp_data_dirs["reports_root"]) / "sensitivity_report.json"
    assert output_path.exists()

@patch('src.reports.generate.get_data_root')
def test_load_profiling_data_missing_file(mock_data_root, temp_data_dirs):
    """Test loading profiling data when file is missing."""
    mock_data_root.return_value = str(Path(temp_data_dirs["data_root"]) / "nonexistent")

    with pytest.raises(FileNotFoundError):
        load_profiling_data()

@patch('src.reports.generate.get_data_root')
def test_load_timing_profile_missing_file(mock_data_root, temp_data_dirs):
    """Test loading timing profile when file is missing."""
    mock_data_root.return_value = str(Path(temp_data_dirs["data_root"]) / "nonexistent")

    with pytest.raises(FileNotFoundError):
        load_timing_profile()

@patch('src.reports.generate.get_project_root')
def test_load_feasibility_gate_result_missing_file(mock_project_root, temp_data_dirs):
    """Test loading feasibility gate result when file is missing."""
    mock_project_root.return_value = str(Path(temp_data_dirs["state_root"]).parent / "nonexistent")

    with pytest.raises(FileNotFoundError):
        load_feasibility_gate_result()
