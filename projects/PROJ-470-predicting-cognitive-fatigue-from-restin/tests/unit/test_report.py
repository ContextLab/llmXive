import os
import sys
import tempfile
import shutil
import pandas as pd
from pathlib import Path

# Add the project root to the path so we can import code modules
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from report import generate_report, load_analysis_results, load_sensitivity_table, render_markdown_table

def test_report_structure():
    """
    Test that the generated report contains the required sections.
    """
    # Create temporary directories for test data
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Setup analysis directory
        analysis_dir = tmpdir / "data" / "analysis"
        analysis_dir.mkdir(parents=True)
        
        # Create mock correlation results
        mock_results = pd.DataFrame({
            'channel': ['Fz', 'Cz', 'Pz'],
            'r': [0.45, 0.12, -0.33],
            'p_value': [0.02, 0.45, 0.08],
            'ci_lower': [0.05, -0.20, -0.60],
            'ci_upper': [0.75, 0.35, -0.05]
        })
        mock_results.to_csv(analysis_dir / "correlation_results.csv", index=False)
        
        # Create mock sensitivity table
        mock_sensitivity = pd.DataFrame({
            'threshold': [0.05, 0.01],
            'count_significant': [1, 0]
        })
        mock_sensitivity.to_csv(analysis_dir / "sensitivity_table.csv", index=False)
        
        # Setup docs directory
        docs_dir = tmpdir / "docs"
        docs_dir.mkdir(parents=True)
        report_path = docs_dir / "final_report.md"
        
        # Generate the report
        generate_report(mock_results, mock_sensitivity, str(report_path))
        
        # Verify the report exists
        assert report_path.exists(), "Report file was not created"
        
        # Read the content
        content = report_path.read_text()
        
        # Check for required sections
        assert "## Correlation Analysis" in content, "Missing 'Correlation Analysis' section"
        assert "## Statistical Significance" in content, "Missing 'Statistical Significance' section"
        assert "## Confidence Intervals" in content, "Missing 'Confidence Intervals' section"
        assert "## Sensitivity Analysis" in content, "Missing 'Sensitivity Analysis' section"
        
        # Check for specific data points
        assert "r = 0.45" in content or "| Fz | 0.4500 | 0.0200 |" in content, "Missing specific correlation data"
        assert "p = 0.02" in content or "| Fz | 0.4500 | 0.0200 |" in content, "Missing specific p-value data"
        
        # Check that sensitivity table is rendered
        assert "0.05" in content and "1" in content, "Sensitivity table data not found"
        
        print("All report structure tests passed.")

def test_report_with_empty_results():
    """
    Test report generation when results are empty.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Setup analysis directory
        analysis_dir = tmpdir / "data" / "analysis"
        analysis_dir.mkdir(parents=True)
        
        # Create empty results
        mock_results = pd.DataFrame()
        
        # Create mock sensitivity table
        mock_sensitivity = pd.DataFrame({
            'threshold': [0.05],
            'count_significant': [0]
        })
        mock_sensitivity.to_csv(analysis_dir / "sensitivity_table.csv", index=False)
        
        # Setup docs directory
        docs_dir = tmpdir / "docs"
        docs_dir.mkdir(parents=True)
        report_path = docs_dir / "final_report.md"
        
        # Generate the report
        generate_report(mock_results, mock_sensitivity, str(report_path))
        
        # Verify the report exists
        assert report_path.exists(), "Report file was not created"
        
        # Read the content
        content = report_path.read_text()
        
        # Check for expected fallback message
        assert "No correlation results available" in content, "Expected fallback message for empty results"
        
        # Check that sensitivity table is still rendered
        assert "## Sensitivity Analysis" in content, "Missing 'Sensitivity Analysis' section"
        
        print("Empty results test passed.")

def test_render_markdown_table():
    """
    Test the markdown table rendering function.
    """
    df = pd.DataFrame({
        'A': [1, 2],
        'B': [3, 4]
    })
    
    md = render_markdown_table(df, "Test Table")
    
    assert "### Test Table" in md, "Title not found"
    assert "| A | B |" in md, "Headers not found"
    assert "| 1 | 3 |" in md, "Row data not found"
    
    md_empty = render_markdown_table(None)
    assert "No data available" in md_empty, "Empty handling failed"
    
    print("Markdown table rendering test passed.")

if __name__ == "__main__":
    test_report_structure()
    test_report_with_empty_results()
    test_render_markdown_table()
    print("All tests passed successfully.")
