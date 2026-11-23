"""
Integration tests for the data pipeline.
"""
import pandas as pd
import numpy as np
import pytest
from code.utils.spatial_blocks import create_spatial_blocks
from code.utils.data_utils import validate_coordinates, check_data_quality

def test_full_pipeline_integration():
    """Test a simplified full pipeline flow."""
    # 1. Create data
    data = {
        'decimalLongitude': np.random.uniform(-120, -60, 100),
        'decimalLatitude': np.random.uniform(25, 50, 100),
        'species': ['A'] * 100
    }
    df = pd.DataFrame(data)

    # 2. Validate
    df_valid = validate_coordinates(df)
    assert len(df_valid) > 0

    # 3. Spatial blocks
    df_blocks = create_spatial_blocks(df_valid)
    assert 'spatial_block' in df_blocks.columns

    # 4. Quality check
    quality = check_data_quality(df_blocks, required_cols=['species'])
    assert quality['total_records'] == len(df_valid)
