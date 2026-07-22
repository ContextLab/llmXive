import pytest
from src.cli.run_pipeline import create_parser, validate_args
import argparse

def test_parser_rejects_low_threshold():
    parser = create_parser()
    # argparse should raise SystemExit because the custom type rejects <0.75
    with pytest.raises(SystemExit):
        parser.parse_args(["--threshold", "0.5", "--species", "arabidopsis"])

def test_validate_args_raises_on_invalid_namespace():
    # Build a namespace manually that bypasses the argparse type check
    ns = argparse.Namespace(threshold=0.5, norm_method="TPM", seed=42, species="arabidopsis")
    with pytest.raises(ValueError):
        validate_args(ns)