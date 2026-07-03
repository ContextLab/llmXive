import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure src is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.chemistry import get_templates, classify_reaction, _match_reaction
from rdkit import Chem

class TestChemistry:
    """Tests for reaction classification logic."""

    @patch('src.utils.chemistry.load_config')
    def test_get_templates_success(self, mock_load_config):
        """Test successful loading of templates from config."""
        mock_config = {
            'reaction_templates': {
                'SN1': {'pattern': '[C:1]([O:2])>>[C:1]+[O:2]'},
                'SN2': {'pattern': '[C:1]([O:2])>>[C:1]=[O:2]'}
            }
        }
        mock_load_config.return_value = mock_config

        templates = get_templates()

        assert templates is not None
        assert 'SN1' in templates
        assert 'SN2' in templates
        assert templates['SN1']['pattern'] == '[C:1]([O:2])>>[C:1]+[O:2]'

    @patch('src.utils.chemistry.load_config')
    def test_get_templates_missing_key(self, mock_load_config):
        """Test handling of missing reaction_templates key."""
        mock_load_config.return_value = {}
        templates = get_templates()
        assert templates == {}

    def test_classify_reaction_no_templates(self):
        """Test classification when no templates are provided."""
        result = classify_reaction("CCO", templates={})
        assert result is None

    def test_classify_reaction_malformed_smiles(self):
        """Test handling of malformed SMILES."""
        # Mock a template that looks valid
        templates = {
            'Test': {'pattern': 'C'}
        }
        # Invalid SMILES
        result = classify_reaction("invalid_smiles_123", templates=templates)
        assert result is None

    @patch('src.utils.chemistry.load_config')
    def test_classify_reaction_match(self, mock_load_config):
        """Test that a matching reaction returns the correct class."""
        # Mock config with a simple pattern
        mock_load_config.return_value = {
            'reaction_templates': {
                'SN1': {'pattern': 'C'}
            }
        }

        # Simple molecule that matches 'C'
        result = classify_reaction("CCO")
        assert result == 'SN1'

    def test_classify_reaction_no_match(self):
        """Test that a non-matching reaction returns None."""
        # Pattern for a complex ring that won't match simple ethanol
        templates = {
            'Benzene': {'pattern': 'c1ccccc1'}
        }
        result = classify_reaction("CCO", templates=templates)
        assert result is None

    def test_match_reaction_with_reaction_smiles(self):
        """Test matching logic with reaction SMILES format."""
        # Pattern: A carbon attached to an oxygen
        pattern_smarts = '[C:1][O:2]'
        pattern = Chem.MolFromSmarts(pattern_smarts)
        
        # Reaction SMILES: Ethanol -> Ethyl cation (simplified representation)
        # Reactants: CCO
        reaction_smiles = "CCO>>[CH3][CH2]+.[OH]-"
        
        # This should match because reactants contain C-O
        result = _match_reaction(reaction_smiles, pattern)
        assert result is True

    def test_match_reaction_no_match(self):
        """Test matching logic when pattern does not fit."""
        # Pattern: Benzene ring
        pattern_smarts = 'c1ccccc1'
        pattern = Chem.MolFromSmarts(pattern_smarts)
        
        # Reaction SMILES: Ethanol
        reaction_smiles = "CCO>>CC"
        
        result = _match_reaction(reaction_smiles, pattern)
        assert result is False

    def test_classify_priority(self):
        """Test that the first matching template wins."""
        templates = {
            'First': {'pattern': 'C'},
            'Second': {'pattern': 'C'} # Same pattern
        }
        result = classify_reaction("CCO", templates=templates)
        assert result == 'First'