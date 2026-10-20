"""
Confirm that providing an invalid ``--step`` argument results in a graceful
exit without raising an exception.
"""

import pytest

def test_invalid_step_argument(monkeypatch):
    from code.cli.main import main
    import sys
    test_args = ["prog", "--step", "invalid_step"]
    monkeypatch.setattr(sys, "argv", test_args)

    # Should not raise; just log a warning and exit
    main()