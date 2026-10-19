"""
Unit tests for the SRA‑Toolkit helper functions.
They verify that the public API returns booleans and does not raise
unexpected exceptions.
"""

from install_sra_toolkit import (
    ensure_ncbi_settings,
    verify_sra_toolkit,
    install_sra_toolkit,
)

def test_ensure_ncbi_settings_returns_bool():
    assert isinstance(ensure_ncbi_settings(), bool)

def test_verify_sra_toolkit_returns_bool():
    assert isinstance(verify_sra_toolkit(), bool)

def test_install_sra_toolkit_returns_bool():
    assert isinstance(install_sra_toolkit(), bool)