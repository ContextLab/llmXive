"""
Unit tests for pre-commit hooks.
"""
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from pre_commit_hooks.check_large_files import check_large_files
from pre_commit_hooks.check_inefficient_imports import check_inefficient_imports

class TestCheckLargeFiles:
    def test_small_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"x" * 1024)  # 1KB
            temp_path = f.name
        
        try:
            result = check_large_files([temp_path])
            assert result == 0, "Small file should pass."
        finally:
            os.unlink(temp_path)

    def test_large_file(self):
        # Create a file larger than 10MB
        size = 11 * 1024 * 1024
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"x" * size)
            temp_path = f.name
        
        try:
            result = check_large_files([temp_path])
            assert result == 1, "Large file should fail."
        finally:
            os.unlink(temp_path)

    def test_nonexistent_file(self):
        result = check_large_files(["/nonexistent/file.txt"])
        assert result == 0, "Nonexistent files should be ignored."

class TestCheckInefficientImports:
    def test_good_imports(self):
        code = """
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
"""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode='w') as f:
            f.write(code)
            temp_path = f.name
        
        try:
            result = check_inefficient_imports([temp_path])
            assert result == 0, "Good imports should pass."
        finally:
            os.unlink(temp_path)

    def test_bad_alias(self):
        code = """
import pandas
import numpy
"""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode='w') as f:
            f.write(code)
            temp_path = f.name
        
        try:
            result = check_inefficient_imports([temp_path])
            assert result == 1, "Missing alias should fail."
        finally:
            os.unlink(temp_path)

    def test_star_import(self):
        code = """
from numpy import *
"""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode='w') as f:
            f.write(code)
            temp_path = f.name
        
        try:
            result = check_inefficient_imports([temp_path])
            assert result == 1, "Star import should fail."
        finally:
            os.unlink(temp_path)

    def test_heavy_lib(self):
        code = """
import tensorflow
"""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode='w') as f:
            f.write(code)
            temp_path = f.name
        
        try:
            result = check_inefficient_imports([temp_path])
            # Depending on strictness, this might be a warning or error.
            # Our implementation returns 1 on any warning.
            assert result == 1, "Heavy lib import should trigger warning/fail."
        finally:
            os.unlink(temp_path)