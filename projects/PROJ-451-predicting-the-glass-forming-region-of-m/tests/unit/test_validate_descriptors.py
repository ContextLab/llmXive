"""
Unit tests for descriptor validation functionality (T017).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.validate_descriptors import (
    validate_descriptor_completeness,
    EXPECTED_DESCRIPTORS
)

class TestDescriptorValidation:
    """Test suite for descriptor validation logic."""

    def test_validate_completeness_all_present(self):
        """Test validation when all descriptors are present and complete."""
        # Create a test DataFrame with all descriptors
        df = pd.DataFrame({
            'composition': ['Fe20Ni80', 'Cu50Zr50', 'Ti50Cu50'],
            'phase': ['amorphous', 'crystalline', 'amorphous'],
        })
        
        # Add all expected descriptors with complete data
        for desc in EXPECTED_DESCRIPTORS:
            df[desc] = [1.0, 2.0, 3.0]
        
        cleaned_df, stats = validate_descriptor_completeness(df)
        
        # All rows should be kept (100% completeness)
        assert len(cleaned_df) == 3
        assert stats['overall']['avg_completeness_pct'] == 100.0
        assert stats['overall']['completeness_threshold_met'] is True
        assert stats['final']['rows_dropped'] == 0

    def test_validate_completeness_partial_missing(self):
        """Test validation when some descriptors have missing values."""
        df = pd.DataFrame({
            'composition': ['Fe20Ni80', 'Cu50Zr50', 'Ti50Cu50', 'Zr50Cu50'],
            'phase': ['amorphous', 'crystalline', 'amorphous', 'crystalline'],
        })
        
        # Add descriptors with some missing values
        for i, desc in enumerate(EXPECTED_DESCRIPTORS):
            if i == 0:
                # First descriptor: one missing value
                values = [1.0, 2.0, 3.0, None]
            elif i == 1:
                # Second descriptor: two missing values
                values = [1.0, None, 3.0, None]
            else:
                # Rest: complete
                values = [1.0, 2.0, 3.0, 4.0]
            df[desc] = values
        
        cleaned_df, stats = validate_descriptor_completeness(df)
        
        # Rows with <95% completeness should be dropped
        # Row 0: 9/10 = 90% -> dropped
        # Row 1: 8/10 = 80% -> dropped
        # Row 2: 10/10 = 100% -> kept
        # Row 3: 8/10 = 80% -> dropped
        assert len(cleaned_df) == 1
        assert stats['final']['rows_dropped'] == 3

    def test_validate_completeness_all_missing(self):
        """Test validation when all descriptors are missing."""
        df = pd.DataFrame({
            'composition': ['Fe20Ni80', 'Cu50Zr50'],
            'phase': ['amorphous', 'crystalline'],
        })
        
        # Add descriptors with all missing values
        for desc in EXPECTED_DESCRIPTORS:
            df[desc] = [None, None]
        
        cleaned_df, stats = validate_descriptor_completeness(df)
        
        # All rows should be dropped (0% completeness)
        assert len(cleaned_df) == 0
        assert stats['final']['rows_dropped'] == 2

    def test_validate_completeness_empty_dataframe(self):
        """Test validation with an empty DataFrame."""
        df = pd.DataFrame({
            'composition': [],
            'phase': [],
        })
        
        for desc in EXPECTED_DESCRIPTORS:
            df[desc] = []
        
        cleaned_df, stats = validate_descriptor_completeness(df)
        
        assert len(cleaned_df) == 0
        assert stats['overall']['total_rows'] == 0
        assert stats['final']['rows_dropped'] == 0

    def test_validate_completeness_threshold_boundary(self):
        """Test validation at the 95% threshold boundary."""
        df = pd.DataFrame({
            'composition': ['Fe20Ni80'] * 100,
            'phase': ['amorphous'] * 100,
        })
        
        # Create 10 descriptors
        num_descriptors = 10
        for i in range(num_descriptors):
            # Make 95% complete (9.5 out of 10, rounded to 9 or 10)
            # For 100 rows, we need each row to have >= 9.5 descriptors
            values = [1.0] * 95 + [None] * 5  # 95% complete
            df[f'desc_{i}'] = values
        
        cleaned_df, stats = validate_descriptor_completeness(df)
        
        # Rows with exactly 95% should be kept
        assert len(cleaned_df) == 95
        assert stats['final']['rows_dropped'] == 5

    def test_expected_descriptors_list(self):
        """Verify that EXPECTED_DESCRIPTORS contains all required descriptors."""
        required_descriptors = [
            'atomic_radius',
            'electronegativity',
            'valence_electron_concentration',
            'atomic_size_mismatch',
            'mixing_enthalpy',
            'atomic_size_difference',
            'valence_electron_size_mismatch',
            'electron_atom_ratio',
            'miedema_heat_of_formation',
            'atomic_packing_factor'
        ]
        
        assert set(EXPECTED_DESCRIPTORS) == set(required_descriptors)
        assert len(EXPECTED_DESCRIPTORS) == 10