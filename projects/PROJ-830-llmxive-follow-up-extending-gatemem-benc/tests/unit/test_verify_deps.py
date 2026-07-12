"""
Unit tests for verify_deps.py
"""

import os
import tempfile
from pathlib import Path
import pytest

# Import the functions from the script
# We need to import from the parent directory of tests
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from verify_deps import parse_requirements, verify_dependencies, FORBIDDEN_PACKAGES


class TestParseRequirements:
    def test_parse_simple_package(self):
        content = "transformers==4.35.0\n"
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(content)
            f.flush()
            path = Path(f.name)

        try:
            packages = parse_requirements(path)
            assert len(packages) == 1
            assert packages[0]["name"] == "transformers"
            assert packages[0]["version_spec"] == "==4.35.0"
        finally:
            os.unlink(path)

    def test_parse_package_with_extras(self):
        content = "torch[cpu]==2.0.0\n"
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(content)
            f.flush()
            path = Path(f.name)

        try:
            packages = parse_requirements(path)
            assert len(packages) == 1
            assert packages[0]["name"] == "torch"
            assert packages[0]["extras"] == "[cpu]"
        finally:
            os.unlink(path)

    def test_parse_comments_and_blanks(self):
        content = """# This is a comment
        pandas>=1.5.0

        numpy==1.24.0
        """
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(content)
            f.flush()
            path = Path(f.name)

        try:
            packages = parse_requirements(path)
            assert len(packages) == 2
            names = [p["name"] for p in packages]
            assert "pandas" in names
            assert "numpy" in names
        finally:
            os.unlink(path)

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            parse_requirements(Path("/nonexistent/path/requirements.txt"))


class TestVerifyDependencies:
    def test_no_forbidden_packages(self):
        packages = [
            {"name": "transformers", "version_spec": "==4.35.0", "raw_line": "transformers==4.35.0", "extras": "", "line_num": 1},
            {"name": "torch", "version_spec": "+cpu", "raw_line": "torch+cpu", "extras": "", "line_num": 2},
            {"name": "pandas", "version_spec": ">=1.5.0", "raw_line": "pandas>=1.5.0", "extras": "", "line_num": 3},
        ]

        results = verify_dependencies(packages)
        assert results["success"] is True
        assert len(results["errors"]) == 0
        assert len(results["forbidden_found"]) == 0

    def test_forbidden_bitsandbytes(self):
        packages = [
            {"name": "bitsandbytes", "version_spec": "", "raw_line": "bitsandbytes", "extras": "", "line_num": 1},
        ]

        results = verify_dependencies(packages)
        assert results["success"] is False
        assert len(results["errors"]) == 1
        assert "bitsandbytes" in results["forbidden_found"]

    def test_torch_without_cpu_flag(self):
        packages = [
            {"name": "torch", "version_spec": "", "raw_line": "torch", "extras": "", "line_num": 1},
        ]

        results = verify_dependencies(packages)
        assert results["success"] is False
        assert len(results["errors"]) == 1
        assert "torch" in results["errors"][0]

    def test_torch_with_cpu_flag(self):
        packages = [
            {"name": "torch", "version_spec": "+cpu", "raw_line": "torch+cpu", "extras": "", "line_num": 1},
        ]

        results = verify_dependencies(packages)
        assert results["success"] is True
        assert len(results["errors"]) == 0

    def test_multiple_forbidden_packages(self):
        packages = [
            {"name": "bitsandbytes", "version_spec": "", "raw_line": "bitsandbytes", "extras": "", "line_num": 1},
            {"name": "cudatoolkit", "version_spec": "", "raw_line": "cudatoolkit", "extras": "", "line_num": 2},
        ]

        results = verify_dependencies(packages)
        assert results["success"] is False
        assert len(results["errors"]) == 2
        assert "bitsandbytes" in results["forbidden_found"]
        assert "cudatoolkit" in results["forbidden_found"]