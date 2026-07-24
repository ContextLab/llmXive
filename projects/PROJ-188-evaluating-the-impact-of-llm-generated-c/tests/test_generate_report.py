import json
import csv
import os
import tempfile
from pathlib import Path
import pytest

# Import the function to test
from generate_final_report import generate_report, load_analysis_results, load_sensitivity_data

def test_generate_report_structure(tmp_path):
    """Test that generate_report produces a valid markdown file with required sections."""
    
    # Setup mock input files
    lmm_results = {
        "interaction_f_stat": 4.5,
        "interaction_p_value": 0.01,
        "tukey_results": [
            {"comparison": "A vs B", "estimate": 0.1, "std_error": 0.05, "t_value": 2.0, "p_adj": 0.04}
        ]
    }
    sensitivity_data = [
        {"threshold": 0.5, "accuracy_mean": 0.8, "latency_mean": 40000, "p_value_interaction": 0.02}
    ]
    participant_stats = {"total": 10, "passed": 8}

    # Write mock inputs
    lmm_file = tmp_path / "analysis_results.json"
    with open(lmm_file, 'w') as f:
        json.dump(lmm_results, f)

    sens_file = tmp_path / "sensitivity_report.csv"
    with open(sens_file, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=sensitivity_data[0].keys())
        writer.writeheader()
        writer.writerow(sensitivity_data[0])

    stats_file = tmp_path / "participant_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(participant_stats, f)

    output_file = tmp_path / "final_report.md"

    # Run generation
    generate_report(lmm_file, sens_file, stats_file, output_file)

    # Assertions
    assert output_file.exists(), "Report file was not created."
    
    content = output_file.read_text()
    
    # Check for mandatory sections and content
    assert "# Final Report" in content, "Missing main header."
    assert "Interaction P-Value" in content, "Missing interaction p-value section."
    assert "0.01" in content, "Incorrect p-value in report."
    assert "BLEU similarity measures fidelity to the baseline" in content, "Missing FR-009 limitation statement."
    assert "sensitivity_chart.png" in content, "Missing chart reference."
    assert "Participant Quality Metrics" in content, "Missing participant stats section."
    
    # Check for chart file creation (even if empty or error handled)
    chart_file = tmp_path / "sensitivity_chart.png"
    assert chart_file.exists(), "Sensitivity chart was not generated."

def test_load_analysis_results_error_handling(tmp_path):
    """Test that load_analysis_results raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        load_analysis_results(tmp_path / "nonexistent.json")

def test_load_sensitivity_data_error_handling(tmp_path):
    """Test that load_sensitivity_data raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        load_sensitivity_data(tmp_path / "nonexistent.csv")
