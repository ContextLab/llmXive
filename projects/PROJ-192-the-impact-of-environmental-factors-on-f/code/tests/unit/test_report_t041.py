import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from src.pipelines.report import (
    generate_null_result_report,
    check_and_handle_null_results,
    load_permanova_results,
    apply_fdr_correction
)

def test_generate_null_result_report_creates_file():
    """Test that null result report is created with correct content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "null_report.csv")
        message = "No significant abiotic drivers detected"
        
        generate_null_result_report(output_path, message)
        
        assert os.path.exists(output_path)
        df = pd.read_csv(output_path)
        assert len(df) == 1
        assert df.iloc[0]["status"] == "NO_SIGNIFICANT_DRIVERS"
        assert df.iloc[0]["message"] == message

def test_check_and_handle_null_results_all_non_significant():
    """Test that null report is generated when all p-values > 0.05."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.csv")
        output_path = os.path.join(tmpdir, "output_null.csv")
        
        # Create data with p-values > 0.05
        df = pd.DataFrame({
            "term": ["pH", "Moisture"],
            "R2": [0.1, 0.05],
            "p-value": [0.15, 0.20]
        })
        df.to_csv(input_path, index=False)
        
        # Load and correct (simulate FDR)
        loaded = load_permanova_results(input_path)
        corrected = apply_fdr_correction(loaded)
        
        # Check function
        result = check_and_handle_null_results(corrected, output_path)
        
        assert result is True
        assert os.path.exists(output_path)

def test_check_and_handle_null_results_has_significant():
    """Test that null report is NOT generated when significant drivers exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.csv")
        output_path = os.path.join(tmpdir, "output_null.csv")
        
        # Create data with one significant p-value
        df = pd.DataFrame({
            "term": ["pH", "Moisture"],
            "R2": [0.5, 0.1],
            "p-value": [0.01, 0.20]
        })
        df.to_csv(input_path, index=False)
        
        loaded = load_permanova_results(input_path)
        corrected = apply_fdr_correction(loaded)
        
        result = check_and_handle_null_results(corrected, output_path)
        
        assert result is False
        # Null report should not be created if significant drivers exist
        # (Unless we explicitly create it for debugging, but the spec implies a specific report)
        # The function returns False, so the caller decides.
        # In the implementation, we only call generate_null_result_report if result is True.
        # So output_path should not exist if we strictly follow the logic in check_and_handle_null_results
        # However, the function itself creates the file if True. If False, it does not.
        assert not os.path.exists(output_path)

def test_check_and_handle_null_results_empty():
    """Test handling of empty DataFrame."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.csv")
        output_path = os.path.join(tmpdir, "output_null.csv")
        
        # Create empty file
        pd.DataFrame(columns=["term", "R2", "p-value"]).to_csv(input_path, index=False)
        
        loaded = load_permanova_results(input_path)
        result = check_and_handle_null_results(loaded, output_path)
        
        assert result is True
        assert os.path.exists(output_path)
        df = pd.read_csv(output_path)
        assert "No data available" in df.iloc[0]["message"]