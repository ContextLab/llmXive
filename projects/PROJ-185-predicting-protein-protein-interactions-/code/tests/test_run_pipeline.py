"""
Unit tests for the CLI entry point (T007).
"""

import pytest
import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.cli.run_pipeline import create_parser, validate_args


class TestCLIParsing:
    """Tests for argument parsing logic."""

    def test_default_args(self):
        """Test that default values are set correctly."""
        parser = create_parser()
        args = parser.parse_args(["run", "--threshold", "0.8"])
        
        assert args.command == "run"
        assert args.threshold == 0.8
        assert args.norm_method == "TPM"
        assert args.seed == 42
        assert args.species == "arabidopsis"

    def test_custom_args(self):
        """Test custom argument values."""
        parser = create_parser()
        args = parser.parse_args([
            "evaluate",
            "--threshold", "0.9",
            "--norm-method", "VST",
            "--seed", "123",
            "--species", "rice",
            "--output-dir", "my_results"
        ])
        
        assert args.command == "evaluate"
        assert args.threshold == 0.9
        assert args.norm_method == "VST"
        assert args.seed == 123
        assert args.species == "rice"
        assert args.output_dir == "my_results"

    def test_invalid_norm_method(self):
        """Test that invalid normalization method raises error."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["run", "--threshold", "0.8", "--norm-method", "INVALID"])


class TestValidation:
    """Tests for argument validation logic."""

    def test_threshold_below_minimum(self):
        """Test that threshold < 0.75 raises ValueError."""
        parser = create_parser()
        args = parser.parse_args(["run", "--threshold", "0.5"])
        
        with pytest.raises(ValueError) as exc_info:
            validate_args(args)
        
        assert "threshold must be >= 0.75" in str(exc_info.value).lower()

    def test_threshold_at_minimum(self):
        """Test that threshold == 0.75 is valid."""
        parser = create_parser()
        args = parser.parse_args(["run", "--threshold", "0.75"])
        
        # Should not raise
        validate_args(args)

    def test_threshold_above_minimum(self):
        """Test that threshold > 0.75 is valid."""
        parser = create_parser()
        args = parser.parse_args(["run", "--threshold", "0.95"])
        
        # Should not raise
        validate_args(args)

    def test_negative_seed(self):
        """Test that negative seed raises ValueError."""
        parser = create_parser()
        args = parser.parse_args(["run", "--threshold", "0.8", "--seed", "-1"])
        
        with pytest.raises(ValueError) as exc_info:
            validate_args(args)
        
        assert "seed must be non-negative" in str(exc_info.value).lower()

    def test_zero_seed(self):
        """Test that zero seed is valid."""
        parser = create_parser()
        args = parser.parse_args(["run", "--threshold", "0.8", "--seed", "0"])
        
        # Should not raise
        validate_args(args)