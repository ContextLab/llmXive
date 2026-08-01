import os
import sys
import tempfile
import shutil
import pandas as pd
import pytest
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from report import load_sensitivity_table, render_markdown_table, generate_report, load_analysis_results

def test_report_stub_ingests_sensitivity_table():
    """
    T007 Verification: 
    1. Create a dummy data/analysis/sensitivity_table.csv
    2. Run the logic that would be triggered by report.py (load and render)
    3. Assert the output contains the CSV data formatted as a markdown table.
    """
    # Setup: Create temporary directory structure
    original_cwd = os.getcwd()
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Change to temp dir to isolate file system operations
        os.chdir(temp_dir)
        
        # Create necessary directories
        data_analysis_dir = Path("data/analysis")
        data_analysis_dir.mkdir(parents=True, exist_ok=True)
        docs_dir = Path("docs")
        docs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create dummy sensitivity_table.csv
        dummy_data = {
            "threshold": [0.05, 0.01],
            "count_significant": [12, 5]
        }
        dummy_df = pd.DataFrame(dummy_data)
        dummy_df.to_csv(data_analysis_dir / "sensitivity_table.csv", index=False)
        
        # Execute: Load the table and render it
        loaded_df = load_sensitivity_table("data/analysis/sensitivity_table.csv")
        
        assert loaded_df is not None, "Failed to load sensitivity table"
        assert len(loaded_df) == 2, "Expected 2 rows in dummy data"
        assert "threshold" in loaded_df.columns, "Missing 'threshold' column"
        assert "count_significant" in loaded_df.columns, "Missing 'count_significant' column"
        
        # Render to markdown
        md_output = render_markdown_table(loaded_df, "Sensitivity Analysis")
        
        # Verify: Check that the markdown output contains the data
        assert "threshold" in md_output, "Markdown table missing 'threshold' header"
        assert "count_significant" in md_output, "Markdown table missing 'count_significant' header"
        assert "0.05" in md_output, "Markdown table missing data value 0.05"
        assert "12" in md_output, "Markdown table missing data value 12"
        assert "0.01" in md_output, "Markdown table missing data value 0.01"
        assert "5" in md_output, "Markdown table missing data value 5"
        
        # Test full report generation flow
        report_path = generate_report({"sensitivity_table": loaded_df}, "docs/final_report.md")
        
        assert os.path.exists(report_path), f"Report file not created at {report_path}"
        
        with open(report_path, 'r') as f:
            report_content = f.read()
        
        assert "Sensitivity Analysis" in report_content, "Report missing Sensitivity Analysis section"
        assert "0.05" in report_content, "Report missing data from sensitivity table"
        
    finally:
        # Cleanup
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)

def test_load_analysis_results_handles_missing_dir():
    """Test that load_analysis_results returns empty dict if directory is missing."""
    original_cwd = os.getcwd()
    temp_dir = tempfile.mkdtemp()
    
    try:
        os.chdir(temp_dir)
        # Ensure directory does not exist
        if os.path.exists("data/analysis"):
            shutil.rmtree("data/analysis")
        
        results = load_analysis_results()
        assert results == {}, "Expected empty dict when directory is missing"
        
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)
