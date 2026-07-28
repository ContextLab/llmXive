"""
Unit tests to verify NO synthetic fallbacks exist in ingestion scripts.
"""
import ast
import os
import pytest
from pathlib import Path

class TestNoSyntheticFallback:
    """
    Ensures ingestion scripts do not contain synthetic data generators.
    """

    @pytest.fixture
    def ingestion_dir(self):
        return Path("code/src/ingest")

    def test_no_generate_synthetic_patterns(self, ingestion_dir):
        """
        Checks that no file in src/ingest contains 'generate_synthetic' or similar patterns.
        """
        forbidden_patterns = [
            "generate_synthetic",
            "mock_",
            "np.random",
            "fake_",
            "synthetic"
        ]

        for py_file in ingestion_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for pattern in forbidden_patterns:
                # Check for function calls or definitions
                if pattern in content:
                    # Allow comments explaining what is NOT done
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if pattern in line and not line.strip().startswith('#'):
                            # Check if it's in a string literal (unlikely to be a real call)
                            try:
                                tree = ast.parse(line)
                                # Simple heuristic: if it's a call, it's bad
                                if any(isinstance(node, ast.Call) for node in ast.walk(tree)):
                                    pytest.fail(f"Found forbidden pattern '{pattern}' in {py_file.name} at line {i+1}: {line.strip()}")
                            except SyntaxError:
                                # If it's not valid Python code (e.g. part of a larger string), skip
                                pass

    def test_no_random_data_generation_in_try_blocks(self, ingestion_dir):
        """
        Ensures try/except blocks do not fallback to random data generation.
        """
        for py_file in ingestion_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for patterns like:
            # try:
            #    ...
            # except:
            #    return generate_synthetic()
            #    return np.random...
            
            if "try:" in content:
                # This is a simplified check. A full AST analysis would be better.
                # We check if 'except' is followed by random generation logic.
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if line.strip().startswith("except") or line.strip().startswith("except:"):
                        # Check next few lines for forbidden patterns
                        for j in range(i+1, min(i+5, len(lines))):
                            next_line = lines[j].strip()
                            if next_line.startswith("#"):
                                continue
                            if any(p in next_line for p in ["generate_synthetic", "mock_", "np.random", "fake_"]):
                                pytest.fail(f"Found synthetic fallback in try/except in {py_file.name} near line {i+1}")