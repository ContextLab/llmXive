"""
Unit tests for convergence analysis module.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.analysis.convergence import (
    calculate_steps_to_target,
    analyze_convergence,
    load_config,
    load_logs
)

import pytest

class TestCalculateStepsToTarget:
    """Tests for calculate_steps_to_target function."""
    
    def test_target_reached_early(self):
        """Test when target is reached early in training."""
        logs = {
            'training_history': [
                {'step': 1, 'success_rate': 0.1},
                {'step': 2, 'success_rate': 0.3},
                {'step': 3, 'success_rate': 0.5},
                {'step': 4, 'success_rate': 0.8},
                {'step': 5, 'success_rate': 0.9}
            ]
        }
        
        result = calculate_steps_to_target(logs, 0.5)
        assert result == 3
        
    def test_target_reached_late(self):
        """Test when target is reached late in training."""
        logs = {
            'training_history': [
                {'step': 1, 'success_rate': 0.1},
                {'step': 2, 'success_rate': 0.2},
                {'step': 3, 'success_rate': 0.3},
                {'step': 4, 'success_rate': 0.4},
                {'step': 5, 'success_rate': 0.5}
            ]
        }
        
        result = calculate_steps_to_target(logs, 0.5)
        assert result == 5
        
    def test_target_never_reached(self):
        """Test when target is never reached."""
        logs = {
            'training_history': [
                {'step': 1, 'success_rate': 0.1},
                {'step': 2, 'success_rate': 0.2},
                {'step': 3, 'success_rate': 0.3}
            ]
        }
        
        result = calculate_steps_to_target(logs, 0.8)
        assert result is None
        
    def test_no_training_history(self):
        """Test when logs have no training_history."""
        logs = {}
        
        result = calculate_steps_to_target(logs, 0.5)
        assert result is None
        
    def test_malformed_entries(self):
        """Test handling of malformed entries."""
        logs = {
            'training_history': [
                {'step': 1},  # Missing success_rate
                {'success_rate': 0.5},  # Missing step
                {'step': 3, 'success_rate': 0.8}  # Valid
            ]
        }
        
        result = calculate_steps_to_target(logs, 0.5)
        assert result == 3
        
class TestAnalyzeConvergence:
    """Tests for analyze_convergence function."""
    
    def test_both_reach_target(self):
        """Test when both methods reach target."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create config
            config_path = Path(tmpdir) / 'config.json'
            with open(config_path, 'w') as f:
                json.dump({'success_rate_threshold': 0.5}, f)
            
            # Create baseline logs
            baseline_path = Path(tmpdir) / 'baseline.json'
            with open(baseline_path, 'w') as f:
                json.dump({
                    'run_id': 'baseline_001',
                    'scheduler_type': 'Static Random',
                    'training_history': [
                        {'step': 1, 'success_rate': 0.1},
                        {'step': 2, 'success_rate': 0.3},
                        {'step': 3, 'success_rate': 0.5}
                    ]
                }, f)
            
            # Create experimental logs
            experimental_path = Path(tmpdir) / 'experimental.json'
            with open(experimental_path, 'w') as f:
                json.dump({
                    'run_id': 'exp_001',
                    'scheduler_type': 'State-Guided',
                    'training_history': [
                        {'step': 1, 'success_rate': 0.2},
                        {'step': 2, 'success_rate': 0.5}
                    ]
                }, f)
            
            result = analyze_convergence(
                baseline_logs_path=str(baseline_path),
                experimental_logs_path=str(experimental_path),
                config_path=str(config_path)
            )
            
            assert result['baseline']['steps_to_target'] == 3
            assert result['experimental']['steps_to_target'] == 2
            assert result['comparison']['absolute_difference'] == 1
            assert result['comparison']['percentage_difference'] == pytest.approx(33.333, rel=0.1)
            assert result['comparison']['interpretation'] == 'faster'
            
    def test_neither_reaches_target(self):
        """Test when neither method reaches target."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'config.json'
            with open(config_path, 'w') as f:
                json.dump({'success_rate_threshold': 0.9}, f)
            
            baseline_path = Path(tmpdir) / 'baseline.json'
            with open(baseline_path, 'w') as f:
                json.dump({
                    'run_id': 'baseline_001',
                    'training_history': [
                        {'step': 1, 'success_rate': 0.1},
                        {'step': 2, 'success_rate': 0.2}
                    ]
                }, f)
            
            experimental_path = Path(tmpdir) / 'experimental.json'
            with open(experimental_path, 'w') as f:
                json.dump({
                    'run_id': 'exp_001',
                    'training_history': [
                        {'step': 1, 'success_rate': 0.2},
                        {'step': 2, 'success_rate': 0.3}
                    ]
                }, f)
            
            result = analyze_convergence(
                baseline_logs_path=str(baseline_path),
                experimental_logs_path=str(experimental_path),
                config_path=str(config_path)
            )
            
            assert result['baseline']['steps_to_target'] is None
            assert result['experimental']['steps_to_target'] is None
            assert result['comparison']['interpretation'] == 'neither_reached_target'
            
    def test_experimental_faster(self):
        """Test when experimental method is faster."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'config.json'
            with open(config_path, 'w') as f:
                json.dump({'success_rate_threshold': 0.5}, f)
            
            baseline_path = Path(tmpdir) / 'baseline.json'
            with open(baseline_path, 'w') as f:
                json.dump({
                    'run_id': 'baseline_001',
                    'training_history': [
                        {'step': 1, 'success_rate': 0.1},
                        {'step': 2, 'success_rate': 0.3},
                        {'step': 3, 'success_rate': 0.4},
                        {'step': 4, 'success_rate': 0.5}
                    ]
                }, f)
            
            experimental_path = Path(tmpdir) / 'experimental.json'
            with open(experimental_path, 'w') as f:
                json.dump({
                    'run_id': 'exp_001',
                    'training_history': [
                        {'step': 1, 'success_rate': 0.2},
                        {'step': 2, 'success_rate': 0.5}
                    ]
                }, f)
            
            result = analyze_convergence(
                baseline_logs_path=str(baseline_path),
                experimental_logs_path=str(experimental_path),
                config_path=str(config_path)
            )
            
            assert result['comparison']['absolute_difference'] == 2
            assert result['comparison']['interpretation'] == 'faster'
            
    def test_experimental_slower(self):
        """Test when experimental method is slower."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'config.json'
            with open(config_path, 'w') as f:
                json.dump({'success_rate_threshold': 0.5}, f)
            
            baseline_path = Path(tmpdir) / 'baseline.json'
            with open(baseline_path, 'w') as f:
                json.dump({
                    'run_id': 'baseline_001',
                    'training_history': [
                        {'step': 1, 'success_rate': 0.2},
                        {'step': 2, 'success_rate': 0.5}
                    ]
                }, f)
            
            experimental_path = Path(tmpdir) / 'experimental.json'
            with open(experimental_path, 'w') as f:
                json.dump({
                    'run_id': 'exp_001',
                    'training_history': [
                        {'step': 1, 'success_rate': 0.1},
                        {'step': 2, 'success_rate': 0.3},
                        {'step': 3, 'success_rate': 0.4},
                        {'step': 4, 'success_rate': 0.5}
                    ]
                }, f)
            
            result = analyze_convergence(
                baseline_logs_path=str(baseline_path),
                experimental_logs_path=str(experimental_path),
                config_path=str(config_path)
            )
            
            assert result['comparison']['absolute_difference'] == -2
            assert result['comparison']['interpretation'] == 'slower'
            
    def test_equal_steps(self):
        """Test when both methods take equal steps."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'config.json'
            with open(config_path, 'w') as f:
                json.dump({'success_rate_threshold': 0.5}, f)
            
            baseline_path = Path(tmpdir) / 'baseline.json'
            with open(baseline_path, 'w') as f:
                json.dump({
                    'run_id': 'baseline_001',
                    'training_history': [
                        {'step': 1, 'success_rate': 0.2},
                        {'step': 2, 'success_rate': 0.5}
                    ]
                }, f)
            
            experimental_path = Path(tmpdir) / 'experimental.json'
            with open(experimental_path, 'w') as f:
                json.dump({
                    'run_id': 'exp_001',
                    'training_history': [
                        {'step': 1, 'success_rate': 0.2},
                        {'step': 2, 'success_rate': 0.5}
                    ]
                }, f)
            
            result = analyze_convergence(
                baseline_logs_path=str(baseline_path),
                experimental_logs_path=str(experimental_path),
                config_path=str(config_path)
            )
            
            assert result['comparison']['absolute_difference'] == 0
            assert result['comparison']['percentage_difference'] == 0.0
            assert result['comparison']['interpretation'] == 'equal'