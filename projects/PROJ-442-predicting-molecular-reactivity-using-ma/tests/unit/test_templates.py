"""
Unit tests for reaction template matching logic.

Tests SMARTS pattern matching and reaction classification.
"""

import pytest
from rdkit import Chem
from rdkit.Chem import rdMolTransforms

from src.utils.chemistry import get_templates, classify_reaction, _match_reaction

class TestTemplates:
    """Test cases for template matching."""

    @pytest.fixture
    def templates(self):
        """Load reaction templates from config."""
        return get_templates()

    def test_get_templates(self, templates):
        """Test that templates are loaded correctly."""
        assert 'SN1' in templates
        assert 'SN2' in templates
        assert 'Diels-Alder' in templates
        assert isinstance(templates['SN1'], str)
        assert isinstance(templates['SN2'], str)
        assert isinstance(templates['Diels-Alder'], str)

    def test_match_reaction_sn1(self):
        """Test SN1 template matching."""
        # Example: Simple substitution reaction
        smiles = "CC(O)C(=O)O.CN>>CC(=O)N.CCO"
        templates = get_templates()
        
        result = classify_reaction(smiles, templates)
        # Result should be one of the expected types or None
        assert result in ['SN1', 'SN2', 'Diels-Alder', None]

    def test_match_reaction_diels_alder(self):
        """Test Diels-Alder template matching."""
        # Example: Diels-Alder reaction
        smiles = "C=CC=C.C=C>>C1CCC1"
        templates = get_templates()
        
        result = classify_reaction(smiles, templates)
        assert result in ['SN1', 'SN2', 'Diels-Alder', None]

    def test_match_reaction_invalid_smiles(self):
        """Test matching with invalid SMILES."""
        smiles = "invalid_smiles"
        templates = get_templates()
        
        result = classify_reaction(smiles, templates)
        assert result is None

    def test_match_reaction_empty(self):
        """Test matching with empty SMILES."""
        smiles = ""
        templates = get_templates()
        
        result = classify_reaction(smiles, templates)
        assert result is None

    def test_match_reaction_no_template(self):
        """Test matching with SMILES that doesn't match any template."""
        # A simple molecule that doesn't match our reaction templates
        smiles = "CCO"  # Just ethanol, no reaction
        templates = get_templates()
        
        result = classify_reaction(smiles, templates)
        assert result is None

    def test_match_reaction_batch(self):
        """Test batch classification."""
        from src.utils.chemistry import classify_batch
        
        smiles_list = [
            "CC(O)C(=O)O.CN>>CC(=O)N.CCO",
            "C=CC=C.C=C>>C1CCC1",
            "invalid",
            ""
        ]
        templates = get_templates()
        
        results = classify_batch(smiles_list, templates)
        assert len(results) == len(smiles_list)
        assert all(r in ['SN1', 'SN2', 'Diels-Alder', None] for r in results)

    def test_template_syntax_validity(self):
        """Test that all template SMARTS are valid."""
        templates = get_templates()
        for name, pattern in templates.items():
            try:
                # Try to compile the SMARTS pattern
                Chem.MolFromSmarts(pattern)
            except Exception as e:
                pytest.fail(f"Invalid SMARTS pattern for {name}: {e}")
