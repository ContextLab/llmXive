import pytest
import tempfile
import os
from pathlib import Path
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.pipeline.static_analysis_check import check_file_integrity, FORBIDDEN_NAMES

class TestStaticAnalysisCheck:
    """Tests for the static analysis integrity check."""

    def test_forbidden_import_detection(self):
        """Test that forbidden imports are detected."""
        code_with_forbidden_import = """
        import dit_attention
        from latent_space import something
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code_with_forbidden_import)
            temp_path = f.name

        try:
            is_valid, violations = check_file_integrity(temp_path)
            assert not is_valid, "Should detect forbidden imports"
            assert len(violations) > 0, "Should have violations"
        finally:
            os.unlink(temp_path)

    def test_allowed_imports_pass(self):
        """Test that allowed imports pass the check."""
        code_with_allowed_imports = """
        import os
        import json
        import logging
        import subprocess
        import tempfile
        import shutil
        import numpy as np
        import pandas as pd
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code_with_allowed_imports)
            temp_path = f.name

        try:
            is_valid, violations = check_file_integrity(temp_path)
            assert is_valid, f"Should pass with allowed imports, but got violations: {violations}"
            assert len(violations) == 0, "Should have no violations"
        finally:
            os.unlink(temp_path)

    def test_forbidden_name_usage_detection(self):
        """Test that usage of forbidden names in code is detected."""
        code_with_forbidden_usage = """
        def some_function():
            x = dit_attention.calculate()
            return latent_space.get_value()
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code_with_forbidden_usage)
            temp_path = f.name

        try:
            is_valid, violations = check_file_integrity(temp_path)
            assert not is_valid, "Should detect forbidden name usage"
            assert len(violations) > 0, "Should have violations"
        finally:
            os.unlink(temp_path)

    def test_evaluate_file_compliance(self):
        """Test that the actual evaluate.py file passes the check."""
        evaluate_file = project_root / "code" / "pipeline" / "evaluate.py"
        assert evaluate_file.exists(), "evaluate.py should exist"

        is_valid, violations = check_file_integrity(str(evaluate_file))
        assert is_valid, f"evaluate.py should not have forbidden imports. Violations: {violations}"
        assert len(violations) == 0, "evaluate.py should have no violations"
