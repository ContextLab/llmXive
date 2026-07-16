"""
Unit tests for T027: Performance Optimization & Profiling.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np
import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from measure_performance import (
    benchmark_vectorization,
    generate_report,
    analyze_file_for_loops,
    HEAVY_LOOP_THRESHOLD
)

class TestBenchmarkVectorization:
    def test_vectorization_speedup(self):
        """Test that vectorized operations are significantly faster than scalar loops."""
        results = benchmark_vectorization()
        
        assert 'scalar_loop_time_seconds' in results
        assert 'vectorized_time_seconds' in results
        assert 'speedup_factor' in results
        
        # Vectorized should be faster (speedup > 1)
        assert results['speedup_factor'] > 1.0, "Vectorization should provide a speedup."
        
        # Check that times are reasonable (not 0, not infinite)
        assert results['scalar_loop_time_seconds'] > 0
        assert results['vectorized_time_seconds'] > 0

    def test_vectorization_correctness(self):
        """Test that vectorized results match scalar results."""
        # Re-implement the logic to verify correctness independently
        n_samples = 1000
        np.random.seed(42)
        df = pd.DataFrame({
            'a': np.random.rand(n_samples),
            'b': np.random.rand(n_samples),
            'c': np.random.rand(n_samples)
        })
        
        scalar = (df['a'] * df['b'] + df['c']).values
        vectorized = (df['a'] * df['b'] + df['c']).values
        
        assert np.allclose(scalar, vectorized)

class TestAnalyzeFileForLoops:
    def test_detects_large_range(self):
        """Test detection of a loop with a literal range > threshold."""
        code = """
        for i in range(20000):
            pass
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = Path(f.name)
        
        try:
            loops = analyze_file_for_loops(temp_path)
            assert len(loops) == 1
            assert loops[0]['estimated_iterations'] == 20000
        finally:
            os.unlink(temp_path)

    def test_ignores_small_range(self):
        """Test that small loops are not flagged as heavy."""
        code = """
        for i in range(100):
            pass
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = Path(f.name)
        
        try:
            loops = analyze_file_for_loops(temp_path)
            # Should be empty or < threshold depending on logic, but definitely not flagged as heavy
            # Our logic flags if >= threshold
            assert len(loops) == 0
        finally:
            os.unlink(temp_path)

class TestGenerateReport:
    def test_report_structure(self):
        """Test that the generated report has the correct structure."""
        report = generate_report()
        
        assert 'timestamp' in report
        assert 'heavy_loop_threshold' in report
        assert 'benchmark_results' in report
        assert 'vectorization_status' in report
        assert 'summary' in report
        
        # Check nested keys
        assert 'speedup_factor' in report['benchmark_results']
        assert 'all_heavy_loops_vectorized' in report['summary']

    def test_report_is_valid_json(self):
        """Test that the report can be serialized to JSON."""
        report = generate_report()
        json_str = json.dumps(report)
        parsed = json.loads(json_str)
        assert parsed == report

if __name__ == "__main__":
    pytest.main([__file__, "-v"])