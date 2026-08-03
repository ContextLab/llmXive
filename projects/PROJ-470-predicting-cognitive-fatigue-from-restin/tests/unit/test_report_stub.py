"""
Unit tests for the report generation stub (T007).
Verifies that report.py can read CSV tables and render them as markdown.
"""
import os
import sys
import tempfile
import shutil
import pandas as pd
import pytest
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from report import load_sensitivity_table, render_markdown_table, generate_report

def test_load_sensitivity_table_from_csv():
    """Test loading a dummy sensitivity table from CSV."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "sensitivity_table.csv"
        # Create dummy CSV as per T022 schema
        df = pd.DataFrame({
            'threshold': [0.05, 0.01],
            'count_significant': [5, 2]
        })
        df.to_csv(csv_path, index=False)
        
        loaded_df = load_sensitivity_table(str(csv_path))
        
        assert not loaded_df.empty
        assert 'threshold' in loaded_df.columns
        assert 'count_significant' in loaded_df.columns
        assert len(loaded_df) == 2
        assert loaded_df.iloc[0]['threshold'] == 0.05
        assert loaded_df.iloc[0]['count_significant'] == 5

def test_render_markdown_table():
    """Test rendering a DataFrame to markdown string."""
    df = pd.DataFrame({
        'threshold': [0.05, 0.01],
        'count_significant': [5, 2]
    })
    
    markdown_str = render_markdown_table(df)
    
    assert isinstance(markdown_str, str)
    assert '|' in markdown_str
    assert 'threshold' in markdown_str
    assert '0.05' in markdown_str
    assert '5' in markdown_str

def test_report_includes_csv_data():
    """Test that the generated report contains the CSV data formatted as markdown."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data" / "analysis"
        docs_dir = Path(tmpdir) / "docs"
        data_dir.mkdir(parents=True)
        docs_dir.mkdir(parents=True)
        
        # Create dummy sensitivity table
        sensitivity_path = data_dir / "sensitivity_table.csv"
        df = pd.DataFrame({
            'threshold': [0.05, 0.01],
            'count_significant': [10, 3]
        })
        df.to_csv(sensitivity_path, index=False)
        
        # Create dummy results JSON
        results_path = data_dir / "results.json"
        import json
        with open(results_path, 'w') as f:
            json.dump({'r': 0.45, 'p': 0.02}, f)
        
        output_path = docs_dir / "final_report.md"
        
        # Load and generate
        loaded_df = load_sensitivity_table(str(sensitivity_path))
        results = load_sensitivity_table(str(results_path.replace('.csv', '.json'))) # Hacky load for test
        import json as j
        with open(results_path, 'r') as f:
            results = j.load(f)
        
        generate_report(results, loaded_df, str(output_path))
        
        # Verify output
        assert output_path.exists()
        with open(output_path, 'r') as f:
            content = f.read()
        
        assert "## Sensitivity Analysis" in content
        assert "threshold" in content
        assert "0.05" in content
        assert "10" in content
        assert "0.01" in content
        assert "3" in content

def test_report_handles_empty_table():
    """Test that report handles empty sensitivity table gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        docs_dir = Path(tmpdir) / "docs"
        docs_dir.mkdir(parents=True)
        
        output_path = docs_dir / "final_report.md"
        empty_df = pd.DataFrame()
        results = {'r': 0.1, 'p': 0.5}
        
        generate_report(results, empty_df, str(output_path))
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            content = f.read()
        
        assert "No sensitivity analysis data available" in content
        assert "## Correlation Analysis" in content
