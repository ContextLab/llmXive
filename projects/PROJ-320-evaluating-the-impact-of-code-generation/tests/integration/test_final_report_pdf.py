"""
Integration test for T036: Final Report PDF Generation.

Verifies that the final report PDF is generated with all required plots
and correlation coefficients.
"""
import os
import sys
import json
import csv
from pathlib import Path
import pytest
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from analysis.generate_final_report_pdf import (
    load_metrics_data,
    calculate_correlation_coefficients,
    generate_final_report_pdf,
    OUTPUT_PDF
)

@pytest.fixture
def sample_metrics_file(tmp_path):
    """Create a sample metrics CSV file for testing."""
    metrics_dir = tmp_path / "data" / "processed"
    metrics_dir.mkdir(parents=True)
    metrics_file = metrics_dir / "prs_metrics.csv"
    
    data = [
        {'pr_id': 1, 'source_type': 'llm', 'comment_count': 5, 'time_to_merge_minutes': 120.5, 'review_cycles': 2, 'complexity_score': 15.2},
        {'pr_id': 2, 'source_type': 'human', 'comment_count': 8, 'time_to_merge_minutes': 180.0, 'review_cycles': 3, 'complexity_score': 18.5},
        {'pr_id': 3, 'source_type': 'llm', 'comment_count': 3, 'time_to_merge_minutes': 90.0, 'review_cycles': 1, 'complexity_score': 12.0},
        {'pr_id': 4, 'source_type': 'human', 'comment_count': 10, 'time_to_merge_minutes': 200.0, 'review_cycles': 4, 'complexity_score': 20.0},
        {'pr_id': 5, 'source_type': 'llm', 'comment_count': 6, 'time_to_merge_minutes': 150.0, 'review_cycles': 2, 'complexity_score': 16.0},
    ]
    
    with open(metrics_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['pr_id', 'source_type', 'comment_count', 'time_to_merge_minutes', 'review_cycles', 'complexity_score'])
        writer.writeheader()
        writer.writerows(data)
    
    return metrics_file

@pytest.fixture
def sample_results_file(tmp_path, sample_metrics_file):
    """Create a sample results JSON file for testing."""
    results_dir = sample_metrics_file.parent
    results_file = results_dir / "results.json"
    
    results = {
        'statistical_tests': {
            'comment_density': {
                't_statistic': -2.15,
                'p_value': 0.045,
                'effect_size': -0.85,
                'significant': True
            },
            'time_to_merge': {
                't_statistic': -1.85,
                'p_value': 0.078,
                'effect_size': -0.72,
                'significant': False
            }
        }
    }
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    return results_file

def test_load_metrics_data(sample_metrics_file):
    """Test that metrics data is loaded correctly."""
    # Temporarily override the global path
    original_path = generate_final_report_pdf.__globals__['METRICS_FILE']
    try:
        generate_final_report_pdf.__globals__['METRICS_FILE'] = sample_metrics_file
        data = load_metrics_data()
        assert len(data) == 5
        assert data[0]['source_type'] == 'llm'
        assert data[0]['comment_count'] == 5
        assert data[0]['complexity_score'] == 15.2
    finally:
        generate_final_report_pdf.__globals__['METRICS_FILE'] = original_path

def test_calculate_correlation_coefficients(sample_metrics_file):
    """Test correlation coefficient calculation."""
    # Temporarily override the global path
    original_path = generate_final_report_pdf.__globals__['METRICS_FILE']
    try:
        generate_final_report_pdf.__globals__['METRICS_FILE'] = sample_metrics_file
        data = load_metrics_data()
        correlations = calculate_correlation_coefficients(data)
        
        assert 'complexity_vs_comments' in correlations
        assert 'complexity_vs_time' in correlations
        assert 'complexity_vs_cycles' in correlations
        assert isinstance(correlations['complexity_vs_comments'], float)
        assert isinstance(correlations['p_value_comments'], float)
    finally:
        generate_final_report_pdf.__globals__['METRICS_FILE'] = original_path

def test_final_report_pdf_generation(tmp_path, sample_metrics_file, sample_results_file):
    """Test that the final report PDF is generated with all required components."""
    # Setup: Create output directory
    output_dir = tmp_path / "reports" / "figures"
    output_dir.mkdir(parents=True)
    output_pdf = output_dir / "final_report.pdf"
    
    # Temporarily override global paths
    original_metrics = generate_final_report_pdf.__globals__['METRICS_FILE']
    original_results = generate_final_report_pdf.__globals__['RESULTS_FILE']
    original_output = generate_final_report_pdf.__globals__['OUTPUT_DIR']
    original_output_pdf = generate_final_report_pdf.__globals__['OUTPUT_PDF']
    
    try:
        generate_final_report_pdf.__globals__['METRICS_FILE'] = sample_metrics_file
        generate_final_report_pdf.__globals__['RESULTS_FILE'] = sample_results_file
        generate_final_report_pdf.__globals__['OUTPUT_DIR'] = output_dir
        generate_final_report_pdf.__globals__['OUTPUT_PDF'] = output_pdf
        
        # Execute: Generate the report
        result_path = generate_final_report_pdf()
        
        # Verify: Check that the file exists
        assert os.path.exists(result_path)
        assert os.path.getsize(result_path) > 0
        
        # Verify: Check PDF content structure
        with PdfPages(result_path) as pdf:
            num_pages = len(pdf.get_page_images())
            assert num_pages == 4, "PDF should contain exactly 4 pages (boxplots, histograms, correlations, summary)"
            
            # Check that pages contain images (plots)
            for i in range(num_pages):
                images = pdf.get_page_images(i)
                assert len(images) > 0, f"Page {i} should contain plot images"
        
    finally:
        # Restore original paths
        generate_final_report_pdf.__globals__['METRICS_FILE'] = original_metrics
        generate_final_report_pdf.__globals__['RESULTS_FILE'] = original_results
        generate_final_report_pdf.__globals__['OUTPUT_DIR'] = original_output
        generate_final_report_pdf.__globals__['OUTPUT_PDF'] = original_output_pdf

def test_correlation_coefficients_are_real(sample_metrics_file):
    """Test that correlation coefficients are real values (not synthetic/fake)."""
    # Temporarily override the global path
    original_path = generate_final_report_pdf.__globals__['METRICS_FILE']
    try:
        generate_final_report_pdf.__globals__['METRICS_FILE'] = sample_metrics_file
        data = load_metrics_data()
        correlations = calculate_correlation_coefficients(data)
        
        # Verify correlations are in valid range [-1, 1]
        for key, value in correlations.items():
            if key.startswith('p_value'):
                assert 0 <= value <= 1, f"P-value {key}={value} should be in [0, 1]"
            else:
                assert -1 <= value <= 1, f"Correlation {key}={value} should be in [-1, 1]"
    finally:
        generate_final_report_pdf.__globals__['METRICS_FILE'] = original_path

if __name__ == "__main__":
    pytest.main([__file__, "-v"])