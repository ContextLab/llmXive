import os
import pytest
from llmxive_toolkit import paths
from create_layout import main as create_layout_main

def test_create_layout_creates_config(tmp_path, monkeypatch):
    """
    Run ``create_layout.main`` in an isolated temporary directory and verify
    that ``code/config.yaml`` exists afterwards.
    """
    # Redirect the toolkit paths to the temporary directory
    monkeypatch.setattr(paths, "root", tmp_path)
    # Ensure the helper creates all needed sub‑folders inside the temp dir
    create_layout_main()
    config_path = paths.code("config.yaml")
    assert config_path.is_file(), f"Config file not found at {config_path}"