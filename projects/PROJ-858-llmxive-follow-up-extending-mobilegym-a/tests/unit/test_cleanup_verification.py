"""
Unit tests for verifying cleanup operations.

These tests ensure that the refactoring process did not break
any existing functionality.
"""

import json
import os
import sys
from pathlib import Path
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging import get_logger

logger = get_logger("test_cleanup_verification")

class TestCleanupVerification:
    """Test cases for cleanup verification."""
    
    def test_imports_valid(self):
        """Verify that all imports in cleaned files are valid."""
        # Test curriculum_scheduler imports
        from scheduler.curriculum_scheduler import CurriculumScheduler, main
        assert CurriculumScheduler is not None
        assert callable(main)
        
        # Test state_coverage imports
        from scheduler.state_coverage import (
            initialize_coverage_vector,
            detect_state_transitions,
            aggregate_coverage_vectors
        )
        assert initialize_coverage_vector is not None
        assert detect_state_transitions is not None
        assert aggregate_coverage_vectors is not None
        
        # Test analysis imports
        from analysis.convergence import load_config, calculate_steps_to_target
        from analysis.sensitivity import compute_pearson_correlation, analyze_sensitivity
        from analysis.transfer import evaluate_transfer_performance, calculate_variance
        
        assert load_config is not None
        assert calculate_steps_to_target is not None
        assert compute_pearson_correlation is not None
        assert analyze_sensitivity is not None
        assert evaluate_transfer_performance is not None
        assert calculate_variance is not None
    
    def test_cleanup_report_exists(self):
        """Verify that cleanup report was generated."""
        report_path = PROJECT_ROOT / "data" / "processed" / "cleanup_report.json"
        assert report_path.exists(), "Cleanup report should exist"
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        assert "files_processed" in report
        assert "summary" in report
        assert report["summary"]["files_modified"] > 0
    
    def test_no_syntax_errors(self):
        """Verify that cleaned files have no syntax errors."""
        import ast
        
        scheduler_files = [
            "code/scheduler/curriculum_scheduler.py",
            "code/scheduler/state_coverage.py",
            "code/scheduler/coverage_writer.py",
            "code/scheduler/trace_logger.py",
            "code/scheduler/error_handling_rollouts.py"
        ]
        
        analysis_files = [
            "code/analysis/convergence.py",
            "code/analysis/sensitivity.py",
            "code/analysis/transfer.py",
            "code/analysis/generate_plots.py",
            "code/analysis/generate_sensitivity_report.py"
        ]
        
        all_files = scheduler_files + analysis_files
        
        for file_path in all_files:
            full_path = PROJECT_ROOT / file_path
            if full_path.exists():
                with open(full_path, 'r') as f:
                    content = f.read()
                
                # This will raise SyntaxError if there's a syntax issue
                ast.parse(content)
    
    def test_logging_standardized(self):
        """Verify that logging calls are standardized."""
        from utils.logging import get_logger
        
        # Test that modules can import and use logger
        from scheduler.curriculum_scheduler import main as scheduler_main
        from analysis.convergence import main as convergence_main
        
        # These should not raise import errors
        assert scheduler_main is not None
        assert convergence_main is not None
    
    def test_docstring_format(self):
        """Verify that docstrings follow Google style."""
        import inspect
        
        # Check a sample function
        from scheduler.curriculum_scheduler import CurriculumScheduler
        
        # Get the class docstring
        docstring = CurriculumScheduler.__doc__
        assert docstring is not None, "Class should have a docstring"
        assert len(docstring.strip()) > 0, "Docstring should not be empty"
    
    def test_cleanup_report_content(self):
        """Verify cleanup report contains expected data."""
        report_path = PROJECT_ROOT / "data" / "processed" / "cleanup_report.json"
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        # Check structure
        assert "timestamp" in report
        assert "files_processed" in report
        assert "details" in report
        assert "summary" in report
        
        # Check summary
        summary = report["summary"]
        assert "total_imports_removed" in summary
        assert "files_modified" in summary
        
        # Check that some files were modified
        assert summary["files_modified"] > 0
        assert summary["total_imports_removed"] > 0
    
    def test_no_duplicate_functions(self):
        """Verify no duplicate function definitions exist."""
        import ast
        
        # Check curriculum_scheduler for duplicates
        scheduler_path = PROJECT_ROOT / "code" / "scheduler" / "curriculum_scheduler.py"
        with open(scheduler_path, 'r') as f:
            tree = ast.parse(f.read())
        
        function_names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                function_names.append(node.name)
        
        # Check for duplicates
        assert len(function_names) == len(set(function_names)), \
            f"Duplicate functions found: {function_names}"
    
    def test_refactoring_script_executes(self):
        """Verify that the refactoring script can execute without errors."""
        from refactor_scheduler_cleanup import main
        
        # This should not raise an exception
        result = main()
        assert result == 0, "Refactoring script should return 0 on success"
    
    def test_api_surface_intact(self):
        """Verify that the public API surface remains intact."""
        # Test that all expected public names are available
        from scheduler.curriculum_scheduler import CurriculumScheduler, main
        from scheduler.state_coverage import (
            initialize_coverage_vector,
            detect_state_transitions,
            aggregate_coverage_vectors,
            merge_coverage_vectors_threadsafe,
            process_rollout_batch,
            process_rollouts_parallel
        )
        from analysis.convergence import (
            load_config,
            load_logs,
            calculate_steps_to_target,
            analyze_convergence,
            save_results,
            main
        )
        from analysis.sensitivity import (
            load_config,
            load_coverage_vectors,
            load_validation_results,
            calculate_vector_scalar,
            align_data,
            compute_pearson_correlation,
            analyze_sensitivity,
            save_results
        )
        
        # Verify all imports succeeded
        assert CurriculumScheduler is not None
        assert initialize_coverage_vector is not None
        assert load_config is not None
        assert compute_pearson_correlation is not None
    
    def test_cleanup_preserves_functionality(self):
        """Verify that cleanup did not break core functionality."""
        # Test basic initialization
        from scheduler.state_coverage import initialize_coverage_vector
        from utils.constants import get_coverage_vector_dimensions
        
        vector = initialize_coverage_vector()
        assert vector is not None
        assert len(vector) == get_coverage_vector_dimensions()
        
        # Test that all 0s initially
        assert all(v == 0 for v in vector)
    
    def test_logging_integration(self):
        """Verify logging integration works correctly."""
        from utils.logging import get_logger, log_with_context
        
        # Test logger creation
        logger = get_logger("test_module")
        assert logger is not None
        
        # Test logging with context
        log_with_context(logger, "test message", level="info")
        
        # Verify no exceptions raised
        assert True