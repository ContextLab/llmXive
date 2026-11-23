"""
Unit tests for the elastic data cleaning module.

Tests verify:
1. FCC crystal system filtering
2. Division-by-zero prevention (C11=C12 exclusion)
3. Correct A1 calculation
4. Missing columns handling
5. NaN value handling
6. Output file creation
"""

import os
import tempfile
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd
import numpy as np
import json

import sys
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.clean import clean_elastic_data

logger = logging.getLogger(__name__)


@pytest.fixture
def sample_fcc_data():
    """Create sample elastic data with FCC and non-FCC entries."""
    data = [
        {
            'material_id': 'MP-123',
            'C11': 200.0,
            'C12': 120.0,
            'C44': 80.0,
            'structure': json.dumps({
                'symmetry': {'crystal_system': 'cubic'}
            })
        },
        {
            'material_id': 'MP-456',
            'C11': 180.0,
            'C12': 100.0,
            'C44': 70.0,
            'structure': json.dumps({
                'symmetry': {'crystal_system': 'cubic'}
            })
        },
        {
            'material_id': 'MP-789',
            'C11': 150.0,
            'C12': 150.0,  # C11 = C12, should be excluded
            'C44': 60.0,
            'structure': json.dumps({
                'symmetry': {'crystal_system': 'cubic'}
            })
        },
        {
            'material_id': 'MP-101',
            'C11': 220.0,
            'C12': 130.0,
            'C44': 90.0,
            'structure': json.dumps({
                'symmetry': {'crystal_system': 'tetragonal'}  # Non-cubic, should be excluded
            })
        },
        {
            'material_id': 'MP-102',
            'C11': 190.0,
            'C12': 110.0,
            'C44': 75.0,
            'structure': json.dumps({
                'symmetry': {'crystal_system': 'cubic'}
            })
        }
    ]
    return pd.DataFrame(data)


@pytest.fixture
def temp_csv_file(sample_fcc_data):
    """Create a temporary CSV file with sample data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_fcc_data.to_csv(f, index=False)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    os.rmdir(temp_dir)


def test_clean_fcc_filter(temp_csv_file, temp_output_dir):
    """Test that non-cubic entries are filtered out."""
    output_path = os.path.join(temp_output_dir, 'cleaned.csv')

    df_cleaned = clean_elastic_data(temp_csv_file, output_path)

    # Should have 3 cubic entries (MP-123, MP-456, MP-102), excluding MP-789 (C11=C12)
    assert len(df_cleaned) == 3
    assert 'MP-101' not in df_cleaned['material_id'].values
    assert all(df_cleaned['A1'] > 0)


def test_clean_division_by_zero(temp_csv_file, temp_output_dir):
    """Test that entries with C11=C12 are excluded."""
    output_path = os.path.join(temp_output_dir, 'cleaned.csv')

    df_cleaned = clean_elastic_data(temp_csv_file, output_path)

    # MP-789 has C11=C12 and should be excluded
    assert 'MP-789' not in df_cleaned['material_id'].values
    # Verify no division by zero occurred (no NaN in A1)
    assert not df_cleaned['A1'].isna().any()


def test_clean_a1_calculation(temp_csv_file, temp_output_dir):
    """Test that A1 is calculated correctly."""
    output_path = os.path.join(temp_output_dir, 'cleaned.csv')

    df_cleaned = clean_elastic_data(temp_csv_file, output_path)

    # MP-123: A1 = 2*80 / (200-120) = 160/80 = 2.0
    mp123_row = df_cleaned[df_cleaned['material_id'] == 'MP-123']
    assert len(mp123_row) == 1
    expected_a1 = 2 * 80.0 / (200.0 - 120.0)
    assert abs(mp123_row['A1'].values[0] - expected_a1) < 1e-10

    # MP-456: A1 = 2*70 / (180-100) = 140/80 = 1.75
    mp456_row = df_cleaned[df_cleaned['material_id'] == 'MP-456']
    expected_a1 = 2 * 70.0 / (180.0 - 100.0)
    assert abs(mp456_row['A1'].values[0] - expected_a1) < 1e-10


def test_clean_missing_columns_raises(temp_output_dir):
    """Test that missing required columns raise an error."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        # Create CSV with missing columns
        data = pd.DataFrame({
            'material_id': ['MP-123'],
            'C11': [200.0]
            # Missing C12, C44, structure
        })
        data.to_csv(f, index=False)
        temp_path = f.name

    output_path = os.path.join(temp_output_dir, 'cleaned.csv')

    with pytest.raises(ValueError, match="Missing required columns"):
        clean_elastic_data(temp_path, output_path)

    os.unlink(temp_path)


def test_clean_handles_nan_values(temp_output_dir):
    """Test that NaN values in elastic constants are handled."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        data = pd.DataFrame([
            {
                'material_id': 'MP-123',
                'C11': 200.0,
                'C12': 120.0,
                'C44': 80.0,
                'structure': json.dumps({'symmetry': {'crystal_system': 'cubic'}})
            },
            {
                'material_id': 'MP-456',
                'C11': np.nan,  # NaN value
                'C12': 100.0,
                'C44': 70.0,
                'structure': json.dumps({'symmetry': {'crystal_system': 'cubic'}})
            }
        ])
        data.to_csv(f, index=False)
        temp_path = f.name

    output_path = os.path.join(temp_output_dir, 'cleaned.csv')

    df_cleaned = clean_elastic_data(temp_path, output_path)

    # MP-456 should be excluded due to NaN
    assert len(df_cleaned) == 1
    assert 'MP-123' in df_cleaned['material_id'].values
    assert 'MP-456' not in df_cleaned['material_id'].values

    os.unlink(temp_path)


def test_clean_output_file_created(temp_csv_file, temp_output_dir):
    """Test that the output file is actually created on disk."""
    output_path = os.path.join(temp_output_dir, 'cleaned.csv')

    df_cleaned = clean_elastic_data(temp_csv_file, output_path)

    # Verify file exists
    assert os.path.exists(output_path)

    # Verify file is not empty
    assert os.path.getsize(output_path) > 0

    # Verify we can read it back
    df_read = pd.read_csv(output_path)
    assert len(df_read) == len(df_cleaned)
    assert list(df_read.columns) == list(df_cleaned.columns)