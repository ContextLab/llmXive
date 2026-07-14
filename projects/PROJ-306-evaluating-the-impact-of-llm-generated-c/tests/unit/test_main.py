"""Basic sanity test for the main orchestration script.

The test checks that the argument parser is correctly constructed and that
required arguments are enforced.  It does **not** run the full pipeline
(which would require external model calls); those are covered by the
integration test suite.
"""

import argparse
import pytest

from code.main import build_arg_parser


def test_parser_requires_dataset():
    parser = build_arg_parser()
    # No arguments – parsing should raise a SystemExit due to the required flag.
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_parser_parses_all_options():
    parser = build_arg_parser()
    args = parser.parse_args(
        ["--dataset", "data/benchmarks/processed/catalog.json", "--model", "gpt-4", "--batch-size", "5"]
    )
    assert args.dataset == "data/benchmarks/processed/catalog.json"
    assert args.model == "gpt-4"
    assert args.batch_size == 5