import pytest
import os
import sys
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from run_analysis import parse_args, pin_orchestration_seed
import argparse

class TestParseArgs:
    def test_default_values(self):
        """Test default argument values."""
        # Simulate no arguments
        sys.argv = ['run_analysis.py']
        args = parse_args()
        
        assert args.N == 1000000
        assert args.primes == [3, 5, 7, 11]
        assert args.seed == 42
        assert args.memory_limit_mb == 6000
        assert args.memory_check_interval == 10000

    def test_custom_values(self):
        """Test custom argument values."""
        sys.argv = [
            'run_analysis.py',
            '--N', '5000000',
            '--primes', '3', '5',
            '--seed', '123',
            '--memory-limit-mb', '4000'
        ]
        args = parse_args()
        
        assert args.N == 5000000
        assert args.primes == [3, 5]
        assert args.seed == 123
        assert args.memory_limit_mb == 4000

class TestPinSeed:
    def test_seed_pinning(self):
        """Test that seed pinning works."""
        pin_orchestration_seed(42)
        
        # Verify seeds are set (basic check)
        import random
        import numpy as np
        
        # Generate a value to verify seed is active
        val1 = random.random()
        val2 = np.random.random()
        
        # Reset and regenerate
        pin_orchestration_seed(42)
        val3 = random.random()
        val4 = np.random.random()
        
        # Should be identical
        assert val1 == val3
        assert val2 == val4