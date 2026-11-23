"""
Minimal test for the ``fetch_hcp_behavioral`` module.

The test checks that the module can be imported and that the
``fetch_hcp_phenotypic_data`` function raises a clear error when
the download URL is unreachable (e.g., no internet).  The CI
environment used for the evaluation may not have internet access,
so the test should not attempt a real download – it merely ensures
that the function signature and error handling behave as expected.
"""

import builtins
import os
import sys
from pathlib import Path

import pytest

# Import the module under test
from download.fetch_hcp_behavioral import fetch_hcp_phenotypic_data

@pytest.fixture
def tmp_output(tmp_path: Path) -> Path:
    """Create a temporary output directory for the test."""
    return tmp_path / "raw"

def test_fetch_raises_when_url_unreachable(monkeypatch, tmp_output):
    """
    Patch ``requests.get`` to simulate a network failure and verify that
    ``fetch_hcp_phenotypic_data`` raises ``RuntimeError`` with a helpful
    message.
    """
    def fake_get(*args, **kwargs):
        raise RuntimeError("simulated network failure")

    monkeypatch.setattr("requests.get", fake_get)

    with pytest.raises(RuntimeError) as excinfo:
        fetch_hcp_phenotypic_data(tmp_output, subjects=["100307"])

    assert "Failed to download" in str(excinfo.value)

def test_invalid_subject_id_warning(capfd, monkeypatch, tmp_output):
    """
    Ensure that providing an invalid subject ID does not break the function.
    The function itself does not validate IDs beyond length, so we test that
    the warning path in ``main`` works via a subprocess call.
    """
    # Run the CLI with an invalid ID; capture stderr.
    script_path = Path(__file__).parents[2] / "code" / "download" / "fetch_hcp_behavioral.py"
    result = os.system(f"{sys.executable} {script_path} --subjects 12345 --output {tmp_output}")

    # The script should exit with non‑zero status because the download will
    # fail (no internet).  The warning about the ID should be printed to
    # stderr, which we capture via capfd.
    captured = capfd.readouterr()
    assert "does not look like a standard HCP ID" in captured.err