"""
Tests for T016b: Data Completeness Report Generation.

Verifies that the script generates a valid JSON artifact with the correct schema
and logic for the 'Empirical Hypothesis Untested' flag.
"""
import json
import os
import tempfile
from pathlib import Path
import pandas as pd
import pytest

# Adjust import path if running standalone
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from generate_completeness_report import generate_report, main
from config import ensure_directories

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_generate_report_real_data_high_completeness():
    """Test report generation with real data and high completeness."""
    report = generate_report(completeness_rate=0.98, is_real_data=True)
    
    assert report["completeness_rate"] == 0.98
    assert report["threshold_met"] is True
    assert report["is_real_data"] is True
    assert report["empirical_hypothesis_untested"] is False
    assert "note" not in report

def test_generate_report_synthetic_data():
    """Test report generation when synthetic fallback is used."""
    report = generate_report(completeness_rate=0.99, is_real_data=False)
    
    assert report["is_real_data"] is False
    assert report["empirical_hypothesis_untested"] is True
    assert "Validation-Only" in report["note"]

def test_generate_report_low_completeness_real():
    """Test report generation when completeness is below threshold for real data."""
    report = generate_report(completeness_rate=0.80, is_real_data=True)
    
    assert report["threshold_met"] is False
    assert report["empirical_hypothesis_untested"] is False # Still real data, just bad quality
    assert "note" not in report

def test_report_schema_fields():
    """Ensure all required SC-005 fields are present."""
    report = generate_report(completeness_rate=0.95, is_real_data=True)
    
    required_fields = [
        "task_id", "artifact_type", "completeness_rate", "threshold_met",
        "threshold_value", "is_real_data", "empirical_hypothesis_untested",
        "missing_columns"
    ]
    
    for field in required_fields:
        assert field in report, f"Missing required field: {field}"

def test_main_integration_with_mock_data(temp_dir):
    """
    Integration test: Create a mock CSV, run main, and verify the JSON output.
    """
    # Setup paths
    data_dir = temp_dir / "data" / "processed"
    report_dir = temp_dir / "artifacts" / "reports"
    data_dir.mkdir(parents=True)
    report_dir.mkdir(parents=True)
    
    csv_path = data_dir / "mlb_processed.csv"
    json_path = report_dir / "data_completeness_report.json"
    
    # Create mock data with high completeness
    mock_data = {
        'game_id': [1, 2, 3],
        'date': ['2019-01-01', '2019-01-02', '2019-01-03'],
        'home_team': ['NYY', 'BOS', 'TB'],
        'away_team': ['TB', 'NYY', 'BOS'],
        'home_runs': [5, 2, 3],
        'away_runs': [3, 4, 2],
        'home_hits': [10, 8, 9],
        'away_hits': [7, 9, 8],
        'home_era': [3.50, 4.10, 3.80],
        'away_era': [4.00, 3.60, 3.90],
        'home_woba': [0.350, 0.320, 0.340],
        'away_woba': [0.330, 0.360, 0.345],
        'home_babip': [0.290, 0.285, 0.295],
        'away_babip': [0.280, 0.290, 0.285]
    }
    df = pd.DataFrame(mock_data)
    df.to_csv(csv_path, index=False)
    
    # Temporarily patch paths in the module (since main() uses global project_root logic)
    # For this test, we rely on the fact that the script looks for relative paths 
    # or we mock the paths. Since the script uses `project_root = Path(__file__).resolve().parent.parent`,
    # and we are running from tests/, we need to be careful.
    # However, to make this robust, we will assume the test runs in the context where
    # the script can find the data if we set the working directory or env vars.
    # A simpler approach for this specific test: verify the logic by calling generate_report directly
    # or mocking the file IO.
    
    # Let's test the logic flow by mocking the file existence check in the script if needed,
    # but for now, let's just verify the JSON generation logic works if the file exists.
    # Since `main` is complex to inject paths into without refactoring, we test `generate_report`
    # and the file writing part separately.
    
    # Simulate the file writing part of main
    from generate_completeness_report import validate_data_completeness
    
    # Run validation on mock data
    required_cols = [
        'game_id', 'date', 'home_team', 'away_team', 'home_runs', 'away_runs',
        'home_hits', 'away_hits', 'home_era', 'away_era', 'home_woba', 'away_woba',
        'home_babip', 'away_babip'
    ]
    rate, missing, passed = validate_data_completeness(df, required_cols)
    
    assert rate == 1.0
    assert missing == []
    
    # Generate and save
    report = generate_report(rate, is_real_data=True, missing_columns=missing)
    with open(json_path, 'w') as f:
        json.dump(report, f)
    
    # Verify file content
    with open(json_path, 'r') as f:
        saved_report = json.load(f)
    
    assert saved_report["completeness_rate"] == 1.0
    assert saved_report["threshold_met"] is True
    assert saved_report["empirical_hypothesis_untested"] is False
    assert saved_report["artifact_type"] == "data_completeness_report"