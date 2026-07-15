import os
import sys
import json
import tempfile
import shutil
import pytest

# Ensure code directory is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.main import parse_args, validate_args, generate_sample_sizes, generate_conditions

class TestMainPipelineLogic:
    """Tests for the parameter loop logic in code/main.py (T014b)"""

    def test_generate_sample_sizes_range(self):
        """Verify n=5..500 with step 5 generates correct list"""
        sizes = generate_sample_sizes(5, 500, 5)
        assert sizes[0] == 5
        assert sizes[-1] == 500
        assert len(sizes) == 100  # (500-5)/5 + 1
        assert sizes[1] == 10
        assert sizes[-2] == 495

    def test_generate_conditions_cross_product(self):
        """Verify conditions loop over n, effect sizes, and hypothesis"""
        sample_sizes = [5, 10]
        effect_sizes = [0.2, 0.5]
        test_type = 't-test'
        hypothesis = 'H1'
        alpha = 0.05

        conditions = generate_conditions(sample_sizes, effect_sizes, test_type, hypothesis, alpha)
        
        # 2 sample sizes * 2 effect sizes = 4 conditions
        assert len(conditions) == 4
        
        # Check structure
        for cond in conditions:
            assert cond['test_type'] == test_type
            assert cond['hypothesis'] == hypothesis
            assert cond['alpha'] == alpha
            assert cond['n'] in sample_sizes
            assert cond['effect_size'] in effect_sizes

    def test_validate_iterations_minimum(self):
        """Verify validation enforces >= 10,000 iterations (FR-001)"""
        args = parse_args()
        args.min_n = 5
        args.max_n = 500
        args.step_n = 5
        args.effect_size = "0.2"
        args.hypothesis = "H1"
        args.iterations = 10000  # Valid
        args.alpha = 0.05
        args.mode = "simulation"
        args.seed = 42
        
        # Should not raise
        validate_args(args)

        args.iterations = 9999  # Invalid
        with pytest.raises(ValueError) as excinfo:
            validate_args(args)
        assert "at least 10,000" in str(excinfo.value)

    def test_full_parameter_loop_coverage(self):
        """Verify the full grid is generated for the specified range"""
        # Simulate the exact loop from T014b: n=5..500 (step 5), effect sizes 0.2,0.5,0.8
        sample_sizes = generate_sample_sizes(5, 500, 5)
        effect_sizes = [0.2, 0.5, 0.8]
        conditions = generate_conditions(sample_sizes, effect_sizes, 't-test', 'H1', 0.05)
        
        expected_count = len(sample_sizes) * len(effect_sizes)
        assert len(conditions) == expected_count
        
        # Verify specific edge cases exist
        n_5_exists = any(c['n'] == 5 for c in conditions)
        n_500_exists = any(c['n'] == 500 for c in conditions)
        es_02_exists = any(c['effect_size'] == 0.2 for c in conditions)
        es_08_exists = any(c['effect_size'] == 0.8 for c in conditions)
        
        assert n_5_exists
        assert n_500_exists
        assert es_02_exists
        assert es_08_exists
