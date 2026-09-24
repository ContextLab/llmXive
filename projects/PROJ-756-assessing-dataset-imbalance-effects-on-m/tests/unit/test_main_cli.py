import pytest
import sys
import io
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, 'code')

def test_cli_parsing():
    """
    Test that CLI arguments are parsed correctly.
    Verifies --full-pipeline, --include-mp, --fallback-mode, --streaming flags.
    """
    from main import main
    import argparse

    # Test help output
    with patch('sys.argv', ['main.py', '--help']):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    # Test --full-pipeline flag
    with patch('sys.argv', ['main.py', '--full-pipeline']):
        with patch('main.run_pipeline') as mock_run:
            main()
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert args.full_pipeline is True
            assert args.include_mp is False
            assert args.fallback_mode is False
            assert args.streaming is False

    # Test --include-mp flag
    with patch('sys.argv', ['main.py', '--include-mp']):
        with patch('main.run_pipeline') as mock_run:
            main()
            args = mock_run.call_args[0][0]
            assert args.include_mp is True

    # Test --fallback-mode flag
    with patch('sys.argv', ['main.py', '--fallback-mode']):
        with patch('main.run_pipeline') as mock_run:
            main()
            args = mock_run.call_args[0][0]
            assert args.fallback_mode is True

    # Test --streaming flag
    with patch('sys.argv', ['main.py', '--streaming']):
        with patch('main.run_pipeline') as mock_run:
            main()
            args = mock_run.call_args[0][0]
            assert args.streaming is True

    # Test combined flags
    with patch('sys.argv', ['main.py', '--full-pipeline', '--include-mp', '--streaming']):
        with patch('main.run_pipeline') as mock_run:
            main()
            args = mock_run.call_args[0][0]
            assert args.full_pipeline is True
            assert args.include_mp is True
            assert args.streaming is True

def test_fallback_mode_override():
    """
    Test that --fallback-mode overrides --include-mp when both are set.
    """
    with patch('sys.argv', ['main.py', '--include-mp', '--fallback-mode']):
        with patch('main.run_pipeline') as mock_run:
            main()
            args = mock_run.call_args[0][0]
            assert args.fallback_mode is True
            assert args.include_mp is False

def test_no_flags():
    """
    Test behavior when no pipeline flags are provided.
    """
    with patch('sys.argv', ['main.py']):
        with patch('main.run_pipeline') as mock_run:
            main()
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert args.full_pipeline is False
            assert args.include_mp is False
            assert args.fallback_mode is False
            assert args.streaming is False
