import os
from pathlib import Path

from create_skeleton import main as create_skeleton_main

def test_create_skeleton_creates_required_directories(tmp_path, monkeypatch):
    """
    Verify that the skeleton creation script creates all required top‑level
    directories under the project root.
    """
    # Monkeypatch the paths utilities to point inside the temporary directory
    from llmxive_toolkit import paths as toolkit_paths
    monkeypatch.setattr(toolkit_paths, "root", tmp_path)

    # Run the skeleton creation script
    create_skeleton_main()

    required_dirs = [
        "data/raw",
        "data/processed",
        "data/results",
        "figures",
        "code/models",
        "code/metrics",
        "code/stats",
        "code/utils",
        "tests/unit",
        "tests/integration",
        "results"
    ]

    for rel_dir in required_dirs:
        dir_path = tmp_path / rel_dir
        assert dir_path.is_dir(), f"Expected directory {dir_path} to exist"
