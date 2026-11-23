"""Unit tests for T062: Structural Baseline Verification."""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.baseline_verification import (
    calculate_baseline_deviation,
    flag_deviations,
    verify_baseline_integrity,
    load_baseline_data,
    write_verification_report,
    run_baseline_verification
)
from config import ensure_directories


class TestCalculateBaselineDeviation:
    def test_simple_deviation(self):
        pre = np.array([1.0, 2.0, 3.0])
        post = np.array([1.1, 2.2, 2.9])
        expected = np.array([0.1, 0.2, 0.1])
        result = calculate_baseline_deviation(pre, post)
        np.testing.assert_array_almost_equal(result, expected)

    def test_negative_deviation_handling(self):
        pre = np.array([1.0, 2.0])
        post = np.array([0.8, 2.5])
        # Absolute difference
        expected = np.array([0.2, 0.5])
        result = calculate_baseline_deviation(pre, post)
        np.testing.assert_array_almost_equal(result, expected)


class TestFlagDeviations:
    def test_no_exceeds(self):
        deviations = np.array([0.001, 0.002, 0.003])
        threshold = 0.005
        flags, count = flag_deviations(deviations, threshold)
        assert count == 0
        assert all(not f for f in flags)

    def test_some_exceeds(self):
        deviations = np.array([0.001, 0.006, 0.003])
        threshold = 0.005
        flags, count = flag_deviations(deviations, threshold)
        assert count == 1
        assert flags == [False, True, False]

    def test_all_exceeds(self):
        deviations = np.array([0.01, 0.02])
        threshold = 0.005
        flags, count = flag_deviations(deviations, threshold)
        assert count == 2
        assert all(flags)


class TestVerifyBaselineIntegrity:
    def test_passing_run(self):
        # Create a mock DataFrame
        data = {
            'solvent': ['water', 'water'],
            'wavelength': [300, 300],
            'absorbance_pre': [0.5, 0.5],
            'absorbance_post': [0.501, 0.502]
        }
        df = pd.DataFrame(data)

        report = verify_baseline_integrity(df, noise_threshold=0.005)

        assert report['overall_status'] == 'PASS'
        assert report['runs_passed'] == 1
        assert report['runs_failed'] == 0

    def test_failing_run(self):
        # Create a mock DataFrame with a large deviation
        data = {
            'solvent': ['methanol', 'methanol'],
            'wavelength': [300, 300],
            'absorbance_pre': [0.5, 0.5],
            'absorbance_post': [0.6, 0.6] # 0.1 deviation > 0.005
        }
        df = pd.DataFrame(data)

        report = verify_baseline_integrity(df, noise_threshold=0.005)

        assert report['overall_status'] == 'FAIL'
        assert report['runs_passed'] == 0
        assert report['runs_failed'] == 1
        # Check details
        assert report['details'][0]['max_deviation'] > 0.005
        assert report['details'][0]['status'] == 'FAIL'

    def test_multiple_solvents(self):
        data = {
            'solvent': ['water', 'water', 'toluene', 'toluene'],
            'wavelength': [300, 300, 300, 300],
            'absorbance_pre': [0.5, 0.5, 0.5, 0.5],
            'absorbance_post': [0.501, 0.502, 0.6, 0.501]
        }
        df = pd.DataFrame(data)

        report = verify_baseline_integrity(df, noise_threshold=0.005)

        assert report['runs_passed'] == 2 # water passes (avg ~0.0015), toluene fails (0.1)
        assert report['runs_failed'] == 1
        assert report['overall_status'] == 'FAIL'


class TestIntegration:
    @pytest.fixture
    def temp_data_dir(self):
        # Create a temporary directory structure for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "data" / "processed"
            data_dir.mkdir(parents=True)

            # Create a fake baseline CSV
            csv_path = data_dir / "ground_state_spectra.csv"
            df = pd.DataFrame({
                'solvent': ['acetonitrile', 'acetonitrile'],
                'wavelength': [250, 250],
                'absorbance_pre': [0.8, 0.8],
                'absorbance_post': [0.801, 0.802]
            })
            df.to_csv(csv_path, index=False)

            yield tmpdir

    def test_full_pipeline(self, temp_data_dir):
        # Mock get_processed_data_path to return our temp dir
        with patch('analysis.baseline_verification.get_processed_data_path', return_value=str(Path(temp_data_dir) / "data" / "processed")):
            report = run_baseline_verification(noise_threshold=0.005)

            # Verify report structure
            assert 'overall_status' in report
            assert 'details' in report
            assert report['overall_status'] == 'PASS'

            # Verify file was written
            output_path = Path(temp_data_dir) / "data" / "processed" / "baseline_verification_report.json"
            assert output_path.exists()

            with open(output_path) as f:
                saved_report = json.load(f)

            assert saved_report['overall_status'] == report['overall_status']