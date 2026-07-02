"""
Unit tests for the RelicLookupTable schema and generation logic.
"""
import pytest
import math
import os
import tempfile
from pathlib import Path

from schemas.relic_lookup_table import (
    RelicLookupTable,
    RelicLookupTableEntry,
    validate_entry,
    validate_table
)

def test_entry_creation():
    """Test basic creation of a lookup table entry."""
    entry = RelicLookupTableEntry(
        m_dm_MeV=100.0,
        m_V_MeV=200.0,
        g=0.01,
        omega_dm_h2=0.12,
        is_resonant=True,
        approximation_error_pct=5.0
    )
    assert entry.m_dm_MeV == 100.0
    assert entry.is_resonant is True
    assert entry.to_dict()['omega_dm_h2'] == 0.12

def test_entry_validation_valid():
    """Test validation of a physically valid entry."""
    entry = RelicLookupTableEntry(
        m_dm_MeV=100.0,
        m_V_MeV=200.0,
        g=0.01,
        omega_dm_h2=0.12,
        approximation_error_pct=5.0
    )
    assert validate_entry(entry) is True

def test_entry_validation_invalid_mass():
    """Test validation fails for negative mass."""
    entry = RelicLookupTableEntry(
        m_dm_MeV=-10.0,
        m_V_MeV=200.0,
        g=0.01,
        omega_dm_h2=0.12
    )
    assert validate_entry(entry) is False

def test_entry_validation_invalid_omega():
    """Test validation fails for negative omega."""
    entry = RelicLookupTableEntry(
        m_dm_MeV=100.0,
        m_V_MeV=200.0,
        g=0.01,
        omega_dm_h2=-0.12
    )
    assert validate_entry(entry) is False

def test_table_roundtrip_csv():
    """Test saving and loading a table from CSV."""
    entries = [
        RelicLookupTableEntry(10.0, 20.0, 0.01, 0.12, False, 2.0),
        RelicLookupTableEntry(50.0, 100.0, 0.005, 0.11, True, 3.0)
    ]
    table = RelicLookupTable(entries=entries, metadata={"test": True})

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        table.save_csv(tmp_path)
        loaded_table = RelicLookupTable.load_csv(tmp_path)

        assert len(loaded_table.entries) == len(entries)
        assert loaded_table.entries[0].m_dm_MeV == entries[0].m_dm_MeV
        assert loaded_table.entries[1].is_resonant == entries[1].is_resonant
        assert loaded_table.metadata['row_count'] == len(entries)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def test_table_validation():
    """Test full table validation."""
    valid_entries = [
        RelicLookupTableEntry(10.0, 20.0, 0.01, 0.12),
        RelicLookupTableEntry(50.0, 100.0, 0.005, 0.11)
    ]
    table = RelicLookupTable(entries=valid_entries, metadata={})
    assert validate_table(table) is True

    invalid_entries = [
        RelicLookupTableEntry(10.0, 20.0, 0.01, 0.12),
        RelicLookupTableEntry(-50.0, 100.0, 0.005, 0.11) # Invalid mass
    ]
    invalid_table = RelicLookupTable(entries=invalid_entries, metadata={})
    assert validate_table(invalid_table) is False