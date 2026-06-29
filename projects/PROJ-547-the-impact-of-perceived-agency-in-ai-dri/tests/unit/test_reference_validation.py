"""
Unit test for the reference‑validation gating script.

The test uses ``unittest.mock`` to patch ``subprocess.run`` so that the
external CLI is not actually invoked. Two scenarios are covered:

1. Successful validation (returncode 0) – the script should complete without
   raising ``PipelineError``.
2. Failed validation (non‑zero returncode) – the script must raise
   ``PipelineError``.
"""

import builtins
from pathlib import Path
from unittest import mock

import pytest

from reference_validation.validate_citations import main, RESEARCH_MD_PATH
from utils.error_handler import PipelineError

@mock.patch("subprocess.run")
def test_validation_success(mock_run):
    # Simulate a successful CLI execution
    mock_run.return_value = mock.Mock(
        args=["reference-validator", str(RESEARCH_MD_PATH), "--threshold", "0.7"],
        returncode=0,
        stdout="All citations valid.",
        stderr="",
    )
    # Should not raise an exception
    main()

@mock.patch("subprocess.run")
def test_validation_failure(mock_run):
    # Simulate a failing CLI execution
    mock_run.return_value = mock.Mock(
        args=["reference-validator", str(RESEARCH_MD_PATH), "--threshold", "0.7"],
        returncode=1,
        stdout="",
        stderr="Citation XYZ failed validation.",
    )
    with pytest.raises(PipelineError):
        main()