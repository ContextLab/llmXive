"""
Unit tests for the RelicLookupTable schema.

These tests verify the data structures, validation logic, and I/O capabilities
of the RelicLookupTable schema defined in code/schemas/relic_lookup_table.py.
"""

import pytest
import numpy as np
import pandas as pd
import tempfile
from pathlib import Path

from schemas.relic_lookup_table import (
    RelicLookupTableEntry,
    RelicLookupTable,
    validate_entry,
    validate_table
)


class TestRelicLookupTableEntry:
    """Tests for the RelicLookupTableEntry dataclass."""

    def test_entry_creation(self):
        """Test basic creation of an entry."""
        entry = RelicLookupTableEntry(
            m_dm=10.0,
            m_v=100.0,
            g=1e-3,
            omega_dm_h2=0.12,
            method="Hulthen"
        )
        assert entry.m_dm == 10.0
        assert entry.m_v == 100.0
        assert entry.g == 1e-3
        assert entry.omega_dm_h2 == 0.12
        assert entry.method == "Hulthen"
        assert entry.is_valid is True

    def test_entry_to_dict(self):
        """Test conversion to dictionary."""
        entry = RelicLookupTableEntry(
            m_dm=5.0,
            m_v=50.0,
            g=2e-3,
            omega_dm_h2=0.12,
            is_valid=True
        )
        d = entry.to_dict()
        assert d['m_dm'] == 5.0
        assert d['m_v'] == 50.0
        assert d['g'] == 2e-3
        assert d['omega_dm_h2'] == 0.12
        assert d['is_valid'] is True

    def test_entry_from_dict(self):
        """Test creation from dictionary."""
        data = {
            'm_dm': 15.0,
            'm_v': 150.0,
            'g': 5e-4,
            'omega_dm_h2': 0.11,
            'method': 'Numerov',
            'is_valid': True,
            'error_estimate': 0.01
        }
        entry = RelicLookupTableEntry.from_dict(data)
        assert entry.m_dm == 15.0
        assert entry.m_v == 150.0
        assert entry.g == 5e-4
        assert entry.omega_dm_h2 == 0.11
        assert entry.method == 'Numerov'
        assert entry.error_estimate == 0.01

    def test_validation_positive_mass(self):
        """Test validation with positive masses."""
        entry = RelicLookupTableEntry(
            m_dm=10.0,
            m_v=100.0,
            g=1e-3,
            omega_dm_h2=0.12
        )
        assert entry.validate() is True

    def test_validation_negative_mass(self):
        """Test validation fails with negative DM mass."""
        entry = RelicLookupTableEntry(
            m_dm=-10.0,
            m_v=100.0,
            g=1e-3,
            omega_dm_h2=0.12
        )
        assert entry.validate() is False

    def test_validation_zero_mass(self):
        """Test validation fails with zero mass."""
        entry = RelicLookupTableEntry(
            m_dm=0.0,
            m_v=100.0,
            g=1e-3,
            omega_dm_h2=0.12
        )
        assert entry.validate() is False

    def test_validation_negative_relic_density(self):
        """Test validation fails with negative relic density."""
        entry = RelicLookupTableEntry(
            m_dm=10.0,
            m_v=100.0,
            g=1e-3,
            omega_dm_h2=-0.12
        )
        assert entry.validate() is False

    def test_validation_invalid_flag(self):
        """Test validation fails if is_valid is False."""
        entry = RelicLookupTableEntry(
            m_dm=10.0,
            m_v=100.0,
            g=1e-3,
            omega_dm_h2=0.12,
            is_valid=False
        )
        assert entry.validate() is False


class TestRelicLookupTable:
    """Tests for the RelicLookupTable class."""

    def test_table_creation(self):
        """Test basic table creation."""
        table = RelicLookupTable(entries=[])
        assert len(table.entries) == 0
        assert table.metadata["version"] == "1.0"
        assert table.metadata["entry_count"] == 0

    def test_add_entry(self):
        """Test adding an entry to the table."""
        table = RelicLookupTable(entries=[])
        entry = RelicLookupTableEntry(
            m_dm=10.0,
            m_v=100.0,
            g=1e-3,
            omega_dm_h2=0.12
        )
        table.add_entry(entry)
        assert len(table.entries) == 1
        assert table.metadata["entry_count"] == 1

    def test_to_dataframe(self):
        """Test conversion to DataFrame."""
        entries = [
            RelicLookupTableEntry(m_dm=10.0, m_v=100.0, g=1e-3, omega_dm_h2=0.12),
            RelicLookupTableEntry(m_dm=20.0, m_v=200.0, g=2e-3, omega_dm_h2=0.11)
        ]
        table = RelicLookupTable(entries=entries)
        df = table.to_dataframe()
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert 'm_dm' in df.columns
        assert 'm_v' in df.columns
        assert 'g' in df.columns
        assert 'omega_dm_h2' in df.columns
        assert df.iloc[0]['m_dm'] == 10.0
        assert df.iloc[1]['m_dm'] == 20.0

    def test_from_dataframe(self):
        """Test creation from DataFrame."""
        data = {
            'm_dm': [10.0, 20.0],
            'm_v': [100.0, 200.0],
            'g': [1e-3, 2e-3],
            'omega_dm_h2': [0.12, 0.11],
            'is_valid': [True, True]
        }
        df = pd.DataFrame(data)
        table = RelicLookupTable.from_dataframe(df)
        
        assert len(table.entries) == 2
        assert table.entries[0].m_dm == 10.0
        assert table.entries[1].m_dm == 20.0

    def test_save_and_load_csv(self):
        """Test saving to and loading from CSV."""
        entries = [
            RelicLookupTableEntry(m_dm=10.0, m_v=100.0, g=1e-3, omega_dm_h2=0.12),
            RelicLookupTableEntry(m_dm=50.0, m_v=500.0, g=5e-3, omega_dm_h2=0.10)
        ]
        table = RelicLookupTable(entries=entries, metadata={"test": "value"})
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            table.save_to_csv(tmp_path)
            loaded_table = RelicLookupTable.load_from_csv(tmp_path)
            
            assert len(loaded_table.entries) == 2
            assert loaded_table.entries[0].m_dm == 10.0
            assert loaded_table.entries[1].m_v == 500.0
            assert loaded_table.metadata.get('source_file') is not None
        finally:
            Path(tmp_path).unlink()

    def test_validate_all(self):
        """Test validation of all entries."""
        valid_entries = [
            RelicLookupTableEntry(m_dm=10.0, m_v=100.0, g=1e-3, omega_dm_h2=0.12),
            RelicLookupTableEntry(m_dm=20.0, m_v=200.0, g=2e-3, omega_dm_h2=0.11)
        ]
        table = RelicLookupTable(entries=valid_entries)
        assert table.validate_all() is True

        invalid_entries = [
            RelicLookupTableEntry(m_dm=10.0, m_v=100.0, g=1e-3, omega_dm_h2=0.12),
            RelicLookupTableEntry(m_dm=-10.0, m_v=200.0, g=2e-3, omega_dm_h2=0.11)
        ]
        table_invalid = RelicLookupTable(entries=invalid_entries)
        assert table_invalid.validate_all() is False


class TestStandaloneValidators:
    """Tests for standalone validation functions."""

    def test_validate_entry_function(self):
        """Test the validate_entry standalone function."""
        entry = RelicLookupTableEntry(m_dm=10.0, m_v=100.0, g=1e-3, omega_dm_h2=0.12)
        assert validate_entry(entry) is True

        bad_entry = RelicLookupTableEntry(m_dm=-10.0, m_v=100.0, g=1e-3, omega_dm_h2=0.12)
        assert validate_entry(bad_entry) is False

    def test_validate_table_function(self):
        """Test the validate_table standalone function."""
        entries = [
            RelicLookupTableEntry(m_dm=10.0, m_v=100.0, g=1e-3, omega_dm_h2=0.12)
        ]
        table = RelicLookupTable(entries=entries)
        assert validate_table(table) is True

        bad_entries = [
            RelicLookupTableEntry(m_dm=-10.0, m_v=100.0, g=1e-3, omega_dm_h2=0.12)
        ]
        bad_table = RelicLookupTable(entries=bad_entries)
        assert validate_table(bad_table) is False
