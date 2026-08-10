import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np
import pandas as pd

from code.profile_simulation import (
    get_memory_usage_mb,
    run_profiled_sweep,
    write_profile_report
)
from code.utils.exceptions import SimulationError


class TestProfileSimulation:
    """Unit tests for the simulation profiling functionality."""

    def test_get_memory_usage_mb_returns_positive_float(self):
        """Test that memory usage function returns a positive float."""
        memory_mb = get_memory_usage_mb()
        assert isinstance(memory_mb, float)
        assert memory_mb > 0

    @pytest.fixture
    def sample_params_csv(self, tmp_path):
        """Create a sample params.csv file for testing."""
        params_file = tmp_path / 'params.csv'
        data = {
            'seed': [1, 2, 3, 4, 5],
            'n': [100, 100, 200, 200, 100],
            'p': [1000, 2000, 1000, 2000, 5000],
            'rho': [0.1, 0.5, 0.3, 0.7, 0.9],
            'iteration': [1, 1, 1, 1, 1]
        }
        df = pd.DataFrame(data)
        df.to_csv(params_file, index=False)
        return str(params_file)

    @pytest.fixture
    def sample_seed_map(self, tmp_path):
        """Create a sample seed_map.json file for testing."""
        seed_map_file = tmp_path / 'seed_map.json'
        seed_map = {
            '100_1000_0.1': [1],
            '100_2000_0.5': [2],
            '200_1000_0.3': [3],
            '200_2000_0.7': [4],
            '100_5000_0.9': [5]
        }
        with open(seed_map_file, 'w') as f:
            json.dump(seed_map, f)
        return str(seed_map_file)

    def test_run_profiled_sweep_basic(self, sample_params_csv, sample_seed_map):
        """Test basic execution of profiled sweep."""
        result = run_profiled_sweep(
            params_file=sample_params_csv,
            seed_map_file=sample_seed_map,
            max_duration_seconds=300.0,
            sample_fraction=1.0  # Run all iterations for this test
        )
        
        assert 'profile_date' in result
        assert 'total_iterations' in result
        assert 'estimated_total_hours' in result
        assert result['total_iterations'] == 5
        assert result['sampled_iterations'] == 5
        assert 'per_iteration_stats' in result
        assert len(result['per_iteration_stats']) == 5

    def test_run_profiled_sweep_extrapolation(self, sample_params_csv, sample_seed_map):
        """Test that extrapolation logic works correctly with partial sampling."""
        result = run_profiled_sweep(
            params_file=sample_params_csv,
            seed_map_file=sample_seed_map,
            max_duration_seconds=300.0,
            sample_fraction=0.5  # Sample 50%
        )
        
        assert result['sampled_iterations'] == 2  # max(1, int(5 * 0.5)) = 2
        assert result['estimated_total_hours'] > 0
        assert result['estimated_total_time_seconds'] > 0

    def test_run_profiled_sweep_file_not_found(self, tmp_path):
        """Test that appropriate error is raised when params file is missing."""
        with pytest.raises(FileNotFoundError):
            run_profiled_sweep(
                params_file=str(tmp_path / 'nonexistent.csv'),
                seed_map_file=str(tmp_path / 'seed_map.json'),
                max_duration_seconds=300.0,
                sample_fraction=0.1
            )

    def test_run_profiled_sweep_seed_map_not_found(self, sample_params_csv, tmp_path):
        """Test that appropriate error is raised when seed map is missing."""
        with pytest.raises(FileNotFoundError):
            run_profiled_sweep(
                params_file=sample_params_csv,
                seed_map_file=str(tmp_path / 'nonexistent.json'),
                max_duration_seconds=300.0,
                sample_fraction=0.1
            )

    def test_write_profile_report(self, tmp_path):
        """Test that profile report is written correctly."""
        sample_result = {
            'test_key': 'test_value',
            'number': 42,
            'nested': {'a': 1, 'b': 2}
        }
        output_path = str(tmp_path / 'test_report.json')
        
        write_profile_report(sample_result, output_path)
        
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        
        assert loaded == sample_result

    def test_profile_result_structure(self, sample_params_csv, sample_seed_map):
        """Test that the profile result contains all required fields."""
        result = run_profiled_sweep(
            params_file=sample_params_csv,
            seed_map_file=sample_seed_map,
            max_duration_seconds=300.0,
            sample_fraction=0.2
        )
        
        required_fields = [
            'profile_date',
            'total_iterations',
            'sampled_iterations',
            'sample_fraction',
            'profile_duration_seconds',
            'average_time_per_iteration',
            'estimated_total_time_seconds',
            'estimated_total_hours',
            'max_duration_allowed_seconds',
            'max_duration_allowed_hours',
            'meets_time_requirement',
            'max_memory_mb',
            'memory_limit_mb',
            'meets_memory_requirement',
            'per_iteration_stats',
            'memory_samples'
        ]
        
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

    def test_memory_limit_check(self, sample_params_csv, sample_seed_map):
        """Test that memory limit check is included in results."""
        result = run_profiled_sweep(
            params_file=sample_params_csv,
            seed_map_file=sample_seed_map,
            max_duration_seconds=300.0,
            sample_fraction=0.2
        )
        
        assert 'meets_memory_requirement' in result
        assert isinstance(result['meets_memory_requirement'], bool)
        assert result['memory_limit_mb'] == 6000

    def test_time_requirement_check(self, sample_params_csv, sample_seed_map):
        """Test that time requirement check is included in results."""
        result = run_profiled_sweep(
            params_file=sample_params_csv,
            seed_map_file=sample_seed_map,
            max_duration_seconds=300.0,
            sample_fraction=0.2
        )
        
        assert 'meets_time_requirement' in result
        assert isinstance(result['meets_time_requirement'], bool)
        assert result['max_duration_allowed_seconds'] == 300.0

    def test_per_iteration_stats_structure(self, sample_params_csv, sample_seed_map):
        """Test that per-iteration stats contain required fields."""
        result = run_profiled_sweep(
            params_file=sample_params_csv,
            seed_map_file=sample_seed_map,
            max_duration_seconds=300.0,
            sample_fraction=0.4
        )
        
        assert len(result['per_iteration_stats']) > 0
        
        required_stat_fields = ['iteration', 'n', 'p', 'rho', 'time_seconds', 'ops_estimate']
        
        for stat in result['per_iteration_stats']:
            for field in required_stat_fields:
                assert field in stat, f"Missing stat field: {field}"

    def test_memory_samples_structure(self, sample_params_csv, sample_seed_map):
        """Test that memory samples contain required fields."""
        result = run_profiled_sweep(
            params_file=sample_params_csv,
            seed_map_file=sample_seed_map,
            max_duration_seconds=300.0,
            sample_fraction=0.4
        )
        
        assert len(result['memory_samples']) > 0
        
        required_memory_fields = ['iteration', 'memory_before_mb', 'memory_after_mb', 'memory_delta_mb']
        
        for sample in result['memory_samples']:
            for field in required_memory_fields:
                assert field in sample, f"Missing memory sample field: {field}"

    def test_sample_fraction_validation(self, sample_params_csv, sample_seed_map):
        """Test that sample fraction is respected."""
        # Test with 0.2 fraction
        result = run_profiled_sweep(
            params_file=sample_params_csv,
            seed_map_file=sample_seed_map,
            max_duration_seconds=300.0,
            sample_fraction=0.2
        )
        
        expected_sample = max(1, int(5 * 0.2))  # 5 total iterations
        assert result['sampled_iterations'] == expected_sample

    def test_empty_params_handling(self, tmp_path):
        """Test handling of empty params file."""
        params_file = tmp_path / 'empty_params.csv'
        pd.DataFrame(columns=['seed', 'n', 'p', 'rho', 'iteration']).to_csv(params_file, index=False)
        
        seed_map_file = tmp_path / 'seed_map.json'
        with open(seed_map_file, 'w') as f:
            json.dump({}, f)
        
        with pytest.raises((ZeroDivisionError, SimulationError)):
            run_profiled_sweep(
                params_file=str(params_file),
                seed_map_file=str(seed_map_file),
                max_duration_seconds=300.0,
                sample_fraction=0.5
            )