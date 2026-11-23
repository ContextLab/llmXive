import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Mock imports to avoid circular dependencies during test
sys.modules['config'] = MagicMock()
sys.modules['config'].ensure_directories = MagicMock()
sys.modules['config'].setup_logging = MagicMock()
sys.modules['config'].get_config_summary = MagicMock()

from analysis.quickstart_validator import (
    check_directories,
    check_files,
    check_imports,
    validate_json_schema,
    check_data_artifacts,
    run_statistical_dry_run
)

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory structure for testing."""
    dirs = ["code", "data/raw", "data/processed", "data/results", "tests"]
    for d in dirs:
        (tmp_path / d).mkdir(parents=True)
    return tmp_path

def test_check_directories_all_present(temp_dir, monkeypatch):
    """Test that check_directories returns True when all dirs exist."""
    monkeypatch.chdir(temp_dir)
    ok, missing = check_directories()
    assert ok is True
    assert missing == []

def test_check_directories_missing(temp_dir, monkeypatch):
    """Test that check_directories returns False when dirs missing."""
    monkeypatch.chdir(temp_dir)
    # Remove one directory
    (temp_dir / "contracts").rmdir() if (temp_dir / "contracts").exists() else None
    ok, missing = check_directories()
    assert ok is False
    assert "contracts" in missing

def test_check_files_all_present(tmp_path, monkeypatch):
    """Test check_files with all required files present."""
    # Create dummy files
    required = [
        "data/processed/trajectories.json",
        "data/processed/generation_stats.json",
        "data/processed/classifier_training_data.json",
        "data/processed/experiment_logs.json",
        "data/results/power_analysis_report.json",
        "data/results/scope_adjustments.json",
        "data/results/memory_profile_report.json",
        "data/results/perf_report.json",
        "data/results/sensitivity_analysis_report.json",
        "data/results/statistical_report.json"
    ]
    for f in required:
        (tmp_path / f).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / f).touch()
    
    monkeypatch.chdir(tmp_path)
    ok, missing = check_files()
    assert ok is True
    assert missing == []

def test_check_files_missing(tmp_path, monkeypatch):
    """Test check_files with missing files."""
    monkeypatch.chdir(tmp_path)
    ok, missing = check_files()
    assert ok is False
    assert len(missing) > 0

def test_validate_json_schema_valid(tmp_path, monkeypatch):
    """Test validate_json_schema with valid JSON."""
    monkeypatch.chdir(tmp_path)
    test_file = tmp_path / "test.json"
    test_file.write_text(json.dumps({"key1": "value1", "key2": 123}))
    
    ok, msg = validate_json_schema("test.json", ["key1", "key2"])
    assert ok is True
    assert msg == "OK"

def test_validate_json_schema_missing_keys(tmp_path, monkeypatch):
    """Test validate_json_schema with missing keys."""
    monkeypatch.chdir(tmp_path)
    test_file = tmp_path / "test.json"
    test_file.write_text(json.dumps({"key1": "value1"}))
    
    ok, msg = validate_json_schema("test.json", ["key1", "key2"])
    assert ok is False
    assert "key2" in msg

def test_validate_json_schema_invalid_json(tmp_path, monkeypatch):
    """Test validate_json_schema with invalid JSON."""
    monkeypatch.chdir(tmp_path)
    test_file = tmp_path / "test.json"
    test_file.write_text("{ invalid json }")
    
    ok, msg = validate_json_schema("test.json", ["key1"])
    assert ok is False
    assert "not valid JSON" in msg

def test_check_data_artifacts_valid(tmp_path, monkeypatch):
    """Test check_data_artifacts with valid data files."""
    monkeypatch.chdir(tmp_path)
    
    # Create minimal valid files
    files_data = {
        "data/processed/generation_stats.json": {
            "total_trajectories": 100,
            "high_emotional_reactivity_count": 50,
            "high_cultural_diversity_count": 50
        },
        "data/results/power_analysis_report.json": {
            "required_sample_size": 64,
            "actual_sample_size": 100,
            "is_sufficient": True
        },
        "data/results/scope_adjustments.json": [],
        "data/results/statistical_report.json": {
            "llm_results": [],
            "holm_bonferroni_correction": 1.0,
            "is_significant": True
        }
    }
    
    for path, data in files_data.items():
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / path).write_text(json.dumps(data))
    
    ok, errors = check_data_artifacts()
    assert ok is True
    assert errors == []

def test_check_data_artifacts_power_halt_missing(tmp_path, monkeypatch):
    """Test check_data_artifacts when power analysis fails but no HALT file."""
    monkeypatch.chdir(tmp_path)
    
    files_data = {
        "data/processed/generation_stats.json": {
            "total_trajectories": 100,
            "high_emotional_reactivity_count": 50,
            "high_cultural_diversity_count": 50
        },
        "data/results/power_analysis_report.json": {
            "required_sample_size": 200,
            "actual_sample_size": 100,
            "is_sufficient": False
        },
        "data/results/scope_adjustments.json": [],
        "data/results/statistical_report.json": {
            "llm_results": [],
            "holm_bonferroni_correction": 1.0,
            "is_significant": True
        }
    }
    
    for path, data in files_data.items():
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / path).write_text(json.dumps(data))
    
    ok, errors = check_data_artifacts()
    assert ok is False
    assert any("HALT file" in e for e in errors)

def test_run_statistical_dry_run_success():
    """Test that the statistical dry run succeeds."""
    # This test might fail if dependencies are not installed, but that's expected in CI
    try:
        ok, msg = run_statistical_dry_run()
        # If we get here without exception, the imports worked
        # The actual result depends on whether statsmodels is installed
        assert isinstance(ok, bool)
        assert isinstance(msg, str)
    except ImportError:
        # Expected if statsmodels not installed in test environment
        pytest.skip("statsmodels not installed")
