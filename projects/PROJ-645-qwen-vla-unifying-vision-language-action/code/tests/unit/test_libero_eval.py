import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import torch
import numpy as np

from src.evaluation.libero_eval import (
    main,
    load_mock_model,
    evaluate_on_benchmark,
    run_single_episode_mock,
    SEEDS
)

class TestLiberoEval:
    """Unit tests for LIBERO evaluation module (T016)"""

    def test_load_mock_model(self):
        """Test that mock model loads correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_path = Path(tmpdir) / "model.pt"
            mock_model = torch.nn.Linear(10, 7)
            torch.save(mock_model.state_dict(), checkpoint_path)

            loaded_model = load_mock_model(str(checkpoint_path))
            assert loaded_model is not None

    def test_run_single_episode_mock(self):
        """Test single episode mock evaluation"""
        class MockEnv:
            def reset(self):
                return {}

            def step(self, action):
                return {}, 1.0, True, {}

        model = load_mock_model(None)
        result = run_single_episode_mock(MockEnv(), model, seed=42, max_steps=10)

        assert 'success' in result
        assert 'trajectory_length' in result
        assert result['trajectory_length'] >= 1

    @patch('src.evaluation.libero_eval.ResourceMonitor')
    def test_main_creates_output(self, mock_monitor):
        """Test that main function creates valid output file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_path = Path(tmpdir) / "model.pt"
            output_path = Path(tmpdir) / "eval_results.json"

            # Create mock checkpoint
            torch.save(torch.nn.Linear(10, 7).state_dict(), checkpoint_path)

            # Mock the monitor
            mock_instance = MagicMock()
            mock_instance.get_peak_ram_gb.return_value = 1.5
            mock_monitor.return_value = mock_instance

            # Run evaluation
            results = main(
                checkpoint_path=str(checkpoint_path),
                output_path=str(output_path),
                benchmarks=["spatial"],
                embodiments=["franka"],
                seeds=[42, 123]
            )

            # Verify file was created
            assert output_path.exists(), "Output file not created"

            # Verify JSON structure
            with open(output_path, 'r') as f:
                data = json.load(f)

            assert 'results' in data
            assert 'seeds_used' in data
            assert len(data['seeds_used']) == 2

            # Verify each result has required keys
            for key, val in data['results'].items():
                assert 'success_rate' in val
                assert 'trajectory_length' in val
                assert 'variance' in val
                assert 'ci_95_lower' in val
                assert 'ci_95_upper' in val
                assert 'type' in val
                assert val['type'] in ['within-embodiment', 'cross-embodiment']

    @patch('src.evaluation.libero_eval.ResourceMonitor')
    def test_within_vs_cross_embodiment_distinction(self, mock_monitor):
        """Test that within-embodiment and cross-embodiment are distinguished"""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_path = Path(tmpdir) / "model.pt"
            output_path = Path(tmpdir) / "eval_results.json"

            torch.save(torch.nn.Linear(10, 7).state_dict(), checkpoint_path)

            mock_instance = MagicMock()
            mock_instance.get_peak_ram_gb.return_value = 1.5
            mock_monitor.return_value = mock_instance

            results = main(
                checkpoint_path=str(checkpoint_path),
                output_path=str(output_path),
                benchmarks=["spatial"],
                embodiments=["franka", "ur5"],
                seeds=[42]
            )

            with open(output_path, 'r') as f:
                data = json.load(f)

            # Check franka is within-embodiment
            franka_key = [k for k in data['results'].keys() if 'franka' in k][0]
            assert data['results'][franka_key]['type'] == 'within-embodiment'

            # Check ur5 is cross-embodiment
            ur5_key = [k for k in data['results'].keys() if 'ur5' in k][0]
            assert data['results'][ur5_key]['type'] == 'cross-embodiment'

    @patch('src.evaluation.libero_eval.ResourceMonitor')
    def test_ci_computation(self, mock_monitor):
        """Test that confidence intervals are computed"""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_path = Path(tmpdir) / "model.pt"
            output_path = Path(tmpdir) / "eval_results.json"

            torch.save(torch.nn.Linear(10, 7).state_dict(), checkpoint_path)

            mock_instance = MagicMock()
            mock_instance.get_peak_ram_gb.return_value = 1.5
            mock_monitor.return_value = mock_instance

            # Use multiple seeds to ensure CI computation
            results = main(
                checkpoint_path=str(checkpoint_path),
                output_path=str(output_path),
                benchmarks=["spatial"],
                embodiments=["franka"],
                seeds=[42, 123, 456, 789, 101112]
            )

            with open(output_path, 'r') as f:
                data = json.load(f)

            for key, val in data['results'].items():
                assert val['ci_95_lower'] <= val['ci_95_upper'], \
                    f"CI bounds invalid for {key}"
                assert val['ci_95_lower'] >= 0.0
                assert val['ci_95_upper'] <= 1.0

    def test_output_format_verification(self):
        """Test that output matches T016 specification exactly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_path = Path(tmpdir) / "model.pt"
            output_path = Path(tmpdir) / "eval_results.json"

            torch.save(torch.nn.Linear(10, 7).state_dict(), checkpoint_path)

            # Create minimal mock monitor
            class MockMonitor:
                def start(self): pass
                def stop(self): pass
                def get_peak_ram_gb(self): return 1.5

            with patch('src.evaluation.libero_eval.ResourceMonitor', return_value=MockMonitor()):
                results = main(
                    checkpoint_path=str(checkpoint_path),
                    output_path=str(output_path),
                    seeds=[42]
                )

            # Verify exact keys required by T016
            for key, val in results['results'].items():
                required_keys = [
                    'success_rate',      # per-seed list
                    'trajectory_length', # per-seed list
                    'variance',
                    'ci_95_lower',
                    'ci_95_upper'
                ]
                for req_key in required_keys:
                    assert req_key in val, f"Missing required key '{req_key}' in {key}"

                # Verify types
                assert isinstance(val['success_rate'], list)
                assert isinstance(val['trajectory_length'], list)
                assert isinstance(val['variance'], (int, float))
                assert isinstance(val['ci_95_lower'], (int, float))
                assert isinstance(val['ci_95_upper'], (int, float))