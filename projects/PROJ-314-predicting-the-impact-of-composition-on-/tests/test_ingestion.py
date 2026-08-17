"""
Unit tests for data ingestion.
"""
import pytest
import pandas as pd
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ingestion import derive_primary_anion_cation_group, validate_data_gap

def test_derive_primary_anion_cation_group():
    result = derive_primary_anion_cation_group("Al2O3")
    assert "O" in result
    assert "Al" in result

def test_validate_data_gap():
    # This should not raise for N >= 30
    validate_data_gap(30)
    # This should raise for N < 30
    with pytest.raises(SystemExit):
        validate_data_gap(29)
