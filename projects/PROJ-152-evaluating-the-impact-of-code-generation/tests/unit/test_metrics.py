"""
Unit tests for metrics.py - Severity Mapping and Metrics Calculation
"""
import pytest
import os
import yaml
import pandas as pd
from pathlib import Path
import tempfile
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from metrics import (
    load_severity_map,
    map_severity_to_ordinal,
    process_findings_csv,
    calculate_vuln_density
)

@pytest.fixture
def temp_severity_map():
    """Create a temporary NIST severity map file."""
    map_data = {
        'default': {
            'HIGH': 4,
            'MEDIUM': 3,
            'LOW': 2,
            'INFO': 1
        },
        'scanners': {
            'bandit': {
                'HIGH': 4,
                'MEDIUM': 3,
                'LOW': 2
            },
            'semgrep': {
                'ERROR': 4,
                'WARNING': 3,
                'NOTE': 2
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(map_data, f)
        return f.name

@pytest.fixture
def temp_findings_csv():
    """Create a temporary raw findings CSV file."""
    data = {
        'finding_id': ['F001', 'F002', 'F003', 'F004'],
        'snippet_id': ['S001', 'S001', 'S002', 'S003'],
        'scanner': ['bandit', 'bandit', 'semgrep', 'bandit'],
        'cwe_id': ['CWE-89', 'CWE-79', 'CWE-79', 'CWE-287'],
        'raw_severity': ['HIGH', 'MEDIUM', 'WARNING', 'LOW'],
        'finding_text': ['SQL Injection', 'XSS', 'XSS', 'Auth Bypass']
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f, index=False)
        return f.name

@pytest.fixture
def temp_snippets_csv():
    """Create a temporary snippets CSV file."""
    data = {
        'snippet_id': ['S001', 'S002', 'S003', 'S004'],
        'model': ['starcoder', 'starcoder', 'codegen', 'neox'],
        'prompt_id': ['P001', 'P002', 'P003', 'P004'],
        'code': ['code1', 'code2', 'code3', 'code4'],
        'line_count': [50, 100, 200, 0]  # Include edge case: 0 lines
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f, index=False)
        return f.name

def test_load_severity_map_success(temp_severity_map):
    """Test successful loading of severity map."""
    result = load_severity_map(temp_severity_map)
    assert 'default' in result
    assert 'scanners' in result
    assert result['default']['HIGH'] == 4

def test_load_severity_map_not_found():
    """Test loading non-existent severity map raises error."""
    with pytest.raises(FileNotFoundError):
        load_severity_map("/nonexistent/path/map.yaml")

def test_map_severity_to_ordinal_valid(temp_severity_map):
    """Test mapping valid severities."""
    map_data = load_severity_map(temp_severity_map)
    
    assert map_severity_to_ordinal("HIGH", "bandit", map_data) == 4
    assert map_severity_to_ordinal("MEDIUM", "bandit", map_data) == 3
    assert map_severity_to_ordinal("WARNING", "semgrep", map_data) == 3
    assert map_severity_to_ordinal("INFO", "unknown_scanner", map_data) == 1

def test_map_severity_to_ordinal_invalid(temp_severity_map):
    """Test mapping invalid severity raises error."""
    map_data = load_severity_map(temp_severity_map)
    
    with pytest.raises(ValueError):
        map_severity_to_ordinal("CRITICAL", "bandit", map_data)

def test_process_findings_csv(temp_findings_csv, temp_severity_map, tmp_path):
    """Test processing findings CSV and adding mapped severity."""
    output_path = tmp_path / "processed_findings.csv"
    
    result_df = process_findings_csv(temp_findings_csv, str(output_path), temp_severity_map)
    
    assert 'mapped_ordinal_rank' in result_df.columns
    assert len(result_df) == 4
    assert result_df.iloc[0]['mapped_ordinal_rank'] == 4  # HIGH -> 4
    assert result_df.iloc[1]['mapped_ordinal_rank'] == 3  # MEDIUM -> 3
    assert result_df.iloc[2]['mapped_ordinal_rank'] == 3  # WARNING -> 3
    
    # Verify output file was created
    assert output_path.exists()
    output_df = pd.read_csv(output_path)
    assert 'mapped_ordinal_rank' in output_df.columns

def test_process_findings_csv_missing_input():
    """Test processing with missing input file raises error."""
    with tempfile.NamedTemporaryFile(suffix='.yaml') as map_f:
        with pytest.raises(FileNotFoundError):
            process_findings_csv("/nonexistent/findings.csv", "/tmp/out.csv", map_f.name)

def test_calculate_vuln_density(temp_snippets_csv, temp_findings_csv):
    """Test vulnerability density calculation."""
    snippets_df = pd.read_csv(temp_snippets_csv)
    findings_df = pd.read_csv(temp_findings_csv)
    
    # Manually add mapped ranks for this test
    findings_df['mapped_ordinal_rank'] = [4, 3, 3, 2]
    
    result = calculate_vuln_density(snippets_df, findings_df)
    
    assert 'vuln_count' in result.columns
    assert 'vuln_density' in result.columns
    
    # S001: 2 vulns, 50 lines -> 4.0 density
    s001 = result[result['snippet_id'] == 'S001'].iloc[0]
    assert s001['vuln_count'] == 2
    assert s001['vuln_density'] == 4.0
    
    # S002: 1 vuln, 100 lines -> 1.0 density
    s002 = result[result['snippet_id'] == 'S002'].iloc[0]
    assert s002['vuln_count'] == 1
    assert s002['vuln_density'] == 1.0
    
    # S003: 1 vuln, 200 lines -> 0.5 density
    s003 = result[result['snippet_id'] == 'S003'].iloc[0]
    assert s003['vuln_count'] == 1
    assert s003['vuln_density'] == 0.5
    
    # S004: 0 vulns, 0 lines -> 0.0 density (avoid div by zero)
    s004 = result[result['snippet_id'] == 'S004'].iloc[0]
    assert s004['vuln_count'] == 0
    assert s004['vuln_density'] == 0.0

def test_calculate_vuln_density_missing_columns():
    """Test density calculation with missing columns raises error."""
    snippets_df = pd.DataFrame({'snippet_id': ['S001']})
    findings_df = pd.DataFrame({'finding_id': ['F001']})
    
    with pytest.raises(ValueError):
        calculate_vuln_density(snippets_df, findings_df)