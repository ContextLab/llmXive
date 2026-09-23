import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from power_analysis import get_nppn_species_list, get_try_species_list, calculate_sample_size, MIN_SPECIES_THRESHOLD

class TestPowerAnalysis:
    
    def test_get_nppn_species_list_returns_set(self):
        """Test that NPPN species list is returned as a set."""
        with patch('power_analysis.get_nppn_species_list_from_fetch') as mock_fetch:
            mock_fetch.return_value = ['Arabidopsis thaliana', 'Zea mays', 'Oryza sativa']
            result = get_nppn_species_list()
            assert isinstance(result, set)
            assert len(result) == 3
            assert 'Arabidopsis thaliana' in result

    def test_get_try_species_list_returns_set(self):
        """Test that TRY species list is returned as a set."""
        with patch('power_analysis.get_try_species_list_internal') as mock_fetch:
            mock_fetch.return_value = ['Arabidopsis thaliana', 'Solanum lycopersicum', 'Glycine max']
            result = get_try_species_list()
            assert isinstance(result, set)
            assert len(result) == 3
            assert 'Arabidopsis thaliana' in result

    def test_calculate_sample_size_raises_error_when_overlap_below_threshold(self):
        """Test that calculate_sample_size raises ValueError when overlap < 55."""
        nppn_species = {'species_' + str(i) for i in range(20)}
        try_species = {'species_' + str(i) for i in range(20)}  # Only 20 overlap
        
        with pytest.raises(ValueError) as excinfo:
            calculate_sample_size(nppn_species, try_species)
        
        assert "Insufficient species for power analysis" in str(excinfo.value)
        assert "N < 55" in str(excinfo.value)

    def test_calculate_sample_size_returns_valid_results_when_overlap_above_threshold(self):
        """Test that calculate_sample_size returns valid results when overlap >= 55."""
        # Create 60 overlapping species
        nppn_species = {'species_' + str(i) for i in range(60)}
        try_species = {'species_' + str(i) for i in range(60)}
        
        result = calculate_sample_size(nppn_species, try_species)
        
        assert result['status'] == 'success'
        assert result['overlap_species_count'] == 60
        assert result['overlap_species_count'] >= MIN_SPECIES_THRESHOLD
        assert 'total_sample_size_required' in result
        assert result['total_sample_size_required'] > 0
        assert 'n_per_group' in result
        assert result['n_per_group'] > 0

    def test_calculate_sample_size_includes_expected_fields(self):
        """Test that result dictionary contains all expected fields."""
        nppn_species = {'species_' + str(i) for i in range(60)}
        try_species = {'species_' + str(i) for i in range(60)}
        
        result = calculate_sample_size(nppn_species, try_species)
        
        expected_fields = [
            'nppn_species_count',
            'try_species_count',
            'overlap_species_count',
            'overlap_species_list',
            'effect_size_f2',
            'alpha',
            'power_target',
            'n_per_group',
            'total_sample_size_required',
            'status',
            'message'
        ]
        
        for field in expected_fields:
            assert field in result, f"Missing field: {field}"

    def test_calculate_sample_size_with_partial_overlap(self):
        """Test with partial overlap between NPPN and TRY species."""
        nppn_species = {'species_' + str(i) for i in range(100)}
        try_species = {'species_' + str(i) for i in range(50, 150)}  # 50 overlap (50-99)
        
        with pytest.raises(ValueError) as excinfo:
            calculate_sample_size(nppn_species, try_species)
        
        assert "Insufficient species for power analysis" in str(excinfo.value)
        assert "Found 50" in str(excinfo.value)

    def test_calculate_sample_size_with_exactly_threshold(self):
        """Test with exactly 55 overlapping species."""
        nppn_species = {'species_' + str(i) for i in range(55)}
        try_species = {'species_' + str(i) for i in range(55)}
        
        result = calculate_sample_size(nppn_species, try_species)
        
        assert result['status'] == 'success'
        assert result['overlap_species_count'] == 55
        assert result['overlap_species_count'] >= MIN_SPECIES_THRESHOLD
        assert 'total_sample_size_required' in result
        assert result['total_sample_size_required'] > 0
