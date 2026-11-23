import os
import sys
import pandas as pd
import pytest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_report_stub_generation(tmp_path):
    """
    Test that code/report.py can ingest a dummy CSV and render it as markdown.
    This test mocks the file existence to avoid dependency on future artifacts.
    """
    # Setup temporary directories
    analysis_dir = tmp_path / "data" / "analysis"
    docs_dir = tmp_path / "docs"
    analysis_dir.mkdir(parents=True)
    docs_dir.mkdir(parents=True)

    # Create a dummy sensitivity table as specified in T007
    dummy_sensitivity = pd.DataFrame({
        "threshold": [0.05, 0.01],
        "significant_count": [5, 1]
    })
    sensitivity_path = analysis_dir / "sensitivity_table.csv"
    dummy_sensitivity.to_csv(sensitivity_path, index=False)

    # Create a dummy correlation results file (required by report.py logic)
    dummy_results = pd.DataFrame({
        "channel": ["Fz", "Cz", "Pz"],
        "correlation": [0.45, 0.12, 0.33],
        "p_value": [0.01, 0.45, 0.03],
        "method": ["pearson", "pearson", "pearson"]
    })
    results_path = analysis_dir / "correlation_results.csv"
    dummy_results.to_csv(results_path, index=False)

    # Change CWD to tmp_path to simulate project root
    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        # Import the module under test
        from code.report import main, generate_report, load_sensitivity_table, render_markdown_table

        # Verify load_sensitivity_table works
        loaded_df = load_sensitivity_table(sensitivity_path)
        assert loaded_df is not None
        assert "threshold" in loaded_df.columns
        assert loaded_df["significant_count"].iloc[0] == 5

        # Verify render_markdown_table works without pandas OptionError
        md_table = render_markdown_table(loaded_df)
        assert "| threshold | significant_count |" in md_table
        assert "| --- | --- |" in md_table
        assert "0.05" in md_table

        # Run the main function (which generates the report)
        # We patch the paths slightly by using the tmp_path context
        # The main function expects data/analysis and docs relative to cwd
        main()

        # Verify output file exists
        output_file = docs_dir / "final_report.md"
        assert output_file.exists(), "Report file was not generated"

        # Verify content contains the CSV data formatted as markdown
        content = output_file.read_text()
        assert "# Cognitive Fatigue Analysis Report" in content
        assert "## Correlation Results" in content
        assert "## Sensitivity Analysis" in content
        assert "0.05" in content
        assert "5" in content
        assert "Fz" in content

    finally:
        os.chdir(original_cwd)

def test_report_handles_missing_files_gracefully(tmp_path):
    """
    Test that report.py handles missing sensitivity table by creating a dummy one
    and proceeding without crashing (as per T007 implementation detail).
    """
    analysis_dir = tmp_path / "data" / "analysis"
    docs_dir = tmp_path / "docs"
    analysis_dir.mkdir(parents=True)
    docs_dir.mkdir(parents=True)

    # Create only correlation results, NOT sensitivity table
    dummy_results = pd.DataFrame({
        "channel": ["Fz"],
        "correlation": [0.5],
        "p_value": [0.05],
        "method": ["pearson"]
    })
    (analysis_dir / "correlation_results.csv").to_csv(dummy_results, index=False)

    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        from code.report import main

        # Should not raise an exception even if sensitivity table is missing
        # It should create a dummy one and generate the report
        main()

        output_file = docs_dir / "final_report.md"
        assert output_file.exists()
        
        # Verify the dummy sensitivity table was created
        assert (analysis_dir / "sensitivity_table.csv").exists()
        
    finally:
        os.chdir(original_cwd)