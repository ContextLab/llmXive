"""Verify the project structure required by T001 exists on disk."""

from pathlib import Path

from llmxive_toolkit import paths

from setup_project_structure import REQUIRED_DIRS, create_structure


def test_all_required_directories_exist():
    create_structure()
    for rel in REQUIRED_DIRS:
        assert paths.path(rel).is_dir(), f"missing directory: {rel}"


def test_gitkeep_markers_present():
    create_structure()
    for rel in REQUIRED_DIRS:
        assert (paths.path(rel) / ".gitkeep").exists(), f"missing .gitkeep in {rel}"


def test_key_top_level_folders():
    for rel in ("code", "tests", "data", "results", "specs"):
        assert paths.path(rel).is_dir()