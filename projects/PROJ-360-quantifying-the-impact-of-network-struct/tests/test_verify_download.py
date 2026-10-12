import tempfile
from pathlib import Path

import pytest

# Import the verification function from the script we just added.
from code.verify_download import verify

def _create_cif_files(target_dir: Path, n: int) -> None:
    """Create *n* empty ``.cif`` files in *target_dir*."""
    for i in range(n):
        (target_dir / f"file_{i}.cif").write_text("")

def test_verify_insufficient_cif_files():
    """The verifier should raise when fewer than 50 CIFs are present."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dir_path = Path(tmpdir)
        _create_cif_files(dir_path, 49)  # one short of the required minimum
        with pytest.raises(RuntimeError):
            verify(dir_path, min_required=50)

def test_verify_sufficient_cif_files():
    """The verifier should succeed when 50 or more CIFs are present."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dir_path = Path(tmpdir)
        _create_cif_files(dir_path, 50)
        # Should not raise; returns the count.
        count = verify(dir_path, min_required=50)
        assert count == 50