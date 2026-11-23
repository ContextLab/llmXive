"""
Unit tests for code/feature_extractor/ast_parser.py
"""
import pytest
import tempfile
import os
from pathlib import Path

from feature_extractor.ast_parser import (
    calculate_cyclomatic_complexity,
    calculate_inheritance_depth,
    extract_token_histogram,
    extract_ast_features,
    extract_features_from_directory,
    get_feature_vector_size,
    CyclomaticComplexityVisitor,
    InheritanceDepthVisitor
)
import ast


class TestCyclomaticComplexity:
    def test_simple_function(self):
        code = "def foo(): pass"
        tree = ast.parse(code)
        # Base complexity is 1
        assert calculate_cyclomatic_complexity(tree) == 1

    def test_if_statement(self):
        code = "def foo():\n    if True:\n        pass"
        tree = ast.parse(code)
        # Base 1 + 1 (if) = 2
        assert calculate_cyclomatic_complexity(tree) == 2

    def test_loop_and_if(self):
        code = """
        def foo():
            for i in range(10):
                if i > 5:
                    break
        """
        tree = ast.parse(code)
        # Base 1 + 1 (for) + 1 (if) = 3
        assert calculate_cyclomatic_complexity(tree) == 3


class TestInheritanceDepth:
    def test_no_inheritance(self):
        code = """
        class A:
            pass
        """
        tree = ast.parse(code)
        assert calculate_inheritance_depth(tree) == 0

    def test_single_inheritance(self):
        code = """
        class A:
            pass
        class B(A):
            pass
        """
        tree = ast.parse(code)
        # A is 0, B inherits A (0) + 1 = 1
        assert calculate_inheritance_depth(tree) == 1

    def test_deep_inheritance(self):
        code = """
        class A: pass
        class B(A): pass
        class C(B): pass
        """
        tree = ast.parse(code)
        # A=0, B=1, C=2
        assert calculate_inheritance_depth(tree) == 2


class TestTokenHistogram:
    def test_basic_tokens(self):
        code = "def foo(): pass"
        hist = extract_token_histogram(code)
        # Should contain NAME, COLON, etc.
        assert isinstance(hist, dict)
        assert len(hist) > 0
        # 'NAME' should be present
        assert any('NAME' in k for k in hist.keys())


class TestExtractASTFeatures:
    def test_parse_valid_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def valid():\n    if True:\n        pass")
            f.flush()
            path = Path(f.name)

        try:
            features = extract_ast_features(path)
            assert features is not None
            assert features['cyclomatic_complexity'] == 2
            assert features['file'] == str(path)
        finally:
            os.unlink(path)

    def test_parse_invalid_syntax(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def invalid(:\n    pass") # Syntax error
            f.flush()
            path = Path(f.name)

        try:
            features = extract_ast_features(path)
            # Should return None for malformed files (T016)
            assert features is None
        finally:
            os.unlink(path)

    def test_extract_features_from_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a valid file
            valid_path = Path(tmpdir) / "valid.py"
            valid_path.write_text("def ok(): pass")

            # Create an invalid file
            invalid_path = Path(tmpdir) / "bad.py"
            invalid_path.write_text("def bad(:")

            features = extract_features_from_directory(Path(tmpdir))

            # Should contain only the valid file
            assert len(features) == 1
            assert features[0]['file'] == str(valid_path)


class TestFeatureVectorSize:
    def test_get_feature_vector_size(self):
        size = get_feature_vector_size()
        # 1 (CC) + 1 (Inheritance) + 10 (Token Hist) = 12
        assert size == 12
