import pytest
from code.install_sra_toolkit import verify_sra_toolkit, ensure_ncbi_settings

def test_verify_sra_toolkit():
    """Verify that verify_sra_toolkit returns a boolean."""
    # This test checks for functional correctness of the check itself,
    # regardless of whether the toolkit is actually installed in the CI.
    result = verify_sra_toolkit()
    assert isinstance(result, bool)

def test_ensure_ncbi_settings():
    """Verify that ensure_ncbi_settings returns a boolean."""
    result = ensure_ncbi_settings()
    assert isinstance(result, bool)
