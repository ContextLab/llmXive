"""
Contract tests for directory setup functionality.
Ensures the directory structure meets the project requirements.
"""
import os
from pathlib import Path
import tempfile

import sys
from pathlib import Path

# Add the code directory to the path
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_directories import create_directories


def test_contract_directory_structure_exists():
    """
    Contract test: Verify that all required directories exist after setup.
    This test ensures the project structure matches the specification.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create base structure
        (tmp_path / "code").mkdir()
        (tmp_path / "data").mkdir()
        (tmp_path / "tests").mkdir()

        # Expected structure
        required_dirs = {
            "code": [
                "data_download",
                "manipulation",
                "preprocess",
                "analysis",
                "visualization",
                "utils",
                "pipeline"
            ],
            "data": [
                "raw-fmri",
                "processed-fmri",
                "behavioral",
                "results"
            ],
            "tests": [
                "unit",
                "integration",
                "contract"
            ]
        }

        code_path = tmp_path / "code"
        data_path = tmp_path / "data"
        tests_path = tmp_path / "tests"

        # Create and verify directories
        for section, subdirs in required_dirs.items():
            base = {
                "code": code_path,
                "data": data_path,
                "tests": tests_path
            }[section]

            for subdir in subdirs:
                dir_path = base / subdir
                dir_path.mkdir(parents=True, exist_ok=True)

                # Verify directory exists
                assert dir_path.exists(), f"Required directory {dir_path} does not exist"

                # Verify appropriate init/gitkeep files
                if section in ["code", "tests"]:
                    init_file = dir_path / "__init__.py"
                    init_file.write_text(f'"""{subdir}."""\n')
                    assert init_file.exists(), f"__init__.py missing for {dir_path}"
                elif section == "data":
                    gitkeep = dir_path / ".gitkeep"
                    gitkeep.write_text("")
                    assert gitkeep.exists(), f".gitkeep missing for {dir_path}"

def test_contract_package_importability():
    """
    Contract test: Verify that all created packages can be imported.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create base structure
        code_path = tmp_path / "code"
        code_path.mkdir()

        # Create packages with __init__.py
        packages = [
            "data_download",
            "manipulation",
            "preprocess",
            "analysis",
            "visualization",
            "utils",
            "pipeline"
        ]

        for pkg in packages:
            pkg_path = code_path / pkg
            pkg_path.mkdir(parents=True, exist_ok=True)
            init_file = pkg_path / "__init__.py"
            init_file.write_text(f'"""{pkg} module."""\n')

        # Add code path to sys.path
        sys.path.insert(0, str(code_path))

        try:
            # Try importing each package
            for pkg in packages:
                try:
                    __import__(pkg)
                except ImportError as e:
                    raise AssertionError(f"Package {pkg} cannot be imported: {e}")
        finally:
            # Clean up sys.path
            sys.path.remove(str(code_path))