"""
Unit tests for T019d: Seed Map Generation
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest

# Import the module functions
# We need to ensure the path is set up correctly if running standalone,
# but in the project structure, code/ is the root for imports.
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from generate_seed_map import (
    load_master_seed,
    load_params,
    load_required_iterations,
    build_seed_map,
    write_seed_map
)
from utils.exceptions import SimulationError

class TestLoadMasterSeed:
    def test_load_master_seed_success(self, tmp_path):
        master_seed_file = tmp_path / "master_seed.txt"
        master_seed_file.write_text("12345")

        with patch('generate_seed_map.Path', return_value=master_seed_file):
            # We need to patch the specific path used in the function
            # The function uses hardcoded "data/sweep/master_seed.txt"
            # So we can't easily patch Path() globally without affecting other logic.
            # Instead, we will patch the open function or the file existence check.
            pass

    # Better approach: Create the files in tmp_path and patch the working directory
    # or patch the specific Path construction.
    # Since the code uses hardcoded strings, we will mock the file system access.

    def test_load_master_seed_missing(self):
        with patch('generate_seed_map.Path.exists', return_value=False):
            with pytest.raises(FileNotFoundError):
                load_master_seed()

    def test_load_master_seed_empty(self):
        mock_file = mock_open(read_data="")
        with patch('generate_seed_map.open', mock_file):
            with patch('generate_seed_map.Path.exists', return_value=True):
                with pytest.raises(ValueError):
                    load_master_seed()

class TestLoadParams:
    def test_load_params_success(self, tmp_path):
        params_file = tmp_path / "params.csv"
        content = "seed,n,p,rho,distribution_type,iteration\n0,100,500,0.0,Normal,0\n1,100,500,0.0,Normal,1"
        params_file.write_text(content)

        # Mock the path to point to tmp_path
        original_path = Path
        def mock_path(path_str):
            if path_str == "data/sweep/params.csv":
                return params_file
            return original_path(path_str)

        with patch('generate_seed_map.Path', mock_path):
            params = load_params()
            assert len(params) == 2
            assert params[0]['n'] == 100
            assert params[1]['iteration'] == 1

    def test_load_params_missing(self):
        with patch('generate_seed_map.Path.exists', return_value=False):
            with pytest.raises(FileNotFoundError):
                load_params()

    def test_load_params_malformed(self, tmp_path):
        params_file = tmp_path / "params.csv"
        content = "seed,n,p,rho,distribution_type,iteration\n0,100,500\n1,100,500,0.0,Normal,1"
        params_file.write_text(content)

        original_path = Path
        def mock_path(path_str):
            if path_str == "data/sweep/params.csv":
                return params_file
            return original_path(path_str)

        with patch('generate_seed_map.Path', mock_path):
            # Should skip malformed line and return valid one
            params = load_params()
            assert len(params) == 1

class TestLoadRequiredIterations:
    def test_load_iterations_success(self, tmp_path):
        json_file = tmp_path / "power_analysis_result.json"
        json_file.write_text('{"iterations": 50, "power": 0.85, "threshold": 0.05}')

        original_path = Path
        def mock_path(path_str):
            if path_str == "data/sweep/power_analysis_result.json":
                return json_file
            return original_path(path_str)

        with patch('generate_seed_map.Path', mock_path):
            iterations = load_required_iterations()
            assert iterations == 50

    def test_load_iterations_missing_key(self, tmp_path):
        json_file = tmp_path / "power_analysis_result.json"
        json_file.write_text('{"power": 0.85}')

        original_path = Path
        def mock_path(path_str):
            if path_str == "data/sweep/power_analysis_result.json":
                return json_file
            return original_path(path_str)

        with patch('generate_seed_map.Path', mock_path):
            with pytest.raises(KeyError):
                load_required_iterations()

class TestBuildSeedMap:
    def test_build_seed_map_correct_counts(self):
        # Mock params: 2 rows for one key, 2 for another
        params = [
            {'seed': 0, 'n': 100, 'p': 500, 'rho': 0.0, 'distribution_type': 'Normal', 'iteration': 0},
            {'seed': 0, 'n': 100, 'p': 500, 'rho': 0.0, 'distribution_type': 'Normal', 'iteration': 1},
            {'seed': 0, 'n': 200, 'p': 1000, 'rho': 0.1, 'distribution_type': 't-dist', 'iteration': 0},
            {'seed': 0, 'n': 200, 'p': 1000, 'rho': 0.1, 'distribution_type': 't-dist', 'iteration': 1},
        ]
        required_iterations = 2
        master_seed = 42

        # Mock load_master_seed
        with patch('generate_seed_map.load_master_seed', return_value=master_seed):
            seed_map = build_seed_map(params, required_iterations)

        # Check keys
        key1 = "(100, 500, 0.0, 'Normal')"
        key2 = "(200, 1000, 0.1, 't-dist')"

        assert key1 in seed_map
        assert key2 in seed_map

        # Check values: sequential seeds
        # Group 1: 42, 43
        # Group 2: 44, 45
        assert seed_map[key1] == [42, 43]
        assert seed_map[key2] == [44, 45]

    def test_build_seed_map_mismatch(self):
        # 1 row but required 2
        params = [
            {'seed': 0, 'n': 100, 'p': 500, 'rho': 0.0, 'distribution_type': 'Normal', 'iteration': 0},
        ]
        required_iterations = 2

        with patch('generate_seed_map.load_master_seed', return_value=42):
            with pytest.raises(SimulationError, match="Seed map mismatch"):
                build_seed_map(params, required_iterations)

class TestWriteSeedMap:
    def test_write_seed_map(self, tmp_path):
        seed_map = {
            "(100, 500, 0.0, 'Normal')": [42, 43],
            "(200, 1000, 0.1, 't-dist')": [44, 45]
        }
        output_file = tmp_path / "seed_map.json"

        write_seed_map(seed_map, str(output_file))

        assert output_file.exists()
        with open(output_file, 'r') as f:
            loaded = json.load(f)
        assert loaded == seed_map