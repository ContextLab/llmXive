"""
Unit tests for the configuration module.
"""
import pytest
import sys
import os

# Add code directory to path if not already present
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code.config import load_config, validate_config, parse_cli_args
from unittest.mock import patch


class TestAlphaListCLI:
    """Tests for the --alpha-list CLI argument functionality (T034)."""

    def test_default_alpha_levels(self):
        """Verify default alpha levels are loaded correctly."""
        cfg = load_config()
        assert cfg["alpha_levels"] == [0.01, 0.05, 0.10]

    def test_parse_alpha_list_override(self):
        """Test that --alpha-list correctly overrides default alpha levels."""
        test_args = ["prog", "--alpha-list", "0.001,0.01,0.05,0.1"]
        with patch('sys.argv', test_args):
            cfg = parse_cli_args()
            assert cfg["alpha_levels"] == [0.001, 0.01, 0.05, 0.1]

    def test_parse_alpha_list_single_value(self):
        """Test parsing a single alpha value."""
        test_args = ["prog", "--alpha-list", "0.05"]
        with patch('sys.argv', test_args):
            cfg = parse_cli_args()
            assert cfg["alpha_levels"] == [0.05]

    def test_parse_alpha_list_invalid_format(self):
        """Test that invalid alpha list format raises ValueError."""
        test_args = ["prog", "--alpha-list", "0.05,invalid,0.1"]
        with patch('sys.argv', test_args):
            with pytest.raises(ValueError, match="Invalid alpha list format"):
                parse_cli_args()

    def test_parse_alpha_list_out_of_range(self):
        """Test that alpha values outside (0, 1) raise ValueError."""
        # Alpha = 0 is invalid
        test_args = ["prog", "--alpha-list", "0.0,0.05"]
        with patch('sys.argv', test_args):
            with pytest.raises(ValueError, match="Invalid alpha value"):
                parse_cli_args()

        # Alpha = 1 is invalid
        test_args = ["prog", "--alpha-list", "0.05,1.0"]
        with patch('sys.argv', test_args):
            with pytest.raises(ValueError, match="Invalid alpha value"):
                parse_cli_args()

        # Negative alpha is invalid
        test_args = ["prog", "--alpha-list", "-0.05,0.1"]
        with patch('sys.argv', test_args):
            with pytest.raises(ValueError, match="Invalid alpha value"):
                parse_cli_args()

    def test_alpha_list_with_other_args(self):
        """Test that --alpha-list works alongside other CLI arguments."""
        test_args = [
            "prog",
            "--icc-range", "0.0,0.1",
            "--icc-step", "0.1",
            "--alpha-list", "0.01,0.10"
        ]
        with patch('sys.argv', test_args):
            cfg = parse_cli_args()
            assert cfg["icc_range"] == [0.0, 0.1]
            assert cfg["icc_step"] == 0.1
            assert cfg["alpha_levels"] == [0.01, 0.10]

    def test_whitespace_handling_in_alpha_list(self):
        """Test that whitespace around values is handled correctly."""
        test_args = ["prog", "--alpha-list", " 0.01 , 0.05 , 0.10 "]
        with patch('sys.argv', test_args):
            cfg = parse_cli_args()
            assert cfg["alpha_levels"] == [0.01, 0.05, 0.10]
