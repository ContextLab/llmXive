"""
Integration test for T029: Report Generation.
Verifies that the report generator creates valid JSON and Markdown files
with correct structure and content.
"""
import os
import json
import tempfile
import pandas as pd
import pytest
from pathlib import Path

from code.report_generator import (
    generate_json_report,
    generate_markdown_report,
    run_report_pipeline
)


@pytest.fixture
def sample_regression_df():
    """Create a sample DataFrame mimicking statsmodels regression output."""
    data = {
        'term': [
            'Intercept',
            'PathologyStatus',
            'BrainRegion_Hippocampus',
            'BrainRegion_Cortex',
            'PathologyStatus*BrainRegion_Hippocampus',
            'BranchPoints',
            'TotalLength'
        ],
        'coef': [0.5, -0.3, 0.1, 0.05, -0.15, -0.02, -0.01],
        'std_err': [0.05, 0.08, 0.06, 0.07, 0.09, 0.005, 0.004],
        't': [10.0, -3.75, 1.67, 0.71, -1.67, -4.0, -2.5],
        'P>|t|': [0.0, 0.0002, 0.096, 0.478, 0.096, 0.0001, 0.013]
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_vif_data():
    """Sample VIF check data."""
    return {
        "trigger_pca": False,
        "vif_scores": {
            "PathologyStatus": 1.2,
            "BrainRegion_Hippocampus": 1.5,
            "BrainRegion_Cortex": 1.4,
            "BranchPoints": 2.1,
            "TotalLength": 1.8
        }
    }


def test_generate_json_report_creates_valid_file(sample_regression_df, sample_vif_data):
    """Test that generate_json_report creates a valid JSON file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_results.json")
        
        report = generate_json_report(
            sample_regression_df,
            sample_vif_data,
            causality_warning=True,
            output_path=output_path
        )
        
        # Verify file exists
        assert os.path.exists(output_path), "JSON report file was not created"
        
        # Verify JSON is valid and can be re-loaded
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        
        # Check structure
        assert "metadata" in loaded
        assert "regression_results" in loaded
        assert "multicollinearity_check" in loaded
        
        # Check metadata
        assert loaded["metadata"]["causality_warning"] is True
        assert loaded["metadata"]["task_id"] == "T029"
        
        # Check regression results
        assert len(loaded["regression_results"]["terms"]) == len(sample_regression_df)
        
        # Check interaction terms detection
        interaction_terms = loaded["regression_results"]["interaction_terms"]
        assert len(interaction_terms) == 1
        assert "PathologyStatus*BrainRegion_Hippocampus" in interaction_terms[0]["term"]


def test_generate_markdown_report_creates_valid_file(sample_regression_df, sample_vif_data):
    """Test that generate_markdown_report creates a valid Markdown file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = os.path.join(tmpdir, "test_results.json")
        md_path = os.path.join(tmpdir, "test_results.md")
        
        # First generate JSON
        generate_json_report(
            sample_regression_df,
            sample_vif_data,
            causality_warning=True,
            output_path=json_path
        )
        
        # Load JSON and generate MD
        with open(json_path, 'r') as f:
            json_report = json.load(f)
        
        generate_markdown_report(json_report, md_path)
        
        # Verify file exists
        assert os.path.exists(md_path), "Markdown report file was not created"
        
        # Read and verify content
        with open(md_path, 'r') as f:
            content = f.read()
        
        # Check for key sections
        assert "# Regression Analysis Report" in content
        assert "## Executive Summary" in content
        assert "## Multicollinearity Check" in content
        assert "## Detailed Regression Results" in content
        assert "## Conclusion" in content
        
        # Check for warning
        assert "causality" in content.lower() or "causality" in content


def test_run_report_pipeline_end_to_end(sample_regression_df, sample_vif_data):
    """Test the full pipeline with temporary files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create input files
        csv_path = os.path.join(tmpdir, "regression_results.csv")
        vif_path = os.path.join(tmpdir, "vif_check.json")
        output_dir = os.path.join(tmpdir, "reports")
        
        sample_regression_df.to_csv(csv_path, index=False)
        with open(vif_path, 'w') as f:
            json.dump(sample_vif_data, f)
        
        # Run pipeline
        result = run_report_pipeline(
            regression_csv=csv_path,
            vif_json=vif_path,
            output_dir=output_dir,
            causality_warning=True
        )
        
        # Verify outputs exist
        assert os.path.exists(result["json_report"])
        assert os.path.exists(result["md_report"])
        
        # Verify they are in the correct directory
        assert result["json_report"].startswith(output_dir)
        assert result["md_report"].startswith(output_dir)
        
        # Verify JSON is valid
        with open(result["json_report"], 'r') as f:
            json.load(f)
        
        # Verify MD has content
        with open(result["md_report"], 'r') as f:
            content = f.read()
        assert len(content) > 100  # Should be a substantial report
