import pytest
import sys
import os
import time
import json
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from simulate_agent import (
    sigmoid, 
    heuristic_solver_success, 
    check_evidence_visibility, 
    run_simulation_batch,
    get_memory_usage_gb
)
from analyze_results import (
    load_simulation_data,
    validate_sample_size,
    build_formula_with_splines,
    run_logistic_regression
)

class TestSimulateAgentOptimization:
    def test_sigmoid_vectorization(self):
        """Test that sigmoid handles vector inputs efficiently."""
        # Scalar
        assert abs(sigmoid(0.0) - 0.5) < 1e-6
        # Large positive
        assert sigmoid(100.0) > 0.99
        # Large negative
        assert sigmoid(-100.0) < 0.01
        
        # Vector (numpy)
        x = np.array([0.0, 1.0, -1.0])
        res = sigmoid(x)
        assert isinstance(res, np.ndarray)
        assert len(res) == 3
        assert abs(res[0] - 0.5) < 1e-6

    def test_check_evidence_visibility(self):
        """Test visibility logic."""
        # Turn 10, Horizon 5 -> Window [6, 10]. Evidence at 8 -> Visible
        assert check_evidence_visibility(10, 8, 5) is True
        # Evidence at 5 -> Not Visible
        assert check_evidence_visibility(10, 5, 5) is False
        # Evidence at 10 -> Visible
        assert check_evidence_visibility(10, 10, 5) is True

    def test_run_simulation_batch_performance(self):
        """
        Test that processing a large batch is reasonably fast.
        We generate a synthetic batch to simulate the load.
        """
        # Create a large batch
        batch_size = 1000
        batch = []
        for i in range(batch_size):
            batch.append({
                'id': i,
                'turns': list(range(20)), # 20 turns
                'evidence_turn_index': 10,
                'density_value': 0.5 + (i % 10) * 0.01
            })
        
        start = time.time()
        results = run_simulation_batch(batch, horizon=5, alpha=1.0, threshold=0.5, seed=42)
        duration = time.time() - start
        
        assert len(results) == batch_size
        # Should complete in under 5 seconds for 1000 items
        assert duration < 5.0, f"Batch processing took {duration:.2f}s, expected < 5s"

class TestAnalyzeResultsOptimization:
    def test_load_simulation_data_speed(self):
        """Test loading a large JSONL file efficiently."""
        # Create a temp file with 5000 lines
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            temp_path = f.name
            for i in range(5000):
                f.write(json.dumps({'success': i%2, 'horizon': i%5, 'density': 0.5}) + '\n')
        
        try:
            start = time.time()
            df = load_simulation_data(Path(temp_path))
            duration = time.time() - start
            
            assert len(df) == 5000
            # Should load 5000 rows in < 1 second
            assert duration < 2.0, f"Loading took {duration:.2f}s"
        finally:
            os.unlink(temp_path)

    def test_build_formula_with_splines(self):
        """Test formula generation."""
        df = pd.DataFrame({'success': [0, 1], 'horizon': [1, 2], 'density': [0.5, 0.6]})
        formula = build_formula_with_splines(df, df_splines=3)
        assert 'bs(horizon, df=3)' in formula
        assert 'density' in formula
        assert '*' in formula # Interaction

    def test_validate_sample_size(self):
        """Test sample size validation."""
        df_small = pd.DataFrame({'success': [0, 1]})
        df_large = pd.DataFrame({'success': [0] * 100})
        
        assert validate_sample_size(df_small, min_size=30) is False
        assert validate_sample_size(df_large, min_size=30) is True