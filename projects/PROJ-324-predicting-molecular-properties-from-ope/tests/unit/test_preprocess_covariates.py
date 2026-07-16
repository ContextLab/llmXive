import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
from io import StringIO

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.data.preprocess import detect_missing_covariates, generate_quality_report

class TestDetectMissingCovariates:
    
    def test_no_missing_covariates(self):
        """Test when all covariates are present."""
        data = {
            "smiles": ["CCO", "CCN"],
            "logP": [0.5, 1.0],
            "temperature": [25.0, 30.0],
            "pH": [7.0, 6.5]
        }
        df = pd.DataFrame(data)
        filtered, excluded = detect_missing_covariates(df, ["temperature", "pH"])
        
        assert len(filtered) == 2
        assert len(excluded) == 0
        assert "missing_covariate" not in excluded.columns or excluded.empty

    def test_some_missing_covariates(self):
        """Test when some rows have missing covariates."""
        data = {
            "smiles": ["CCO", "CCN", "CC"],
            "logP": [0.5, 1.0, 0.2],
            "temperature": [25.0, np.nan, 30.0],
            "pH": [7.0, 6.5, np.nan]
        }
        df = pd.DataFrame(data)
        filtered, excluded = detect_missing_covariates(df, ["temperature", "pH"])
        
        assert len(filtered) == 1 # Only the first row has both
        assert len(excluded) == 2 # Second row missing temp, third missing pH
        
        # Check that missing_covariate column is populated
        assert "missing_covariate" in excluded.columns
        assert excluded.loc[0, "missing_covariate"] == "temperature" # Row 1 (index 1 in orig) missing temp
        assert excluded.loc[1, "missing_covariate"] == "pH" # Row 2 (index 2 in orig) missing pH

    def test_all_missing_covariates(self):
        """Test when all rows have missing covariates."""
        data = {
            "smiles": ["CCO", "CCN"],
            "logP": [0.5, 1.0],
            "temperature": [np.nan, np.nan],
            "pH": [np.nan, np.nan]
        }
        df = pd.DataFrame(data)
        filtered, excluded = detect_missing_covariates(df, ["temperature", "pH"])
        
        assert len(filtered) == 0
        assert len(excluded) == 2
        assert excluded.loc[0, "missing_covariate"] == "temperature,pH"
        assert excluded.loc[1, "missing_covariate"] == "temperature,pH"

    def test_no_covariate_columns(self):
        """Test when covariate columns are not in the dataframe."""
        data = {
            "smiles": ["CCO", "CCN"],
            "logP": [0.5, 1.0]
        }
        df = pd.DataFrame(data)
        filtered, excluded = detect_missing_covariates(df, ["temperature", "pH"])
        
        assert len(filtered) == 2
        assert len(excluded) == 0

class TestGenerateQualityReport:
    
    def test_generate_report_single_exclusion(self):
        """Test generating report with one exclusion reason."""
        excluded_df = pd.DataFrame({
            "smiles": ["CCO"],
            "missing_covariate": ["temperature"]
        })
        report = generate_quality_report([excluded_df], ["missing_covariates"])
        
        assert len(report) == 1
        assert report["exclusion_reason"].iloc[0] == "missing_covariates"
        assert report["missing_covariate"].iloc[0] == "temperature"

    def test_generate_report_multiple_exclusions(self):
        """Test generating report with multiple exclusion reasons."""
        excluded1 = pd.DataFrame({
            "smiles": ["CCO"],
            "missing_covariate": ["temperature"]
        })
        excluded2 = pd.DataFrame({
            "smiles": ["CCN"],
            "missing_covariate": [""] # Empty string if not from covariate check
        })
        
        report = generate_quality_report([excluded1, excluded2], ["missing_covariates", "low_confidence"])
        
        assert len(report) == 2
        assert report["exclusion_reason"].iloc[0] == "missing_covariates"
        assert report["exclusion_reason"].iloc[1] == "low_confidence"
        assert report["missing_covariate"].iloc[0] == "temperature"
        assert report["missing_covariate"].iloc[1] == ""

    def test_empty_exclusions(self):
        """Test generating report with no excluded data."""
        report = generate_quality_report([], [])
        assert report.empty