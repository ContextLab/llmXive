import os
import shutil
import tempfile
import pytest
from pathlib import Path

# We need to add the code directory to the path to import the module
# assuming tests are run from the project root.
sys_path_backup = list(__import__('sys').path)
try:
    __import__('sys').path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
    from setup_directories import ensure_directory
finally:
    __import__('sys').path[:] = sys_path_backup


def test_ensure_directory_creates_and_adds_gitkeep(tmp_path):
    """
    Test that ensure_directory creates the directory and a .gitkeep file if it doesn't exist.
    """
    test_dir = tmp_path / "test_subdir"
    ensure_directory(str(test_dir))

    assert test_dir.exists(), f"Directory {test_dir} was not created."
    assert test_dir.is_dir(), f"{test_dir} is not a directory."

    gitkeep = test_dir / ".gitkeep"
    assert gitkeep.exists(), f".gitkeep file was not created in {test_dir}."
    assert gitkeep.is_file(), f"{gitkeep} is not a file."


def test_ensure_directory_idempotent(tmp_path):
    """
    Test that running ensure_directory on an existing directory doesn't fail or overwrite.
    """
    test_dir = tmp_path / "existing_dir"
    test_dir.mkdir()
    gitkeep = test_dir / ".gitkeep"
    gitkeep.write_text("original content")

    ensure_directory(str(test_dir))

    assert test_dir.exists()
    assert gitkeep.exists()
    assert gitkeep.read_text() == "original content", ".gitkeep content was modified."


def test_full_structure_creation(tmp_path):
    """
    Test the main logic of T001, T002, T003 by creating the specific paths.
    """
    # Temporarily change working directory to tmp_path to mimic project root
    old_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        # T001
        ensure_directory("data")
        ensure_directory("data/defects4j")
        assert (tmp_path / "data" / ".gitkeep").exists()
        assert (tmp_path / "data" / "defects4j" / ".gitkeep").exists()

        # T002
        ensure_directory("code")
        ensure_directory("code/utils")
        ensure_directory("code/models")
        assert (tmp_path / "code" / ".gitkeep").exists()
        assert (tmp_path / "code" / "utils" / ".gitkeep").exists()
        assert (tmp_path / "code" / "models" / ".gitkeep").exists()

        # T003
        ensure_directory("explanations")
        ensure_directory("state")
        ensure_directory("tests")
        assert (tmp_path / "explanations" / ".gitkeep").exists()
        assert (tmp_path / "state" / ".gitkeep").exists()
        assert (tmp_path / "tests" / ".gitkeep").exists()

    finally:
        os.chdir(old_cwd)
