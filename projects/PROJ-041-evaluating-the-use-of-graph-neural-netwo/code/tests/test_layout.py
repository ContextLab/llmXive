"""
test_layout.py
----------------

Tests that the project layout creation script generates the expected
configuration file at ``code/config.yaml``.
"""

import os

from llmxive_toolkit import paths
from create_layout import main as create_layout_main


def test_create_layout_creates_config(tmp_path, monkeypatch):
    """
    Run ``create_layout.main`` in an isolated temporary directory and verify
    that ``code/config.yaml`` exists afterwards.
    """
    # Change working directory to a temporary folder
    monkeypatch.chdir(tmp_path)

    # Execute the layout creation script
    create_layout_main()

    # Expected config path
    config_path = paths.code("config.yaml")
    assert config_path.is_file(), f"Config file not found at {config_path}"
