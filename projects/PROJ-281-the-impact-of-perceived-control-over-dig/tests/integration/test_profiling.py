import os
import tempfile
import time
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from code.profiling import (
    run_profiling_pipeline,
    save_report,
    RuntimeLimitExceededError,
    get_memory_usage_gb,
    get_peak_memory_gb
)
from code.config import CONFIG

class TestProfiling:
    """Integration tests for the profiling pipeline."""
    
    @pytest.fixture
    def sample_data_file(self, tmp_path):
        """Create a temporary CSV file with sample data."""
        data = {
            'text': ['Sample text ' + str(i) for i in range(100)],
            'anxiety_score': np.random.rand(100),
            'control_proxy': np.random.rand(100),
            'confidence_score': np.random.rand(100)
        }
        df = pd.DataFrame(data)
        file_path = tmp_path / "test_data.csv"
        df.to_csv(file_path, index=False)
        return str(file_path)
    
    @pytest.fixture
    def large_sample_data_file(self, tmp_path):
        """Create a larger temporary CSV file to test runtime limits."""
        # Create a dataset that would take a long time to process if we had real heavy computation
        n_rows = 10000
        data = {
            'text': ['Sample text ' + str(i) for i in range(n_rows)],
            'anxiety_score': np.random.rand(n_rows),
            'control_proxy': np.random.rand(n_rows),
            'confidence_score': np.random.rand(n_rows)
        }
        df = pd.DataFrame(data)
        file_path = tmp_path / "large_test_data.csv"
        df.to_csv(file_path, index=False)
        return str(file_path)
    
    def test_profiling_basic_functionality(self, sample_data_file, tmp_path):
        """Test basic profiling functionality with small dataset."""
        output_path = str(tmp_path / "test_report.md")
        
        results = run_profiling_pipeline(
            input_data_path=sample_data_file,
            runtime_limit_hours=1.0,
            min_sample_size=100
        )
        
        # Verify results structure
        assert 'input_file' in results
        assert 'runtime_limit_hours' in results
        assert 'final_status' in results
        assert 'attempts' in results
        assert 'sample_size' in results
        
        # Verify successful completion
        assert results['final_status'] == 'completed'
        assert len(results['attempts']) >= 1
        
        # Verify report generation
        save_report(results, output_path)
        assert os.path.exists(output_path)
        
        # Verify report content
        with open(output_path, 'r') as f:
            content = f.read()
            assert 'Runtime Performance Report' in content
            assert 'Sample Size' in content
            assert 'Total Runtime' in content
    
    def test_profiling_runtime_limit_handling(self, large_sample_data_file, tmp_path):
        """Test handling of runtime limit with a dataset that might exceed limits."""
        # Use a very short limit to simulate timeout
        output_path = str(tmp_path / "timeout_report.md")
        
        results = run_profiling_pipeline(
            input_data_path=large_sample_data_file,
            runtime_limit_hours=0.0001,  # Very short limit (0.36 seconds)
            min_sample_size=1000
        )
        
        # The result should either complete quickly or handle the timeout
        assert 'final_status' in results
        assert len(results['attempts']) >= 1
        
        # If it timed out, it should have attempted reduction
        if results['final_status'] == 'runtime_limit_exceeded' or results['final_status'] == 'completed_with_sample_reduction':
            assert any(a.get('reduction_applied', False) for a in results['attempts'])
        
        # Verify report generation
        save_report(results, output_path)
        assert os.path.exists(output_path)
    
    def test_profiling_memory_tracking(self, sample_data_file):
        """Test that memory usage is tracked correctly."""
        results = run_profiling_pipeline(
            input_data_path=sample_data_file,
            runtime_limit_hours=1.0
        )
        
        assert 'peak_memory_gb' in results
        assert results['peak_memory_gb'] >= 0
    
    def test_profiling_with_nonexistent_file(self, tmp_path):
        """Test error handling for non-existent input file."""
        fake_path = str(tmp_path / "nonexistent.csv")
        
        with pytest.raises(FileNotFoundError):
            run_profiling_pipeline(input_data_path=fake_path)
    
    def test_profiling_ms_per_row_calculation(self, sample_data_file):
        """Test that ms_per_row is calculated correctly."""
        results = run_profiling_pipeline(
            input_data_path=sample_data_file,
            runtime_limit_hours=1.0
        )
        
        if results['final_status'] == 'completed' and results['sample_size'] > 0:
            assert results['ms_per_row'] is not None
            assert results['ms_per_row'] >= 0
            
            # Verify calculation
            expected_ms_per_row = (results['total_runtime_seconds'] * 1000) / results['sample_size']
            assert abs(results['ms_per_row'] - expected_ms_per_row) < 0.001
    
    def test_save_report_format(self, sample_data_file, tmp_path):
        """Test the format of the saved report."""
        output_path = str(tmp_path / "format_test.md")
        
        results = run_profiling_pipeline(
            input_data_path=sample_data_file,
            runtime_limit_hours=1.0
        )
        
        save_report(results, output_path)
        
        with open(output_path, 'r') as f:
            content = f.read()
            
        # Verify key sections exist
        assert '# Runtime Performance Report' in content
        assert '## Summary' in content
        assert '## Attempt Details' in content
        assert 'Generated' in content
        assert 'Input File' in content
        assert 'Runtime Limit' in content
        assert 'Final Status' in content
        assert 'Sample Size' in content
        assert 'Total Runtime' in content
        assert 'Peak Memory Usage' in content
    
    def test_profiling_with_sample_reduction(self, large_sample_data_file, tmp_path):
        """Test that sample reduction works when runtime limit is exceeded."""
        output_path = str(tmp_path / "reduction_report.md")
        
        # Set a very low limit to force reduction
        results = run_profiling_pipeline(
            input_data_path=large_sample_data_file,
            runtime_limit_hours=0.00001,  # Extremely short
            min_sample_size=100
        )
        
        # Should either complete with reduction or fail gracefully
        assert 'final_status' in results
        assert 'attempts' in results
        
        # If reduction was applied, verify the sample size
        if results['sample_reduction_applied']:
            assert results['sample_size'] == 100
            assert results['final_status'] == 'completed_with_sample_reduction'
    
    def test_profiling_integration_with_config(self, sample_data_file):
        """Test profiling integration with configuration settings."""
        # Use config values
        limit_hours = 6.0  # Default from config
        
        results = run_profiling_pipeline(
            input_data_path=sample_data_file,
            runtime_limit_hours=limit_hours
        )
        
        assert results['runtime_limit_hours'] == limit_hours
        assert results['final_status'] in ['completed', 'failed']
    
    def test_profiling_empty_dataset_handling(self, tmp_path):
        """Test handling of empty dataset."""
        empty_path = str(tmp_path / "empty.csv")
        pd.DataFrame(columns=['text', 'anxiety_score']).to_csv(empty_path, index=False)
        
        results = run_profiling_pipeline(
            input_data_path=empty_path,
            runtime_limit_hours=1.0
        )
        
        # Should handle empty dataset gracefully
        assert 'final_status' in results
        # The exact status depends on implementation, but it shouldn't crash
    
    def test_profiling_report_contains_required_fields(self, sample_data_file, tmp_path):
        """Ensure the report contains all required fields per task specification."""
        output_path = str(tmp_path / "required_fields_report.md")
        
        results = run_profiling_pipeline(
            input_data_path=sample_data_file,
            runtime_limit_hours=1.0
        )
        
        save_report(results, output_path)
        
        with open(output_path, 'r') as f:
            content = f.read()
            
        # Required fields from task specification
        required_fields = [
            'runtime_limit_hours',
            'final_status',
            'sample_size',
            'sample_reduction_applied',
            'total_runtime_seconds',
            'ms_per_row',
            'peak_memory_gb'
        ]
        
        for field in required_fields:
            # Check if field is mentioned in the report
            # Note: The report format uses human-readable labels, so we check for the concept
            if field == 'runtime_limit_hours':
                assert 'Runtime Limit' in content
            elif field == 'final_status':
                assert 'Final Status' in content
            elif field == 'sample_size':
                assert 'Sample Size' in content
            elif field == 'sample_reduction_applied':
                assert 'Sample Reduction Applied' in content
            elif field == 'total_runtime_seconds':
                assert 'Total Runtime' in content
            elif field == 'ms_per_row':
                assert 'Milliseconds per Row' in content
            elif field == 'peak_memory_gb':
                assert 'Peak Memory Usage' in content