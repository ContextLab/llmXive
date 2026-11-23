"""
Unit tests for generate_final_report.py
"""
import json
import os
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd

# Adjust path for imports if running standalone
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.analysis.generate_final_report import (
    load_json_safe, 
    load_csv_safe, 
    format_coefficient,
    generate_executive_summary,
    generate_main_table,
    generate_robustness_section,
    generate_limitations,
    generate_appendix,
    main
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_load_json_safe_found(temp_data_dir):
    file_path = temp_data_dir / "test.json"
    file_path.write_text('{"key": "value"}')
    result = load_json_safe(file_path)
    assert result == {"key": "value"}

def test_load_json_safe_not_found(temp_data_dir):
    file_path = temp_data_dir / "missing.json"
    result = load_json_safe(file_path)
    assert result == {}

def test_load_csv_safe_found(temp_data_dir):
    file_path = temp_data_dir / "test.csv"
    file_path.write_text("a,b\n1,2")
    result = load_csv_safe(file_path)
    assert len(result) == 1
    assert result['a'].iloc[0] == 1

def test_load_csv_safe_not_found(temp_data_dir):
    file_path = temp_data_dir / "missing.csv"
    result = load_csv_safe(file_path)
    assert result.empty

def test_format_coefficient():
    assert format_coefficient(1.23456) == "1.2346"
    assert format_coefficient(None) == "N/A"
    assert format_coefficient(float('nan')) == "N/A"
    assert format_coefficient("invalid") == "N/A"

def test_generate_executive_summary_positive():
    main_res = {
        'author_count_coefficient': 0.5,
        'p_value': 0.01
    }
    summary = generate_executive_summary(main_res, {})
    assert "positive" in summary.lower()
    assert "statistically significant" in summary.lower()

def test_generate_executive_summary_negative():
    main_res = {
        'author_count_coefficient': -0.5,
        'p_value': 0.01
    }
    summary = generate_executive_summary(main_res, {})
    assert "negative" in summary.lower()

def test_generate_executive_summary_inconclusive():
    main_res = {
        'author_count_coefficient': 0.5,
        'p_value': 0.20
    }
    summary = generate_executive_summary(main_res, {})
    assert "not statistically significant" in summary.lower()

def test_generate_main_table():
    main_res = {
        'author_count_coefficient': 0.5,
        'std_err': 0.1,
        'p_value': 0.01,
        'ci_95_lower': 0.3,
        'ci_95_upper': 0.7
    }
    table = generate_main_table(main_res)
    assert "| Author Count |" in table
    assert "0.5000" in table

def test_generate_main_table_warning():
    main_res = {
        'author_count_coefficient': 0.5,
        'high_collinearity_warning': True
    }
    table = generate_main_table(main_res)
    assert "Warning" in table

def test_generate_robustness_section():
    robust_data = {
        'subsample_results': [
            {'language': 'Python', 'coefficient': 0.4, 'std_err': 0.1, 'p_value_raw': 0.02, 'n_rows': 50}
        ]
    }
    section = generate_robustness_section(robust_data)
    assert "Python" in section
    assert "0.4000" in section

def test_generate_limitations():
    main_res = {'high_collinearity_warning': True}
    robust_data = {'excluded_subsamples': True}
    limit = generate_limitations(main_res, robust_data)
    assert "High collinearity" in limit
    assert "insufficient sample size" in limit.lower()

def test_generate_appendix():
    appendix = generate_appendix()
    assert "Reproducibility" in appendix
    assert "python code/analysis/generate_final_report.py" in appendix
