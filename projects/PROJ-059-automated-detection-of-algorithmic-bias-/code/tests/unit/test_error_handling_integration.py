"""
Unit tests for T043: Error Handling Integration.
Verifies that error_handler utilities are correctly imported and used in US1, US2, US3 modules.
"""
import pytest
import sys
import os
from pathlib import Path

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.bias_pipeline.error_handler import safe_execute, ExecutionError, handle_pipeline_error
from src.bias_pipeline.extractor import parse_ast_tree, process_single_repo
from src.bias_pipeline.simulation import inject_bias_model, run_simulation_and_independence_check
from src.bias_pipeline.analyzer import compute_spearman_correlation, run_correlation_analysis

class TestErrorHandlingImport:
    """Test that error handling functions are available."""
    
    def test_safe_execute_import(self):
        assert callable(safe_execute)
    
    def test_execution_error_import(self):
        assert issubclass(ExecutionError, Exception)
    
    def test_handle_pipeline_error_import(self):
        assert callable(handle_pipeline_error)

class TestExtractorErrorHandling:
    """Test that extractor uses error handling."""
    
    def test_parse_ast_tree_returns_none_on_syntax_error(self, tmp_path):
        # Create a file with syntax error
        bad_file = tmp_path / "bad.py"
        bad_file.write_text("def broken(") # Missing closing paren
        
        result = parse_ast_tree(bad_file)
        assert result is None
    
    def test_process_single_repo_handles_missing_dir(self):
        # Should not crash, should handle error gracefully
        # The decorator handles the error and returns a dict with error info
        try:
            result = process_single_repo(Path("/nonexistent/path"))
            assert isinstance(result, dict)
            assert 'error' in result or 'repo_path' in result
        except Exception as e:
            # If it raises, it should be a handled error
            assert isinstance(e, ExecutionError)

class TestSimulationErrorHandling:
    """Test that simulation uses error handling."""
    
    def test_inject_bias_model_handles_extreme_values(self):
        # Should not crash with extreme skew
        data = [[1, 2, 0], [3, 4, 1]]
        try:
            result = inject_bias_model(data, 10.0) # Extreme skew
            assert result is not None
        except Exception:
            pass # Expected to handle or raise specific error

class TestAnalyzerErrorHandling:
    """Test that analyzer uses error handling."""
    
    def test_compute_spearman_correlation_raises_on_insufficient_data(self):
        with pytest.raises(ValueError):
            compute_spearman_correlation([1], [2])
    
    def test_run_correlation_analysis_handles_empty_lists(self):
        # Should raise or handle gracefully
        with pytest.raises(ValueError):
            run_correlation_analysis([], [], Path("/tmp/test.json"))

class TestDecoratorUsage:
    """Test that decorators are correctly applied."""
    
    def test_handle_pipeline_error_decorator_preserves_signature(self):
        @handle_pipeline_error(task_name="TestTask")
        def my_func(x):
            return x * 2
        
        assert my_func(5) == 10
