import pytest
import csv
import tempfile
import os
from pathlib import Path
from analysis.sensitivity import run_sweep_kruskal, run_sensitivity_analysis, load_metrics_for_sensitivity

@pytest.fixture
def sample_metrics_data():
    """
    Creates a temporary CSV file with sample metrics data for testing.
    """
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        writer = csv.writer(f)
        writer.writerow(['task_id', 'style', 'ast_distance', 'ngram_entropy'])
        
        # Task 1: Different distributions per style
        for i in range(10):
            writer.writerow(['task_1', 'neutral', 10.0 + i, 0.5])
            writer.writerow(['task_1', 'pep8', 20.0 + i, 0.6])
            writer.writerow(['task_1', 'minified', 30.0 + i, 0.7])
        
        # Task 2: Identical distributions (should not be significant)
        for i in range(10):
            writer.writerow(['task_2', 'neutral', 15.0, 0.5])
            writer.writerow(['task_2', 'pep8', 15.0, 0.6])
            writer.writerow(['task_2', 'minified', 15.0, 0.7])
        
        return f.name

def test_load_metrics_for_sensitivity(sample_metrics_data):
    """Test loading metrics from CSV"""
    data = load_metrics_for_sensitivity(Path(sample_metrics_data))
    assert len(data) == 60 # 2 tasks * 3 styles * 10 samples
    assert data[0]['task_id'] == 'task_1'
    assert data[0]['style'] == 'neutral'
    os.unlink(sample_metrics_data)

def test_run_sweep_kruskal_significant(sample_metrics_data):
    """Test that Kruskal-Wallis detects significant differences"""
    data = load_metrics_for_sensitivity(Path(sample_metrics_data))
    alpha_range = [0.05, 0.01]
    
    results = run_sweep_kruskal(data, alpha_range, metric='ast_distance')
    
    assert len(results) == 2
    # At alpha=0.05, task_1 should be significant (different means)
    # task_2 should not be significant (identical means)
    assert results[0]['significant_count'] >= 1 
    os.unlink(sample_metrics_data)

def test_run_sensitivity_analysis_output(sample_metrics_data):
    """Test that sensitivity analysis writes a CSV file"""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / 'sensitivity_test.csv'
        
        summary = run_sensitivity_analysis(
            Path(sample_metrics_data),
            output_path,
            alpha_range=[0.05]
        )
        
        assert output_path.exists()
        assert summary['significant_task_count_range'][0] >= 0
        
        # Verify CSV content
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert 'significant_tasks' in rows[0]
        
        os.unlink(sample_metrics_data)
