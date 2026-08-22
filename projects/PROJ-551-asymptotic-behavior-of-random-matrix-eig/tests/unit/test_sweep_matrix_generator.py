"""
Unit tests for sweep_matrix_generator.py (T040a)
"""
import os
import sys
import tempfile
import json
from pathlib import Path
import pytest
import numpy as np

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.sweep_matrix_generator import (
    generate_sweep_configs,
    save_raw_sweep_matrix,
    run_sweep_generation
)


class TestGenerateSweepConfigs:
    """Tests for generate_sweep_configs function"""

    def test_generate_single_config(self):
        """Test generating a single configuration"""
        configs = generate_sweep_configs(
            N_values=[100],
            theta_values=[2.0],
            seeds=[42]
        )
        assert len(configs) == 1
        assert configs[0]["N"] == 100
        assert configs[0]["theta"] == 2.0
        assert configs[0]["seed"] == 42
        assert configs[0]["perturbation_type"] == "diagonal"

    def test_generate_multiple_configs(self):
        """Test generating multiple configurations"""
        configs = generate_sweep_configs(
            N_values=[100, 200],
            theta_values=[1.0, 2.0],
            seeds=[42, 43]
        )
        assert len(configs) == 8  # 2 * 2 * 2
        # Check that all combinations are present
        N_values = set(c["N"] for c in configs)
        theta_values = set(c["theta"] for c in configs)
        seed_values = set(c["seed"] for c in configs)
        assert N_values == {100, 200}
        assert theta_values == {1.0, 2.0}
        assert seed_values == {42, 43}


class TestSaveRawSweepMatrix:
    """Tests for save_raw_sweep_matrix function"""

    def test_save_matrix_creates_file(self):
        """Test that save_raw_sweep_matrix creates a valid .npy file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            config = {
                "N": 100,
                "theta": 2.0,
                "seed": 42,
                "perturbation_type": "diagonal"
            }

            filepath = save_raw_sweep_matrix(config, output_dir)

            assert os.path.exists(filepath)
            assert filepath.endswith(".npy")

            # Verify the file can be loaded
            matrix = np.load(filepath)
            assert matrix.shape == (100, 100)
            assert matrix.dtype == np.float64

    def test_save_matrix_filename_format(self):
        """Test that the filename follows the expected format"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            config = {
                "N": 500,
                "theta": 2.5,
                "seed": 123,
                "perturbation_type": "diagonal"
            }

            filepath = save_raw_sweep_matrix(config, output_dir)
            filename = os.path.basename(filepath)

            assert filename == "matrix_N500_theta2.5_seed123.npy"

    def test_save_matrix_reproducibility(self):
        """Test that the same seed produces the same matrix"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            config = {
                "N": 50,
                "theta": 1.5,
                "seed": 999,
                "perturbation_type": "diagonal"
            }

            filepath1 = save_raw_sweep_matrix(config, output_dir)
            matrix1 = np.load(filepath1)

            # Generate again with same config
            filepath2 = save_raw_sweep_matrix(config, output_dir)
            matrix2 = np.load(filepath2)

            # Should be identical
            assert np.allclose(matrix1, matrix2)


class TestRunSweepGeneration:
    """Tests for run_sweep_generation function"""

    def test_run_sweep_creates_files(self):
        """Test that run_sweep_generation creates the expected files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            files = run_sweep_generation(
                N_values=[50],
                theta_values=[1.0, 2.0],
                seeds=[42],
                output_dir=output_dir
            )

            assert len(files) == 2
            for f in files:
                assert os.path.exists(f)
                assert f.endswith(".npy")

    def test_run_sweep_default_values(self):
        """Test that run_sweep_generation works with default values"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Use minimal defaults to avoid long tests
            files = run_sweep_generation(
                N_values=[50],
                theta_values=[2.0],
                seeds=[42],
                output_dir=output_dir
            )

            assert len(files) == 1
            matrix = np.load(files[0])
            assert matrix.shape == (50, 50)

    def test_run_sweep_different_perturbation_types(self):
        """Test sweep generation with different perturbation types"""
        for ptype in ["diagonal", "block-sparse", "random-sparse"]:
            with tempfile.TemporaryDirectory() as tmpdir:
                output_dir = Path(tmpdir)

                files = run_sweep_generation(
                    N_values=[50],
                    theta_values=[2.0],
                    seeds=[42],
                    perturbation_type=ptype,
                    output_dir=output_dir
                )

                assert len(files) == 1
                matrix = np.load(files[0])
                assert matrix.shape == (50, 50)
