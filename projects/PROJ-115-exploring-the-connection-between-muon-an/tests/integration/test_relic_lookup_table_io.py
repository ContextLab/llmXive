"""
Integration tests for RelicLookupTable I/O operations.

These tests verify the end-to-end process of generating, saving, loading,
and validating a complete lookup table file.
"""

import pytest
import tempfile
import numpy as np
from pathlib import Path

from schemas.relic_lookup_table import (
    RelicLookupTable,
    RelicLookupTableEntry,
    validate_table
)


class TestLookupTableIntegration:
    """Integration tests for lookup table file operations."""

    def test_roundtrip_csv(self):
        """Test that a table can be saved and loaded back with identical data."""
        # Create a realistic set of entries
        n_points = 50
        entries = []
        for i in range(n_points):
            m_dm = 10.0 + i * 2.0
            m_v = 50.0 + i * 5.0
            g = 1e-3 * (1 + i * 0.1)
            omega = 0.12 * (1 - i * 0.001)  # Slight variation
            
            entries.append(RelicLookupTableEntry(
                m_dm=m_dm,
                m_v=m_v,
                g=g,
                omega_dm_h2=omega,
                method="Hulthen",
                is_valid=True,
                error_estimate=0.005
            ))

        original_table = RelicLookupTable(
            entries=entries,
            metadata={"source": "integration_test", "grid_size": n_points}
        )

        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Save
            original_table.save_to_csv(tmp_path)
            assert Path(tmp_path).exists()

            # Load
            loaded_table = RelicLookupTable.load_from_csv(tmp_path)

            # Verify structure
            assert len(loaded_table.entries) == n_points
            assert validate_table(loaded_table) is True

            # Verify data integrity
            for orig, loaded in zip(original_table.entries, loaded_table.entries):
                assert orig.m_dm == loaded.m_dm
                assert orig.m_v == loaded.m_v
                assert orig.g == loaded.g
                assert np.isclose(orig.omega_dm_h2, loaded.omega_dm_h2)
                assert orig.method == loaded.method
                assert orig.is_valid == loaded.is_valid

        finally:
            Path(tmp_path).unlink()

    def test_large_table_generation(self):
        """Test generating and saving a larger table (1000 points)."""
        n_points = 1000
        entries = []
        for i in range(n_points):
            m_dm = np.random.uniform(1.0, 100.0)
            m_v = np.random.uniform(10.0, 500.0)
            g = np.random.uniform(1e-4, 1e-2)
            omega = np.random.uniform(0.01, 0.5)
            
            entries.append(RelicLookupTableEntry(
                m_dm=m_dm,
                m_v=m_v,
                g=g,
                omega_dm_h2=omega,
                method="Hulthen",
                is_valid=True
            ))

        table = RelicLookupTable(entries=entries)
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            table.save_to_csv(tmp_path)
            loaded = RelicLookupTable.load_from_csv(tmp_path)
            assert len(loaded.entries) == n_points
            assert validate_table(loaded) is True
        finally:
            Path(tmp_path).unlink()

    def test_mixed_validity_table(self):
        """Test a table containing both valid and invalid entries."""
        entries = []
        # Valid entry
        entries.append(RelicLookupTableEntry(
            m_dm=10.0, m_v=100.0, g=1e-3, omega_dm_h2=0.12, is_valid=True
        ))
        # Invalid entry (negative mass)
        entries.append(RelicLookupTableEntry(
            m_dm=-10.0, m_v=100.0, g=1e-3, omega_dm_h2=0.12, is_valid=False
        ))
        # Valid entry
        entries.append(RelicLookupTableEntry(
            m_dm=20.0, m_v=200.0, g=2e-3, omega_dm_h2=0.11, is_valid=True
        ))

        table = RelicLookupTable(entries=entries)
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            table.save_to_csv(tmp_path)
            loaded = RelicLookupTable.load_from_csv(tmp_path)
            
            # The table itself loads fine, but validation should fail due to the invalid entry
            assert len(loaded.entries) == 3
            assert validate_table(loaded) is False
            # Specific entry validation
            assert loaded.entries[0].validate() is True
            assert loaded.entries[1].validate() is False
            assert loaded.entries[2].validate() is True
        finally:
            Path(tmp_path).unlink()