"""
Unit tests for sensitivity analysis module.

Tests FR-009: p-value threshold sensitivity analysis.
Verifies that the analysis correctly evaluates correlations across
different significance thresholds (0.01, 0.05, 0.1).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
from typing import Dict, Any
import json
import tempfile

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / 'code'))

from src.analysis.sensitivity import (
    run_sensitivity_analysis,
    _compute_thresholded_correlations,
    _generate_sensitivity_summary,
    save_sensitivity_report,
    setup_logger_module
)


class TestSensitivityAnalysis:
    """Test suite for sensitivity analysis functionality."""

    @pytest.fixture
    def sample_data(self):
        """Create sample dataframe for testing."""
        np.random.seed(42)
        n_samples = 100

        # Create correlated data
        tolerance = np.random.normal(0.9, 0.05, n_samples)
        tilting = np.random.normal(5.0, 1.0, n_samples)
        bond_var = np.random.normal(0.02, 0.005, n_samples)
        volume = np.random.normal(100, 10, n_samples)

        # Create thermal conductivity with some correlation to descriptors
        thermal = (
            10.0
            - 5.0 * (tolerance - 0.9)
            - 0.5 * (tilting - 5.0)
            + 100.0 * bond_var
            + 0.01 * (volume - 100)
            + np.random.normal(0, 1, n_samples)
        )

        # Create chemistry classes
        chemistry = np.random.choice(['oxide', 'halide', 'nitride'], n_samples)

        df = pd.DataFrame({
            'tolerance_factor': tolerance,
            'octahedral_tilting_angle': tilting,
            'bond_length_variance': bond_var,
            'unit_cell_volume': volume,
            'thermal_conductivity_normalized': thermal,
            'chemistry_class': chemistry
        })

        return df

    @pytest.fixture
    def descriptors(self):
        """List of descriptor names."""
        return [
            'tolerance_factor',
            'octahedral_tilting_angle',
            'bond_length_variance',
            'unit_cell_volume'
        ]

    def test_run_sensitivity_analysis_basic(self, sample_data, descriptors):
        """Test basic sensitivity analysis execution."""
        result = run_sensitivity_analysis(
            df=sample_data,
            descriptors=descriptors,
            target='thermal_conductivity_normalized',
            thresholds=[0.01, 0.05, 0.1]
        )

        # Check structure
        assert 'thresholds' in result
        assert 'results' in result
        assert 'summary' in result
        assert 'metadata' in result

        # Check thresholds
        assert result['thresholds'] == [0.01, 0.05, 0.1]

        # Check metadata
        assert result['metadata']['n_samples'] == 100
        assert result['metadata']['n_descriptors'] == 4
        assert result['metadata']['method'] == 'spearman'

    def test_run_sensitivity_analysis_stratified(self, sample_data, descriptors):
        """Test stratified sensitivity analysis."""
        result = run_sensitivity_analysis(
            df=sample_data,
            descriptors=descriptors,
            target='thermal_conductivity_normalized',
            thresholds=[0.01, 0.05, 0.1],
            stratify_by='chemistry_class'
        )

        # Check stratified results exist
        assert 'results' in result
        assert 'stratified' in result['results']

        # Check all chemistry classes are present
        assert 'oxide' in result['results']['stratified']
        assert 'halide' in result['results']['stratified']
        assert 'nitride' in result['results']['stratified']

        # Check each stratum has all thresholds
        for stratum in result['results']['stratified'].values():
            for threshold in [0.01, 0.05, 0.1]:
                assert threshold in stratum

    def test_compute_thresholded_correlations(self, sample_data, descriptors):
        """Test correlation computation at a single threshold."""
        result = _compute_thresholded_correlations(
            df=sample_data,
            descriptors=descriptors,
            target='thermal_conductivity_normalized',
            threshold=0.05,
            method='spearman'
        )

        # Check structure
        assert 'threshold' in result
        assert 'correlations' in result
        assert 'significant_count' in result
        assert 'significant_pairs' in result

        # Check correlations dict has all descriptors
        assert len(result['correlations']) == len(descriptors)
        for desc in descriptors:
            assert desc in result['correlations']
            corr_data = result['correlations'][desc]
            assert 'correlation' in corr_data
            assert 'p_value' in corr_data
            assert 'significant' in corr_data
            assert 'threshold' in corr_data

    def test_generate_sensitivity_summary(self, sample_data, descriptors):
        """Test summary generation across thresholds."""
        # First run full analysis
        full_result = run_sensitivity_analysis(
            df=sample_data,
            descriptors=descriptors,
            target='thermal_conductivity_normalized',
            thresholds=[0.01, 0.05, 0.1]
        )

        summary = full_result['summary']

        # Check summary structure
        assert 'stable_significant' in summary
        assert 'threshold_sensitive' in summary
        assert 'always_non_significant' in summary
        assert 'stability_scores' in summary

        # Check stability scores
        assert len(summary['stability_scores']) == len(descriptors)
        for desc in descriptors:
            assert desc in summary['stability_scores']
            score = summary['stability_scores'][desc]
            assert 0 <= score <= 1

    def test_save_sensitivity_report(self, sample_data, descriptors):
        """Test saving results to JSON file."""
        result = run_sensitivity_analysis(
            df=sample_data,
            descriptors=descriptors,
            target='thermal_conductivity_normalized',
            thresholds=[0.01, 0.05, 0.1]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test_sensitivity.json'
            saved_path = save_sensitivity_report(result, output_path)

            # Check file exists
            assert saved_path.exists()

            # Check JSON is valid
            with open(saved_path, 'r') as f:
                loaded = json.load(f)

            # Check structure preserved
            assert 'thresholds' in loaded
            assert 'results' in loaded
            assert 'summary' in loaded

    def test_invalid_target_column(self, sample_data, descriptors):
        """Test error handling for missing target column."""
        with pytest.raises(ValueError, match="Target column"):
            run_sensitivity_analysis(
                df=sample_data,
                descriptors=descriptors,
                target='nonexistent_column',
                thresholds=[0.01, 0.05, 0.1]
            )

    def test_missing_descriptors(self, sample_data):
        """Test error handling for missing descriptor columns."""
        with pytest.raises(ValueError, match="Missing descriptor columns"):
            run_sensitivity_analysis(
                df=sample_data,
                descriptors=['nonexistent_desc'],
                target='thermal_conductivity_normalized',
                thresholds=[0.01, 0.05, 0.1]
            )

    def test_insufficient_samples(self):
        """Test error handling for insufficient samples."""
        # Create dataframe with only 2 samples
        df = pd.DataFrame({
            'tolerance_factor': [0.9, 0.91],
            'thermal_conductivity_normalized': [10.0, 11.0]
        })

        with pytest.raises(ValueError, match="Insufficient samples"):
            run_sensitivity_analysis(
                df=df,
                descriptors=['tolerance_factor'],
                target='thermal_conductivity_normalized',
                thresholds=[0.01, 0.05, 0.1]
            )

    def test_custom_thresholds(self, sample_data, descriptors):
        """Test with custom threshold values."""
        custom_thresholds = [0.001, 0.01, 0.05, 0.1, 0.2]
        result = run_sensitivity_analysis(
            df=sample_data,
            descriptors=descriptors,
            target='thermal_conductivity_normalized',
            thresholds=custom_thresholds
        )

        assert result['thresholds'] == custom_thresholds
        for t in custom_thresholds:
            assert t in result['results']

    def test_pearson_method(self, sample_data, descriptors):
        """Test with Pearson correlation method."""
        result = run_sensitivity_analysis(
            df=sample_data,
            descriptors=descriptors,
            target='thermal_conductivity_normalized',
            thresholds=[0.05],
            method='pearson'
        )

        assert result['metadata']['method'] == 'pearson'

    def test_stability_score_calculation(self, sample_data, descriptors):
        """Test that stability scores are correctly calculated."""
        result = run_sensitivity_analysis(
            df=sample_data,
            descriptors=descriptors,
            target='thermal_conductivity_normalized',
            thresholds=[0.01, 0.05, 0.1]
        )

        summary = result['summary']

        for desc, score in summary['stability_scores'].items():
            # Count how many thresholds this descriptor is significant at
            significant_count = 0
            for threshold in [0.01, 0.05, 0.1]:
                if threshold in result['results']:
                    if desc in result['results'][threshold]['correlations']:
                        if result['results'][threshold]['correlations'][desc]['significant']:
                            significant_count += 1

            expected_score = significant_count / 3.0
            assert abs(score - expected_score) < 1e-10

    def test_stratified_summary_structure(self, sample_data, descriptors):
        """Test stratified summary has correct structure per group."""
        result = run_sensitivity_analysis(
            df=sample_data,
            descriptors=descriptors,
            target='thermal_conductivity_normalized',
            thresholds=[0.01, 0.05, 0.1],
            stratify_by='chemistry_class'
        )

        for stratum_name, stratum_summary in result['summary'].items():
            if stratum_name.startswith('stratum_'):
                assert 'stable_significant' in stratum_summary
                assert 'threshold_sensitive' in stratum_summary
                assert 'always_non_significant' in stratum_summary
                assert 'stability_scores' in stratum_summary