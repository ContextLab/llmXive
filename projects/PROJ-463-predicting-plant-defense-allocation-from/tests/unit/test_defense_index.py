"""
Unit tests for Defense Allocation Index calculation (T039).
"""
import pytest
import pandas as pd
import numpy as np
import json
import tempfile
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.analysis.defense_index import (
    classify_trait,
    standardize_traits,
    calculate_dai,
    load_trait_data
)

class TestClassifyTrait:
    """Tests for trait classification logic."""

    def test_chemical_trait_recognition(self):
        """Test that chemical traits are correctly identified."""
        chemical_traits = [
            'alkaloid content',
            'terpenoid levels',
            'phenolic compounds',
            'glucosinolate concentration',
            'tannin content'
        ]
        for trait in chemical_traits:
            assert classify_trait(trait) == 'chemical', f"Failed to classify {trait} as chemical"

    def test_physical_trait_recognition(self):
        """Test that physical traits are correctly identified."""
        physical_traits = [
            'thorn density',
            'leaf thickness',
            'trichome count',
            'leaf toughness',
            'spine length'
        ]
        for trait in physical_traits:
            assert classify_trait(trait) == 'physical', f"Failed to classify {trait} as physical"

    def test_ambiguous_trait_classification(self):
        """Test that ambiguous traits return None."""
        ambiguous_traits = [
            'growth rate',
            'leaf area',
            'plant height'
        ]
        for trait in ambiguous_traits:
            assert classify_trait(trait) is None, f"Ambiguous trait {trait} was classified"

class TestStandardizeTraits:
    """Tests for trait standardization."""

    def test_z_score_calculation(self):
        """Test that z-scores are calculated correctly."""
        data = {
            'species_name': ['A', 'A', 'A', 'B', 'B', 'B'],
            'trait_type': ['chemical', 'chemical', 'chemical', 'chemical', 'chemical', 'chemical'],
            'trait_value': [10, 20, 30, 100, 200, 300]
        }
        df = pd.DataFrame(data)
        
        standardized = standardize_traits(df)
        
        # For species A: mean=20, std=10, z-scores should be [-1, 0, 1]
        # For species B: mean=200, std=100, z-scores should be [-1, 0, 1]
        
        species_a = standardized[standardized['species_name'] == 'A']
        species_a_z = sorted(species_a['z_score'].tolist())
        
        # Check that z-scores are approximately [-1, 0, 1]
        assert np.isclose(species_a_z[0], -1, atol=0.01), "Z-score calculation incorrect for species A"
        assert np.isclose(species_a_z[1], 0, atol=0.01), "Z-score calculation incorrect for species A"
        assert np.isclose(species_a_z[2], 1, atol=0.01), "Z-score calculation incorrect for species A"

    def test_single_trait_handling(self):
        """Test that single traits get z-score of 0."""
        data = {
            'species_name': ['A', 'B'],
            'trait_type': ['chemical', 'chemical'],
            'trait_value': [10, 20]
        }
        df = pd.DataFrame(data)
        
        standardized = standardize_traits(df)
        
        # When only one trait per species, z-score should be 0
        assert all(standardized['z_score'] == 0), "Single trait should have z-score of 0"

class TestCalculateDAI:
    """Tests for DAI calculation."""

    def test_dai_calculation_basic(self):
        """Test basic DAI calculation."""
        trait_data = {
            'primary_source_results': {
                'Species_A': {
                    'traits': [
                        {'trait_name': 'alkaloid content', 'trait_value': 100},
                        {'trait_name': 'thorn density', 'trait_value': 50}
                    ]
                }
            }
        }
        
        dai_df = calculate_dai(trait_data)
        
        assert len(dai_df) == 1, "Should have one species"
        assert 'dai' in dai_df.columns, "DAI column should exist"
        assert 'species_name' in dai_df.columns, "Species name column should exist"

    def test_dai_with_multiple_traits(self):
        """Test DAI calculation with multiple chemical and physical traits."""
        trait_data = {
            'primary_source_results': {
                'Species_A': {
                    'traits': [
                        {'trait_name': 'alkaloid content', 'trait_value': 100},
                        {'trait_name': 'terpenoid levels', 'trait_value': 200},
                        {'trait_name': 'thorn density', 'trait_value': 50},
                        {'trait_name': 'leaf thickness', 'trait_value': 10}
                    ]
                }
            }
        }
        
        dai_df = calculate_dai(trait_data)
        
        assert len(dai_df) == 1
        assert not np.isnan(dai_df['dai'].iloc[0]), "DAI should not be NaN"

    def test_dai_with_fallback_data(self):
        """Test DAI calculation including fallback data."""
        trait_data = {
            'primary_source_results': {
                'Species_A': {
                    'traits': [
                        {'trait_name': 'alkaloid content', 'trait_value': 100}
                    ]
                }
            },
            'fallback_results': {
                'Species_A': {
                    'traits': [
                        {'trait_name': 'thorn density', 'trait_value': 50}
                    ]
                }
            }
        }
        
        dai_df = calculate_dai(trait_data)
        
        assert len(dai_df) == 1
        assert not dai_df.empty

    def test_empty_trait_data(self):
        """Test handling of empty trait data."""
        trait_data = {
            'primary_source_results': {},
            'fallback_results': {}
        }
        
        dai_df = calculate_dai(trait_data)
        
        assert dai_df.empty, "Should return empty DataFrame for empty input"

class TestIntegration:
    """Integration tests for the full pipeline."""

    def test_full_pipeline_with_mock_data(self, tmp_path):
        """Test the full DAI calculation pipeline with mock data."""
        # Create mock trait data
        trait_data = {
            'primary_source_results': {
                'Arabidopsis_thaliana': {
                    'traits': [
                        {'trait_name': 'glucosinolate content', 'trait_value': 150},
                        {'trait_name': 'trichome density', 'trait_value': 20}
                    ]
                },
                'Zea_mays': {
                    'traits': [
                        {'trait_name': 'tannin content', 'trait_value': 80},
                        {'trait_name': 'leaf toughness', 'trait_value': 30}
                    ]
                }
            }
        }
        
        # Write to temp file
        trait_file = tmp_path / 'trait_fallback_summary.json'
        with open(trait_file, 'w') as f:
            json.dump(trait_data, f)
        
        # Load and process
        loaded_data = load_trait_data(trait_file)
        dai_df = calculate_dai(loaded_data)
        
        assert len(dai_df) == 2
        assert 'Arabidopsis_thaliana' in dai_df['species_name'].values
        assert 'Zea_mays' in dai_df['species_name'].values
        assert all(dai_df['dai'].notna())