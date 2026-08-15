"""
Integration tests for ast_parser.py focusing on T016 (skip logic) and T012 (real extraction).
"""
import pytest
import tempfile
from pathlib import Path
import os

from feature_extractor.ast_parser import extract_features_from_directory
from utils.logging import get_logger


@pytest.fixture
def sample_repo(tmp_path):
    """Create a temporary directory structure with valid and invalid Python files."""
    repo_dir = tmp_path / "sample_repo"
    repo_dir.mkdir()
    
    # Valid file
    (repo_dir / "module1.py").write_text("""
    def add(a, b):
        return a + b
    
    class Calculator:
        def multiply(self, x, y):
            return x * y
    """)
    
    # Valid file in subdirectory
    sub_dir = repo_dir / "utils"
    sub_dir.mkdir()
    (sub_dir / "helper.py").write_text("""
    def helper():
        if True:
            return 1
    """)
    
    # Invalid file (syntax error)
    (repo_dir / "broken.py").write_text("def broken(:")
    
    # Valid file with complex inheritance
    (repo_dir / "complex.py").write_text("""
    class A: pass
    class B(A): pass
    class C(B): pass
    """)
    
    return repo_dir


def test_mixed_repo_processing(sample_repo):
    """
    Test that the parser processes a directory with mixed valid/invalid files.
    Verifies T016: Invalid files are skipped, valid files are processed.
    """
    features = extract_features_from_directory(sample_repo)
    
    # We expect 3 valid files: module1.py, helper.py, complex.py
    # broken.py should be skipped
    assert len(features) == 3
    
    file_names = [f['file'] for f in features]
    assert not any("broken.py" in name for name in file_names)
    
    # Verify specific metrics
    complex_features = next(f for f in features if "complex.py" in f['file'])
    assert complex_features['inheritance_depth'] == 2
    
    helper_features = next(f for f in features if "helper.py" in f['file'])
    assert helper_features['cyclomatic_complexity'] == 2  # Base 1 + 1 (if)


def test_empty_directory():
    """Test processing an empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        features = extract_features_from_directory(Path(tmpdir))
        assert features == []


def test_nonexistent_directory():
    """Test processing a non-existent directory."""
    features = extract_features_from_directory(Path("/nonexistent/path"))
    assert features == []
