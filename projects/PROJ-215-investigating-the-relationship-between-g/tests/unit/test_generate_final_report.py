import pytest
import json
import pandas as pd
from pathlib import Path
import tempfile
import os

# Mock the config and logging for unit testing
import sys
from unittest.mock import patch, MagicMock

# We need to mock the config.get_output_path to point to temp directories
# and ensure the logging module is set up.

@pytest.fixture
def temp_dirs():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Create structure
        (tmp_path / "results").mkdir()
        (tmp_path / "data" / "interim").mkdir(parents=True)
        (tmp_path / "data" / "processed").mkdir(parents=True)
        yield tmp_path

@pytest.fixture
def mock_config(temp_dirs):
    with patch('code.generate_final_report.get_output_path') as mock_get_path:
        def side_effect(subpath):
            if subpath == "results":
                return str(temp_dirs / "results")
            elif subpath == "data/interim":
                return str(temp_dirs / "data" / "interim")
            elif subpath == "data/processed":
                return str(temp_dirs / "data" / "processed")
            return str(temp_dirs / subpath)
        mock_get_path.side_effect = side_effect
        yield

def test_generate_final_report_with_data(temp_dirs, mock_config):
    """Test that the report is generated correctly when all data is present."""
    from code.generate_final_report import generate_final_report, main
    
    # Create mock association results
    assoc_df = pd.DataFrame({
        'taxon': ['TaxonA', 'TaxonB', 'TaxonC'],
        'coef': [0.5, -0.3, 0.1],
        'pval': [0.01, 0.02, 0.06],
        'qval': [0.03, 0.04, 0.07],
        'direction': ['positive', 'negative', 'positive']
    })
    
    # Create mock covariate check
    covariate_data = {'max_delta': 0.02, 'threshold_met': True}
    with open(temp_dirs / "results" / "covariate_delta.json", 'w') as f:
        json.dump(covariate_data, f)
    
    # Create mock KS results
    ks_data = {'statistic': 0.1, 'p_value': 0.04, 'result': 'pass'}
    with open(temp_dirs / "data" / "processed" / "ks_test_results.json", 'w') as f:
        json.dump(ks_data, f)
    
    # Create mock validation report
    validation_text = "Validation Status: PASS\nMatch Rate: 90%"
    with open(temp_dirs / "results" / "validation_report.txt", 'w') as f:
        f.write(validation_text)
    
    # Create mock metrics
    metrics_data = {'retention_rate': 90.0, 'total_runtime_hours': 2.0}
    with open(temp_dirs / "results" / "metrics.json", 'w') as f:
        json.dump(metrics_data, f)
    
    # Generate report
    report = generate_final_report(
        association_results=assoc_df,
        covariate_check=covariate_data,
        ks_test_results=ks_data,
        validation_results=None,
        validation_report_text=validation_text,
        metrics=metrics_data
    )
    
    # Assertions
    assert "Executive Summary" in report
    assert "Significant taxa found: 3" in report
    assert "SC-005" in report
    assert "SC-002" in report
    assert "SC-003" in report
    assert "TaxonA" in report
    assert "positive" in report
    assert "Validation Status: PASS" in report

def test_generate_final_report_missing_data(temp_dirs, mock_config):
    """Test that the report handles missing data gracefully."""
    from code.generate_final_report import generate_final_report
    
    report = generate_final_report(
        association_results=None,
        covariate_check=None,
        ks_test_results=None,
        validation_results=None,
        validation_report_text=None,
        metrics=None
    )
    
    assert "No significant taxa identified" in report
    assert "Covariate adjustment check: SKIPPED" in report
    assert "KS Test for uniformity: SKIPPED" in report
    assert "Independent Cohort Validation: No report available" in report
    assert "Metrics data not available" in report
