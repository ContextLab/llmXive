"""
Unit tests for power_analysis.py
"""
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.power_analysis import (
    get_nppn_species_list,
    get_try_species_list,
    calculate_sample_size,
    main,
    MIN_OVERLAP_SPECIES
)

class TestPowerAnalysis:

    def test_calculate_sample_size_returns_positive_int(self):
        """Test that calculate_sample_size returns a positive integer."""
        n = calculate_sample_size(effect_size=0.5, alpha=0.05, power=0.80)
        assert isinstance(n, int)
        assert n > 0

    def test_calculate_sample_size_varies_with_effect_size(self):
        """Test that sample size changes with effect size."""
        n_small_effect = calculate_sample_size(effect_size=0.2, alpha=0.05, power=0.80)
        n_large_effect = calculate_sample_size(effect_size=0.8, alpha=0.05, power=0.80)
        # Smaller effect size should require larger sample size
        assert n_small_effect > n_large_effect

    @patch('code.power_analysis.get_nppn_species_list')
    @patch('code.power_analysis.get_try_species_list')
    def test_main_halts_when_overlap_below_threshold(self, mock_try, mock_nppn):
        """Test that main exits with error when overlap < 55."""
        mock_nppn.return_value = {'species_a', 'species_b'}
        mock_try.return_value = {'species_b', 'species_c'}
        # Overlap is 1, which is < 55

        # We expect sys.exit(1) to be called
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

        # Check that report file was created
        report_path = Path("state/power_analysis_report.yaml")
        assert report_path.exists()

        with open(report_path, 'r') as f:
            report = yaml.safe_load(f)

        assert report['status'] == 'failed'
        assert report['overlap_count'] == 1
        assert report['minimum_required'] == MIN_OVERLAP_SPECIES

    @patch('code.power_analysis.get_nppn_species_list')
    @patch('code.power_analysis.get_try_species_list')
    def test_main_succeeds_when_overlap_above_threshold(self, mock_try, mock_nppn):
        """Test that main succeeds when overlap >= 55."""
        # Create 60 overlapping species
        overlap_species = {f'species_{i}' for i in range(60)}
        mock_nppn.return_value = overlap_species
        mock_try.return_value = overlap_species

        # We expect no exception and success report
        try:
            main()
        except SystemExit as e:
            # Should not exit
            pytest.fail(f"main() exited with code {e.code} but should have succeeded")

        # Check that report file was created
        report_path = Path("state/power_analysis_report.yaml")
        assert report_path.exists()

        with open(report_path, 'r') as f:
            report = yaml.safe_load(f)

        assert report['status'] == 'success'
        assert report['overlap_species_count'] == 60
        assert report['required_sample_size'] is not None

    def test_get_nppn_species_list_returns_set(self):
        """Test that get_nppn_species_list returns a set."""
        species = get_nppn_species_list()
        assert isinstance(species, set)

    def test_get_try_species_list_returns_set(self):
        """Test that get_try_species_list returns a set."""
        species = get_try_species_list()
        assert isinstance(species, set)
