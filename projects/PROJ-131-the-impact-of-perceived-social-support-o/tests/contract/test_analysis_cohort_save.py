"""
Contract tests for T016: Saving the validated analysis cohort.

These tests verify that:
1. The save_cohort module correctly reads the validation report.
2. It raises appropriate errors if validation failed.
3. It correctly copies the intermediate cohort to the final location.
4. The output file matches the expected schema.
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import pytest

# Import the function under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from analysis.save_cohort import save_validated_cohort


@pytest.fixture
def temp_dirs():
    """Create temporary directories for test artifacts."""
    base = tempfile.mkdtemp()
    data_dir = Path(base) / "data" / "results"
    data_dir.mkdir(parents=True)
    yield base, data_dir
    shutil.rmtree(base)


def test_save_cohort_success(temp_dirs):
    """Test successful saving when validation passes."""
    base, data_dir = temp_dirs
    
    # Create intermediate cohort
    cohort_data = {
        'age': [25, 30, 35],
        'gender': ['M', 'F', 'M'],
        'social_support': [5.0, 4.5, 6.0],
        'harassment_exposure': [1, 0, 1],
        'harassment_severity': [2.0, 0.0, 5.0]
    }
    intermediate_path = data_dir / "intermediate_cohort.csv"
    pd.DataFrame(cohort_data).to_csv(intermediate_path, index=False)
    
    # Create passing validation report
    validation_report = {
        "is_valid": True,
        "checks": {
            "harassment_variance": {"passed": True, "value": 0.45},
            "social_support_variance": {"passed": True, "value": 1.2},
            "vif": {"passed": True, "max_vif": 2.5}
        },
        "errors": []
    }
    validation_path = data_dir / "validation_report.json"
    with open(validation_path, 'w') as f:
        json.dump(validation_report, f)
    
    # Run save function
    output_path = data_dir / "analysis_cohort.csv"
    result = save_validated_cohort(
        intermediate_path=str(intermediate_path),
        validation_report_path=str(validation_path),
        output_path=str(output_path)
    )
    
    assert result is True
    assert output_path.exists()
    
    # Verify content matches
    saved_df = pd.read_csv(output_path)
    original_df = pd.read_csv(intermediate_path)
    pd.testing.assert_frame_equal(saved_df, original_df)


def test_save_cohort_validation_failed(temp_dirs):
    """Test that saving fails when validation report indicates failure."""
    base, data_dir = temp_dirs
    
    # Create intermediate cohort
    cohort_data = {
        'age': [25, 30, 35],
        'social_support': [5.0, 4.5, 6.0],
        'harassment_exposure': [1, 0, 1]
    }
    intermediate_path = data_dir / "intermediate_cohort.csv"
    pd.DataFrame(cohort_data).to_csv(intermediate_path, index=False)
    
    # Create failing validation report
    validation_report = {
        "is_valid": False,
        "checks": {
            "harassment_variance": {"passed": False, "value": 0.0}
        },
        "errors": ["Harassment exposure variance too low (SD < 0.2)"]
    }
    validation_path = data_dir / "validation_report.json"
    with open(validation_path, 'w') as f:
        json.dump(validation_report, f)
    
    # Attempt to save - should raise RuntimeError
    output_path = data_dir / "analysis_cohort.csv"
    with pytest.raises(RuntimeError) as exc_info:
        save_validated_cohort(
            intermediate_path=str(intermediate_path),
            validation_report_path=str(validation_path),
            output_path=str(output_path)
        )
    
    assert "E-VALIDATION-001" in str(exc_info.value)
    assert not output_path.exists()


def test_save_cohort_missing_validation_report(temp_dirs):
    """Test that saving fails if validation report is missing."""
    base, data_dir = temp_dirs
    
    # Create intermediate cohort
    cohort_data = {'age': [25, 30], 'social_support': [5.0, 6.0]}
    intermediate_path = data_dir / "intermediate_cohort.csv"
    pd.DataFrame(cohort_data).to_csv(intermediate_path, index=False)
    
    # No validation report created
    output_path = data_dir / "analysis_cohort.csv"
    
    with pytest.raises(FileNotFoundError):
        save_validated_cohort(
            intermediate_path=str(intermediate_path),
            validation_report_path=str(data_dir / "validation_report.json"),
            output_path=str(output_path)
        )


def test_save_cohort_missing_intermediate(temp_dirs):
    """Test that saving fails if intermediate cohort is missing."""
    base, data_dir = temp_dirs
    
    # Create passing validation report
    validation_report = {"is_valid": True, "errors": []}
    validation_path = data_dir / "validation_report.json"
    with open(validation_path, 'w') as f:
        json.dump(validation_report, f)
    
    # No intermediate cohort created
    output_path = data_dir / "analysis_cohort.csv"
    
    with pytest.raises(FileNotFoundError):
        save_validated_cohort(
            intermediate_path=str(data_dir / "intermediate_cohort.csv"),
            validation_report_path=str(validation_path),
            output_path=str(output_path)
        )


def test_save_cohort_output_schema(temp_dirs):
    """Test that the saved cohort has the expected columns."""
    base, data_dir = temp_dirs
    
    # Create intermediate cohort with expected columns
    expected_cols = [
        'age', 'gender', 'education', 'income',
        'social_support', 'harassment_exposure', 'harassment_severity',
        'depression', 'anxiety', 'ptsd'
    ]
    cohort_data = {col: [1, 2, 3] for col in expected_cols}
    intermediate_path = data_dir / "intermediate_cohort.csv"
    pd.DataFrame(cohort_data).to_csv(intermediate_path, index=False)
    
    # Create passing validation report
    validation_report = {"is_valid": True, "errors": []}
    validation_path = data_dir / "validation_report.json"
    with open(validation_path, 'w') as f:
        json.dump(validation_report, f)
    
    # Save cohort
    output_path = data_dir / "analysis_cohort.csv"
    save_validated_cohort(
        intermediate_path=str(intermediate_path),
        validation_report_path=str(validation_path),
        output_path=str(output_path)
    )
    
    # Verify schema
    saved_df = pd.read_csv(output_path)
    assert list(saved_df.columns) == expected_cols