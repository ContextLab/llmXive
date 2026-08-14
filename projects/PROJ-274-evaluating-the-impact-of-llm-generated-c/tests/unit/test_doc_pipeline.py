"""
Unit tests for the doc_pipeline CLI module.

These tests verify that the CLI argument parsing works correctly
and that the module can be imported without errors.
"""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from generation.doc_pipeline import main
from doc_generation import DataFetchError

def test_argparse_required_args():
    """Test that required arguments are enforced."""
    with patch('sys.argv', ['doc_pipeline.py']):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 2  # argparse exits with 2 on missing required args

def test_argparse_valid_args():
    """Test that valid arguments are parsed correctly."""
    with patch('sys.argv', [
        'doc_pipeline.py',
        '--repo', 'https://github.com/test/repo',
        '--commit', 'abc123',
        '--output', 'data/test.md'
    ]):
        # We expect it to fail later during execution (fetch), but argparse should pass
        with patch('generation.doc_pipeline.fetch_real_repo_data') as mock_fetch:
            mock_fetch.side_effect = DataFetchError("Mock fetch error")
            with pytest.raises(DataFetchError):
                main()

def test_module_import():
    """Test that the module can be imported."""
    from generation import doc_pipeline
    assert doc_pipeline is not None
    assert hasattr(doc_pipeline, 'main')
