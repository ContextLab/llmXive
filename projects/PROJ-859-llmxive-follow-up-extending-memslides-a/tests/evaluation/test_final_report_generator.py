"""
Tests for the Final Report Generator.
"""
import json
import csv
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from evaluation.final_report_generator import (
    compute_file_hash,
    load_json_safe,
    load_csv_safe,
    generate_data_provenance_section,
    generate_statistical_analysis_section,
    generate_sensitivity_sweep_section,
    generate_report,
    FinalReportError
)
from config import get_config

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

def test_compute_file_hash(temp_dir):
    """Test SHA256 hash computation."""
    test_file = temp_dir / "test.txt"
    content = "Hello, World!"
    test_file.write_text(content)
    
    # Expected hash for "Hello, World!"
    import hashlib
    expected = hashlib.sha256(content.encode()).hexdigest()
    
    result = compute_file_hash(test_file)
    assert result == expected

def test_compute_file_hash_missing():
    """Test hash computation on missing file raises error."""
    with pytest.raises(FinalReportError):
        compute_file_hash(Path("/nonexistent/file.txt"))

def test_load_json_safe(temp_dir):
    """Test safe JSON loading."""
    test_file = temp_dir / "data.json"
    data = {"key": "value", "num": 123}
    test_file.write_text(json.dumps(data))
    
    result = load_json_safe(test_file)
    assert result == data

def test_load_json_safe_missing(temp_dir):
    """Test safe JSON loading on missing file returns None."""
    result = load_json_safe(temp_dir / "missing.json")
    assert result is None

def test_load_csv_safe(temp_dir):
    """Test safe CSV loading."""
    test_file = temp_dir / "data.csv"
    test_file.write_text("a,b\n1,2\n3,4")
    
    result = load_csv_safe(test_file)
    assert len(result) == 2
    assert result[0] == {"a": "1", "b": "2"}

def test_generate_data_provenance_section():
    """Test generation of the provenance section."""
    config = get_config()
    stats_data = {"method_used": "beta_regression"}
    sweep_data = [{"compression_ratio": 0.5, "fidelity_rate": 0.9}]
    imputation_data = {"total_traces": 100, "imputed_count": 10, "reasons": {"nan": 10}}
    lineage_data = {"summary": "Test lineage"}
    
    section = generate_data_provenance_section(stats_data, sweep_data, imputation_data, lineage_data, config)
    
    assert "Data Provenance" in section
    assert "Configuration & Random Seed" in section
    assert "Imputation Statistics" in section
    assert "Input Artifact Integrity" in section
    assert str(config.SEED) in section

def test_generate_statistical_analysis_section_beta():
    """Test statistical section with beta regression."""
    data = {
        "method_used": "beta_regression",
        "beta_coefficients": {"entropy": 0.5, "repetition": -0.2},
        "p_values": {"entropy": 0.01, "repetition": 0.5}
    }
    section = generate_statistical_analysis_section(data)
    
    assert "Beta Regression" in section
    assert "entropy" in section
    assert "repetition" in section
    assert "0.01" in section

def test_generate_statistical_analysis_section_missing():
    """Test statistical section with missing data."""
    section = generate_statistical_analysis_section(None)
    assert "Warning" in section

def test_generate_sensitivity_sweep_section():
    """Test sensitivity sweep section generation."""
    data = [
        {"compression_ratio": 0.1, "fidelity_tolerance": 0.8, "fidelity_rate": 0.95, "latency": 100, "rule_count": 50},
        {"compression_ratio": 0.5, "fidelity_tolerance": 0.9, "fidelity_rate": 0.85, "latency": 200, "rule_count": 20}
    ]
    section = generate_sensitivity_sweep_section(data)
    
    assert "Sensitivity Sweep Analysis" in section
    assert "0.1" in section
    assert "0.95" in section

def test_generate_report_full(temp_dir):
    """Test end-to-end report generation."""
    # Create mock input files
    stats_path = temp_dir / "statistical_analysis.json"
    stats_path.write_text(json.dumps({"method_used": "beta_regression", "beta_coefficients": {"x": 1.0}, "p_values": {"x": 0.01}}))
    
    sweep_path = temp_dir / "sensitivity_sweep.csv"
    with open(sweep_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["compression_ratio", "fidelity_tolerance", "fidelity_rate", "latency", "rule_count"])
        writer.writerow([0.5, 0.9, 0.95, 100, 50])
    
    imputation_path = temp_dir / "imputation_summary.md"
    imputation_path.write_text("# Imputation Summary\n\nTotal: 100, Imputed: 5")
    
    lineage_path = temp_dir / "data_lineage.json"
    lineage_path.write_text(json.dumps({"summary": "Test DAG"}))
    
    output_path = temp_dir / "final_report.md"
    
    config = get_config()
    
    # Generate report
    generate_report(stats_path, sweep_path, imputation_path, lineage_path, output_path, config)
    
    # Verify output exists and contains expected content
    assert output_path.exists()
    content = output_path.read_text()
    assert "Data Provenance" in content
    assert "Statistical Analysis Results" in content
    assert "Sensitivity Sweep Analysis" in content
    assert "Data Lineage" in content

def test_generate_report_missing_input(temp_dir):
    """Test report generation fails loudly if input is missing."""
    output_path = temp_dir / "final_report.md"
    config = get_config()
    
    with pytest.raises(FinalReportError) as exc_info:
        generate_report(
            temp_dir / "missing_stats.json",
            temp_dir / "missing_sweep.csv",
            temp_dir / "missing_imp.md",
            temp_dir / "missing_lineage.json",
            output_path,
            config
        )
    
    assert "Critical input files missing" in str(exc_info.value)