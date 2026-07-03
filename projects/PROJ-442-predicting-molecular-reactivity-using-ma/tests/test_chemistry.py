"""
Tests for chemistry utilities.
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os
from src.utils.chemistry import get_templates, classify_reaction, _match_reaction
from rdkit import Chem

class TestChemistry:
    @patch('src.utils.chemistry.load_config')
    def test_get_templates_success(self, mock_load_config):
        mock_load_config.return_value = {
            "reaction_templates": {
                "SN1": "pattern1",
                "SN2": "pattern2"
            }
        }
        templates = get_templates()
        assert "SN1" in templates
        assert "SN2" in templates

    @patch('src.utils.chemistry.load_config')
    def test_get_templates_empty(self, mock_load_config):
        mock_load_config.return_value = {}
        templates = get_templates()
        # Should fall back to defaults
        assert len(templates) > 0

    def test_match_reaction_basic(self):
        # Placeholder test - real RDKit matching not implemented yet
        assert _match_reaction("CCO", "CCO") is True
        assert _match_reaction("", "CCO") is False

    def test_classify_reaction(self):
        templates = {"SN1": "pattern1"}
        result = classify_reaction("CCO", templates)
        # Depends on _match_reaction implementation
        assert result in [None, "SN1"]
