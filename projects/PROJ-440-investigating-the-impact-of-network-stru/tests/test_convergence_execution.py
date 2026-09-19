import os
import sys
import json
import numpy as np
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add project root to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from run_convergence_tests import (
    load_convergence_targets, 
    run_convergence_simulation, 
    compute_convergence_metrics,
    save_convergence_results
)
from simulate_oscillators import set_seed
from extract_energy_decay import extract_decay_rate

class TestConvergenceExecution:
    @pytest.fixture
    def mock_targets(self, tmp_path):
        targets = {
            "targets": [
                {"id": "graph_1", "class": "random", "edges": [(0,1), (1,2), (2,0)]},
                {"id": "graph_2", "class": "scale_free", "edges": [(0,1), (1,2), (2,3), (3,0), (0,2)]}
            ]
        }
        file_path = tmp_path / "convergence_targets.json"
        with open(file_path, 'w') as f:
            json.dump(targets, f)
        return str(file_path)

    def test_load_convergence_targets(self, mock_targets):
        targets = load_convergence_targets(mock_targets)
        assert len(targets) == 2
        assert targets[0]['id'] == 'graph_1'
        assert 'edges' in targets[0]

    def test_compute_convergence_metrics_valid(self):
        # Simulate successful decay rates with low variance
        results = [
            {'seed': 1, 'decay_rate': 0.050, 'r_squared': 0.99, 'status': 'dissipative'},
            {'seed': 2, 'decay_rate': 0.051, 'r_squared': 0.99, 'status': 'dissipative'},
            {'seed': 3, 'decay_rate': 0.049, 'r_squared': 0.99, 'status': 'dissipative'}
        ]
        output = {'graph_id': 'test', 'results': results}
        
        metrics = compute_convergence_metrics(output)
        
        assert metrics['graph_id'] == 'test'
        assert metrics['n_samples'] == 3
        assert metrics['passed_assertion'] is True # CV should be small
        assert metrics['cv'] < 0.01

    def test_compute_convergence_metrics_high_variance(self):
        # Simulate decay rates with high variance
        results = [
            {'seed': 1, 'decay_rate': 0.050, 'r_squared': 0.99, 'status': 'dissipative'},
            {'seed': 2, 'decay_rate': 0.100, 'r_squared': 0.99, 'status': 'dissipative'},
            {'seed': 3, 'decay_rate': 0.020, 'r_squared': 0.99, 'status': 'dissipative'}
        ]
        output = {'graph_id': 'test', 'results': results}
        
        metrics = compute_convergence_metrics(output)
        
        # CV will be high, so assertion should fail
        assert metrics['passed_assertion'] is False

    def test_compute_convergence_metrics_no_valid(self):
        # All resonant or failed
        results = [
            {'seed': 1, 'decay_rate': -0.01, 'r_squared': 0.99, 'status': 'resonant'}
        ]
        output = {'graph_id': 'test', 'results': results}
        
        metrics = compute_convergence_metrics(output)
        
        assert metrics['passed_assertion'] is False
        assert metrics['error'] is not None

    def test_save_convergence_results(self, tmp_path):
        metrics = [
            {'graph_id': 'g1', 'mean_decay': 0.05, 'std_decay': 0.001, 'cv': 0.02, 'passed_assertion': False, 'n_samples': 3},
            {'graph_id': 'g2', 'mean_decay': 0.05, 'std_decay': 0.0001, 'cv': 0.002, 'passed_assertion': True, 'n_samples': 3}
        ]
        output_path = tmp_path / "results.json"
        
        save_convergence_results(metrics, str(output_path))
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert 'summary' in data
        assert len(data['summary']) == 2
        assert data['all_passed'] is False
