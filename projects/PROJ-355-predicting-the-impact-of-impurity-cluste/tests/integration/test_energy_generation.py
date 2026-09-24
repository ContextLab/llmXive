"""
Integration test for segregation energy generation verification.
"""
import pytest
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from config import get_project_root

def test_energy_generation_output(project_root):
    """
    Verify that simulate_energy produces non-empty results.
    """
    energies_path = project_root / "data" / "processed" / "segregation_energies.csv"

    if not energies_path.exists():
        pytest.skip("Energy file not found. Run T017c first.")

    df = pd.read_csv(energies_path)
    assert len(df) > 0, "Energy file exists but is empty"
    assert "segregation_energy" in df.columns, "Missing segregation_energy column"
    assert df["segregation_energy"].notna().any(), "All energy values are NaN"
