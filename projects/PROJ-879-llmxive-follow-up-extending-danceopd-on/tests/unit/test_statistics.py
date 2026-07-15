"""
Unit tests for statistical analysis functions in utils/statistics.py
"""
import pytest
import numpy as np
import pandas as pd
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import time
import signal

from utils.statistics import (
    calculate_effect_size,
    bootstrap_power_analysis,
    run_bootstrap_test,
    TimeoutError
)


class TestCalculateEffectSize:
    """Tests for calculate_effect_size function."""
    
    def test_effect_size_positive(self):
        """Test effect size calculation with positive difference."""
        group1 = np.array([10, 12, 11, 13, 12])
        group2 = np.array([8, 9, 7, 8, 9])
        
        effect_size = calculate_effect_size(group1, group2)
        
        assert effect_size > 0
        assert isinstance(effect_size, float)
    
    def test_effect_size_negative(self):
        """Test effect size calculation with negative difference."""
        group1 = np.array([8, 9, 7, 8, 9])
        group2 = np.array([10, 12, 11, 13, 12])
        
        effect_size = calculate_effect_size(group1, group2)
        
        assert effect_size < 0
        assert isinstance(effect_size, float)
    
    def test_effect_size_zero(self):
        """Test effect size calculation with identical groups."""
        group = np.array([10, 12, 11, 13, 12])
        
        effect_size = calculate_effect_size(group, group)
        
        assert effect_size == 0.0
    
    def test_effect_size_with_zero_variance(self):
        """Test effect size when one group has zero variance."""
        group1 = np.array([10, 10, 10, 10, 10])
        group2 = np.array([8, 9, 7, 8, 9])
        
        effect_size = calculate_effect_size(group1, group2)
        
        # Should not raise an error
        assert isinstance(effect_size, float)


class TestBootstrapPowerAnalysis:
    """Tests for bootstrap_power_analysis function."""
    
    def test_basic_power_analysis(self):
        """Test basic power analysis with small sample."""
        np.random.seed(42)
        teacher_scores = np.random.normal(10, 2, 100)
        tree_scores = np.random.normal(12, 2, 100)
        
        results = bootstrap_power_analysis(
            fid_scores_teacher=teacher_scores,
            fid_scores_tree=tree_scores,
            target_power=0.5,  # Lower target for faster test
            bootstrap_iterations=100,  # Fewer iterations for speed
            min_samples=10,
            sample_increment=5,
            time_budget_seconds=60.0
        )
        
        assert "status" in results
        assert "final_power" in results
        assert "final_p_value" in results
        assert "history" in results
        assert results["final_sample_size"] >= 10
    
    def test_complete_status_when_power_reached(self):
        """Test that status is 'complete' when power target is reached."""
        np.random.seed(42)
        # Create data with large effect size
        teacher_scores = np.random.normal(5, 1, 200)
        tree_scores = np.random.normal(15, 1, 200)
        
        results = bootstrap_power_analysis(
            fid_scores_teacher=teacher_scores,
            fid_scores_tree=tree_scores,
            target_power=0.8,
            bootstrap_iterations=100,
            min_samples=10,
            sample_increment=10,
            time_budget_seconds=300.0
        )
        
        # With large effect size, should reach power target
        assert results["status"] == "complete" or results["final_power"] >= 0.8
    
    def test_insufficient_samples(self):
        """Test behavior when sample size is below minimum."""
        teacher_scores = np.random.normal(10, 2, 5)
        tree_scores = np.random.normal(12, 2, 5)
        
        results = bootstrap_power_analysis(
            fid_scores_teacher=teacher_scores,
            fid_scores_tree=tree_scores,
            min_samples=10,
            bootstrap_iterations=10
        )
        
        assert results["status"] == "error"
        assert "below minimum" in results["message"]
    
    def test_empty_history_on_error(self):
        """Test that history is empty when error occurs."""
        teacher_scores = np.random.normal(10, 2, 5)
        tree_scores = np.random.normal(12, 2, 5)
        
        results = bootstrap_power_analysis(
            fid_scores_teacher=teacher_scores,
            fid_scores_tree=tree_scores,
            min_samples=10,
            bootstrap_iterations=10
        )
        
        assert len(results["history"]) == 0


class TestRunBootstrapTest:
    """Tests for run_bootstrap_test function."""
    
    def test_run_with_valid_csv(self):
        """Test running bootstrap test with valid CSV file."""
        np.random.seed(42)
        
        # Create temporary CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({
                'teacher_fid': np.random.normal(10, 2, 50),
                'tree_fid': np.random.normal(12, 2, 50)
            })
            df.to_csv(f.name, index=False)
            csv_path = f.name
        
        # Create temporary output file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name
        
        try:
            results = run_bootstrap_test(
                fid_data_path=csv_path,
                output_path=output_path,
                time_budget_seconds=60.0
            )
            
            assert "status" in results
            assert os.path.exists(output_path)
            
            # Verify output file contains valid JSON
            with open(output_path, 'r') as f:
                saved_results = json.load(f)
                assert saved_results == results
        finally:
            os.unlink(csv_path)
            os.unlink(output_path)
    
    def test_missing_columns_raises_error(self):
        """Test that missing required columns raises ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({
                'wrong_col1': [1, 2, 3],
                'wrong_col2': [4, 5, 6]
            })
            df.to_csv(f.name, index=False)
            csv_path = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name
        
        try:
            with pytest.raises(ValueError, match="must contain"):
                run_bootstrap_test(
                    fid_data_path=csv_path,
                    output_path=output_path,
                    time_budget_seconds=60.0
                )
        finally:
            os.unlink(csv_path)
            os.unlink(output_path)
    
    def test_nan_values_filtered(self):
        """Test that NaN values are filtered out."""
        np.random.seed(42)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({
                'teacher_fid': [10, np.nan, 12, 11, np.nan],
                'tree_fid': [12, 13, np.nan, 14, 15]
            })
            df.to_csv(f.name, index=False)
            csv_path = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name
        
        try:
            results = run_bootstrap_test(
                fid_data_path=csv_path,
                output_path=output_path,
                time_budget_seconds=60.0
            )
            
            # Should complete without error
            assert "status" in results
        finally:
            os.unlink(csv_path)
            os.unlink(output_path)


class TestTimeoutHandling:
    """Tests for timeout handling in statistical tests."""
    
    def test_timeout_error_raised(self):
        """Test that TimeoutError is raised when timeout occurs."""
        from utils.statistics import timeout_handler, TimeoutError
        
        # Mock signal handler
        with patch('signal.SIGALRM'):
            try:
                timeout_handler(None, None)
                assert False, "TimeoutError should have been raised"
            except TimeoutError:
                pass  # Expected
    
    def test_partial_results_on_timeout(self, tmp_path):
        """Test that partial results are saved on timeout."""
        np.random.seed(42)
        
        # Create CSV
        csv_path = tmp_path / "fid_data.csv"
        df = pd.DataFrame({
            'teacher_fid': np.random.normal(10, 2, 100),
            'tree_fid': np.random.normal(12, 2, 100)
        })
        df.to_csv(csv_path, index=False)
        
        output_path = tmp_path / "results.json"
        partial_path = tmp_path / "partial_results.json"
        
        # Mock time to simulate timeout
        with patch('time.time', side_effect=[0, 0, 0, 10000]):  # First 3 calls normal, then large
            with patch('utils.statistics.bootstrap_power_analysis', return_value={
                'status': 'timeout',
                'message': 'Test timeout'
            }):
                try:
                    run_bootstrap_test(
                        fid_data_path=str(csv_path),
                        output_path=str(output_path),
                        time_budget_seconds=1.0
                    )
                except SystemExit as e:
                    assert e.code == 2
                
                # Check partial results file exists
                assert partial_path.exists()
                
                with open(partial_path, 'r') as f:
                    partial_data = json.load(f)
                    assert partial_data['status'] == 'timeout'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
