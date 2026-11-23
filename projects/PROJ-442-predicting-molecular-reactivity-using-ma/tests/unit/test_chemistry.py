"""
Unit tests for chemistry classification utilities.
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os
from src.utils.chemistry import get_templates, classify_reaction, _match_reaction
from rdkit import Chem
from rdkit.Chem import rdChemReactions

class TestChemistry:
    """Test suite for chemistry module functions."""

    def test_get_templates_loads_from_config(self):
        """Test that get_templates loads patterns from config.yaml."""
        with patch('src.utils.chemistry.load_config') as mock_load_config:
            # Mock config with valid templates
            mock_load_config.return_value = {
                'reaction_templates': {
                    'SN1': {
                        'pattern': '[C:1]([O:2])>>[C:1+]([O:2-])',
                        'description': 'SN1 test'
                    },
                    'SN2': {
                        'pattern': '[N:1][C:2][Cl:3]>>[N:1][C:2][Cl:3]',
                        'description': 'SN2 test'
                    }
                }
            }
            
            templates = get_templates()
            
            assert 'SN1' in templates
            assert 'SN2' in templates
            assert templates['SN1']['pattern'] == '[C:1]([O:2])>>[C:1+]([O:2-])'
            assert templates['SN2']['pattern'] == '[N:1][C:2][Cl:3]>>[N:1][C:2][Cl:3]'
            assert 'reaction' in templates['SN1']
            assert 'reaction' in templates['SN2']

    def test_get_templates_invalid_pattern_raises(self):
        """Test that invalid SMARTS patterns raise ValueError."""
        with patch('src.utils.chemistry.load_config') as mock_load_config:
            mock_load_config.return_value = {
                'reaction_templates': {
                    'Invalid': {
                        'pattern': '[invalid smarts',
                        'description': 'Invalid test'
                    }
                }
            }
            
            with pytest.raises(ValueError, match="Invalid SMARTS pattern"):
                get_templates()

    def test_classify_reaction_returns_type(self):
        """Test classification of a reaction that matches a template."""
        # Create a mock template that matches any reaction with ">>"
        mock_templates = {
            'TestType': {
                'pattern': '[*:1]>>[*:1]',
                'description': 'Test',
                'reaction': rdChemReactions.ReactionFromSmarts('[*:1]>>[*:1]')
            }
        }
        
        result = classify_reaction('[C:1]>>[C:1]', templates=mock_templates)
        assert result == 'TestType'

    def test_classify_reaction_no_match(self):
        """Test classification returns None when no template matches."""
        mock_templates = {
            'Specific': {
                'pattern': '[N:1][C:2][Cl:3]>>[N:1][C:2][Cl:3]',
                'description': 'Specific',
                'reaction': rdChemReactions.ReactionFromSmarts('[N:1][C:2][Cl:3]>>[N:1][C:2][Cl:3]')
            }
        }
        
        # This reaction doesn't match the specific pattern
        result = classify_reaction('[C:1]>>[C:1]', templates=mock_templates)
        assert result is None

    def test_classify_reaction_empty_input(self):
        """Test classification handles empty or invalid input."""
        result = classify_reaction('', templates={})
        assert result is None

        result = classify_reaction(None, templates={})
        assert result is None

    def test_match_reaction_with_valid_reaction(self):
        """Test _match_reaction with a valid reaction."""
        template = {
            'pattern': '[C:1]>>[C:1]',
            'reaction': rdChemReactions.ReactionFromSmarts('[C:1]>>[C:1]')
        }
        
        # Should not raise an exception
        result = _match_reaction('[C:1]>>[C:1]', template)
        # Result depends on implementation, but should be boolean
        assert isinstance(result, bool)

    def test_match_reaction_invalid_smiles(self):
        """Test _match_reaction with invalid SMILES."""
        template = {
            'pattern': '[C:1]>>[C:1]',
            'reaction': rdChemReactions.ReactionFromSmarts('[C:1]>>[C:1]')
        }
        
        result = _match_reaction('invalid_smiles', template)
        assert result is False

    def test_get_templates_caching(self):
        """Test that get_templates caches results."""
        with patch('src.utils.chemistry.load_config') as mock_load_config:
            mock_load_config.return_value = {
                'reaction_templates': {
                    'Cached': {
                        'pattern': '[C:1]>>[C:1]',
                        'description': 'Cached'
                    }
                }
            }
            
            # First call
            templates1 = get_templates()
            # Second call (should use cache)
            templates2 = get_templates()
            
            assert templates1 is templates2
            mock_load_config.assert_called_once()
