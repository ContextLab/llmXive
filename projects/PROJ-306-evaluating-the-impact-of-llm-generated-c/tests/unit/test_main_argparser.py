"""
Unit tests for the ``code/main.py`` argument parser.
These tests ensure that the parser accepts the required arguments
and supplies sensible defaults.
"""

import argparse
from pathlib import Path

from code.main import build_arg_parser

def test_default_arguments():
    parser = build_arg_parser()
    args = parser.parse_args([])  # no CLI overrides
    # Default dataset path
    expected_dataset = Path("data") / "benchmarks" / "processed" / "catalog.json"
    assert Path(args.dataset) == expected_dataset
    # Default model should be the fallback model defined in config
    from code.config import get_model_config
    assert args.model == get_model_config().fallback_model
    # Default batch size
    assert args.batch_size == 10
    # Default output directory
    expected_output = Path("data") / "coverage_reports"
    assert Path(args.output_dir) == expected_output

def test_overridden_arguments():
    parser = build_arg_parser()
    args = parser.parse_args(
        [
            "--dataset",
            "custom/catalog.json",
            "--model",
            "code-llama-7b",
            "--batch-size",
            "5",
            "--output-dir",
            "custom/coverage",
        ]
    )
    assert args.dataset == "custom/catalog.json"
    assert args.model == "code-llama-7b"
    assert args.batch_size == 5
    assert args.output_dir == "custom/coverage"