"""
Unit tests for the ``code.main`` orchestrator.

The tests verify that the argument parser accepts the flags required
by the Quickstart documentation and that the module can be imported
without side effects.
"""

import sys

def test_parse_args(monkeypatch):
    """
    Ensure that ``--phase`` and ``--sample`` are parsed correctly.
    """
    # Simulate command‑line invocation
    monkeypatch.setattr(sys, "argv", ["prog", "--phase", "all", "--sample", "small"])
    from code.main import parse_args

    args = parse_args()
    assert args.phase == "all"
    assert args.sample == "small"