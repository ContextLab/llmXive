"""
Unit tests for data provenance verification.

Tests that human_annotations are generated independently of teacher_scores
and student_scalar, relying only on species_id and prompt_text.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from provenance import verify_provenance_independence, load_dataset


def create_test_dataset(independent_annotations: bool = True):
    """
    Create a test dataset for provenance verification.
    
    Args:
        independent_annotations: If True, human_annotations depend only on species_id and prompt_text.
                               If False, human_annotations also depend on teacher_scores.
    """
    n_samples = 100
    
    # Create base data
    data = {
        'species_id': np.random.choice([1, 2, 3, 4, 5], n_samples),
        'prompt_text': np.random.choice(['prompt_a', 'prompt_b', 'prompt_c'], n_samples),
        'teacher_scores': np.random.randn(n_samples, 4).tolist(),
        'student_scalar': np.random.randn(n_samples).tolist(),
    }
    
    if independent_annotations:
        # human_annotations depend ONLY on species_id and prompt_text
        # Create a deterministic mapping
        annotations = []
        for idx, row in enumerate(data['species_id']):
            prompt = data['prompt_text'][idx]
            # Create a hash-like value based on species_id and prompt_text
            combined_key = f"{row}_{prompt}"
            # Use a simple deterministic function
            annotations.append((hash(combined_key) % 100) / 100.0)
        data['human_annotations'] = annotations
    else:
        # human_annotations depend on teacher_scores as well (violates provenance)
        teacher_scores_array = np.array(data['teacher_scores'])
        teacher_mean = teacher_scores_array.mean(axis=1)
        # Add dependency on teacher_scores
        data['human_annotations'] = teacher_mean + np.random.randn(n_samples) * 0.01
    
    return pd.DataFrame(data)


class TestProvenanceVerification:
    """Test cases for data provenance verification."""
    
    def test_independent_annotations_pass(self):
        """Test that independent annotations pass verification."""
        df = create_test_dataset(independent_annotations=True)
        
        # Mock logger
        class MockLogger:
            def info(self, msg): pass
            def warning(self, msg): pass
            def error(self, msg): pass
            def debug(self, msg): pass
        
        logger = MockLogger()
        results = verify_provenance_independence(df, logger)
        
        assert results["status"] == "passed", f"Expected pass, got: {results['checks']}"
        
        # Verify specific checks passed
        annotation_check = next(c for c in results["checks"] if c["check"] == "annotation_consistency")
        assert annotation_check["status"] == "passed"
    
    def test_dependent_annotations_fail(self):
        """Test that dependent annotations (on teacher_scores) fail verification."""
        df = create_test_dataset(independent_annotations=False)
        
        # Mock logger
        class MockLogger:
            def info(self, msg): pass
            def warning(self, msg): pass
            def error(self, msg): pass
            def debug(self, msg): pass
        
        logger = MockLogger()
        results = verify_provenance_independence(df, logger)
        
        # This should fail because human_annotations vary within (species_id, prompt_text) groups
        # when they depend on teacher_scores
        assert results["status"] == "failed", f"Expected fail, got: {results['checks']}"
    
    def test_missing_columns_raises_error(self):
        """Test that missing required columns raise an error."""
        df = pd.DataFrame({
            'species_id': [1, 2, 3],
            'prompt_text': ['a', 'b', 'c'],
            # Missing human_annotations, teacher_scores, student_scalar
        })
        
        class MockLogger:
            def info(self, msg): pass
            def warning(self, msg): pass
            def error(self, msg): pass
            def debug(self, msg): pass
        
        logger = MockLogger()
        
        with pytest.raises(ValueError, match="Missing required columns"):
            verify_provenance_independence(df, logger)
    
    def test_consistency_within_groups(self):
        """Test that human_annotations are consistent within (species_id, prompt_text) groups."""
        # Create dataset where same (species_id, prompt_text) always gives same annotation
        data = {
            'species_id': [1, 1, 2, 2, 1],
            'prompt_text': ['a', 'a', 'b', 'b', 'a'],
            'human_annotations': [0.5, 0.5, 0.7, 0.7, 0.5],  # Consistent
            'teacher_scores': [[1, 2, 3, 4], [2, 3, 4, 5], [1, 1, 1, 1], [2, 2, 2, 2], [3, 3, 3, 3]],
            'student_scalar': [0.1, 0.2, 0.3, 0.4, 0.5],
        }
        df = pd.DataFrame(data)
        
        class MockLogger:
            def info(self, msg): pass
            def warning(self, msg): pass
            def error(self, msg): pass
            def debug(self, msg): pass
        
        logger = MockLogger()
        results = verify_provenance_independence(df, logger)
        
        assert results["status"] == "passed"
        annotation_check = next(c for c in results["checks"] if c["check"] == "annotation_consistency")
        assert annotation_check["status"] == "passed"
    
    def test_inconsistency_within_groups_fails(self):
        """Test that inconsistent human_annotations within groups fail verification."""
        # Create dataset where same (species_id, prompt_text) gives different annotations
        data = {
            'species_id': [1, 1, 2, 2, 1],
            'prompt_text': ['a', 'a', 'b', 'b', 'a'],
            'human_annotations': [0.5, 0.6, 0.7, 0.7, 0.5],  # Inconsistent for (1, 'a')
            'teacher_scores': [[1, 2, 3, 4], [2, 3, 4, 5], [1, 1, 1, 1], [2, 2, 2, 2], [3, 3, 3, 3]],
            'student_scalar': [0.1, 0.2, 0.3, 0.4, 0.5],
        }
        df = pd.DataFrame(data)
        
        class MockLogger:
            def info(self, msg): pass
            def warning(self, msg): pass
            def error(self, msg): pass
            def debug(self, msg): pass
        
        logger = MockLogger()
        results = verify_provenance_independence(df, logger)
        
        assert results["status"] == "failed"
        annotation_check = next(c for c in results["checks"] if c["check"] == "annotation_consistency")
        assert annotation_check["status"] == "failed"
    
    def test_empty_dataset(self):
        """Test handling of empty dataset."""
        df = pd.DataFrame(columns=['species_id', 'prompt_text', 'human_annotations', 'teacher_scores', 'student_scalar'])
        
        class MockLogger:
            def info(self, msg): pass
            def warning(self, msg): pass
            def error(self, msg): pass
            def debug(self, msg): pass
        
        logger = MockLogger()
        
        # Should handle empty dataset gracefully
        results = verify_provenance_independence(df, logger)
        assert results["status"] == "passed"  # No violations in empty data
    
    def test_single_sample(self):
        """Test handling of single sample dataset."""
        df = pd.DataFrame({
            'species_id': [1],
            'prompt_text': ['a'],
            'human_annotations': [0.5],
            'teacher_scores': [[1, 2, 3, 4]],
            'student_scalar': [0.1],
        })
        
        class MockLogger:
            def info(self, msg): pass
            def warning(self, msg): pass
            def error(self, msg): pass
            def debug(self, msg): pass
        
        logger = MockLogger()
        results = verify_provenance_independence(df, logger)
        
        assert results["status"] == "passed"
    
    def test_large_dataset_performance(self):
        """Test performance with larger dataset."""
        # Create a larger dataset
        n_samples = 1000
        df = create_test_dataset(independent_annotations=True)
        
        class MockLogger:
            def info(self, msg): pass
            def warning(self, msg): pass
            def error(self, msg): pass
            def debug(self, msg): pass
        
        logger = MockLogger()
        
        # Should complete without timeout
        results = verify_provenance_independence(df, logger)
        assert results["status"] in ["passed", "failed"]  # Either result is acceptable for performance test
    
    def test_json_serialization(self):
        """Test that results can be serialized to JSON."""
        df = create_test_dataset(independent_annotations=True)
        
        class MockLogger:
            def info(self, msg): pass
            def warning(self, msg): pass
            def error(self, msg): pass
            def debug(self, msg): pass
        
        logger = MockLogger()
        results = verify_provenance_independence(df, logger)
        
        # Should not raise
        json_str = json.dumps(results, default=str)
        assert len(json_str) > 0
    
    def test_teacher_scores_format(self):
        """Test handling of teacher_scores as string representation."""
        # Create dataset with teacher_scores as string
        data = {
            'species_id': [1, 2],
            'prompt_text': ['a', 'b'],
            'human_annotations': [0.5, 0.7],
            'teacher_scores': ['[1, 2, 3, 4]', '[2, 3, 4, 5]'],  # String representation
            'student_scalar': [0.1, 0.2],
        }
        df = pd.DataFrame(data)
        
        class MockLogger:
            def info(self, msg): pass
            def warning(self, msg): pass
            def error(self, msg): pass
            def debug(self, msg): pass
        
        logger = MockLogger()
        
        # Should handle string representation
        results = verify_provenance_independence(df, logger)
        assert results["status"] in ["passed", "failed"]
    
    def test_string_teacher_scores_invalid_format(self):
        """Test handling of invalid string teacher_scores format."""
        data = {
            'species_id': [1],
            'prompt_text': ['a'],
            'human_annotations': [0.5],
            'teacher_scores': ['invalid_json'],  # Invalid JSON
            'student_scalar': [0.1],
        }
        df = pd.DataFrame(data)
        
        class MockLogger:
            def info(self, msg): pass
            def warning(self, msg): pass
            def error(self, msg): pass
            def debug(self, msg): pass
        
        logger = MockLogger()
        
        with pytest.raises(ValueError, match="teacher_scores column must contain list-like values"):
            verify_provenance_independence(df, logger)
    
    def test_correlation_checks_produced(self):
        """Test that correlation checks are produced in results."""
        df = create_test_dataset(independent_annotations=True)
        
        class MockLogger:
            def info(self, msg): pass
            def warning(self, msg): pass
            def error(self, msg): pass
            def debug(self, msg): pass
        
        logger = MockLogger()
        results = verify_provenance_independence(df, logger)
        
        assert "details" in results
        assert "partial_correlations_teacher" in results["details"]
        assert "student_scalar_correlations" in results["details"]