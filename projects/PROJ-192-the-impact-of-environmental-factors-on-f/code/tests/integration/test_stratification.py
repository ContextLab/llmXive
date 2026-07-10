"""
Integration test for User Story 2 Stratification (T025).

Verifies that the stratification logic correctly splits data by biome
and handles edge cases like missing values or empty strata.
"""
import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Import the function to test
from src.pipelines.analysis import stratify_by_biome, run_stratification_pipeline

@pytest.fixture
def sample_data():
    """Create synthetic ASV and Metadata data for testing."""
    # ASV Table: 15 samples, 5 features
    asv_data = {
        'ASV_1': [10, 5, 0, 2, 0, 15, 3, 0, 1, 0, 20, 5, 0, 2, 1],
        'ASV_2': [0, 1, 5, 0, 2, 0, 4, 5, 0, 1, 0, 1, 6, 0, 2],
        'ASV_3': [2, 0, 1, 3, 5, 1, 0, 2, 4, 5, 2, 0, 1, 3, 4],
        'ASV_4': [5, 4, 3, 2, 1, 6, 5, 4, 3, 2, 5, 4, 3, 2, 1],
        'ASV_5': [1, 2, 3, 4, 5, 2, 3, 4, 5, 6, 1, 2, 3, 4, 5]
    }
    # Indices correspond to samples
    asv_df = pd.DataFrame(asv_data, index=[f"sample_{i}" for i in range(1, 16)])
    
    # Metadata: Includes 'biome' column
    meta_data = {
        'pH': [6.5, 7.0, 5.5, 6.0, 7.2, 6.8, 5.0, 6.2, 7.5, 6.9, 6.4, 5.8, 6.1, 7.1, 5.9],
        'nutrients': [100, 120, 80, 90, 110, 105, 75, 85, 115, 108, 95, 70, 88, 112, 78],
        'biome': [
            'Forest', 'Forest', 'Forest', 'Forest', 'Forest', # 5 Forest
            'Grassland', 'Grassland', 'Grassland', 'Grassland', 'Grassland', # 5 Grassland
            'Wetland', 'Wetland', 'Wetland', 'Wetland', 'Wetland' # 5 Wetland
        ]
    }
    meta_df = pd.DataFrame(meta_data, index=asv_df.index)
    
    return asv_df, meta_df

def test_stratify_by_biome_basic(sample_data):
    """Test basic stratification logic."""
    asv_df, meta_df = sample_data
    
    strata = stratify_by_biome(asv_df, meta_df, biome_column="biome")
    
    assert len(strata) == 3, "Should have 3 unique biomes"
    assert 'Forest' in strata
    assert 'Grassland' in strata
    assert 'Wetland' in strata
    
    # Check sample counts
    assert len(strata['Forest'][0]) == 5
    assert len(strata['Grassland'][0]) == 5
    assert len(strata['Wetland'][0]) == 5
    
    # Check that feature counts match original
    for biome, (a, m) in strata.items():
        assert a.shape[1] == 5, f"Features should match for {biome}"
        assert m.shape[1] == 3, f"Metadata columns should match for {biome}"

def test_stratify_by_biome_missing_values(sample_data):
    """Test handling of missing biome values."""
    asv_df, meta_df = sample_data
    
    # Introduce NaN in biome column
    meta_df.loc['sample_1', 'biome'] = None
    
    strata = stratify_by_biome(asv_df, meta_df, biome_column="biome")
    
    # Forest should now have 4 samples
    assert len(strata['Forest'][0]) == 4
    # Total samples should be 14
    total_samples = sum(len(a) for a, _ in strata.values())
    assert total_samples == 14

def test_stratify_by_biome_missing_column(sample_data):
    """Test error handling when biome column is missing."""
    asv_df, meta_df = sample_data
    
    with pytest.raises(ValueError, match="Biome column"):
        stratify_by_biome(asv_df, meta_df, biome_column="non_existent_column")

def test_run_stratification_pipeline(sample_data, tmp_path):
    """Test the full pipeline including file I/O."""
    asv_df, meta_df = sample_data
    
    # Create temporary input files
    asv_path = tmp_path / "asv_table.tsv"
    meta_path = tmp_path / "harmonized_matrix.csv"
    output_dir = tmp_path / "strata"
    
    asv_df.to_csv(asv_path, sep='\t')
    meta_df.to_csv(meta_path)
    
    # Run pipeline
    results = run_stratification_pipeline(
        input_asv_path=str(asv_path),
        input_metadata_path=str(meta_path),
        output_dir=str(output_dir),
        biome_column="biome"
    )
    
    # Verify in-memory results
    assert len(results) == 3
    
    # Verify files were created
    assert output_dir.exists()
    files = list(output_dir.glob("*"))
    assert len(files) == 6 # 3 asv + 3 meta
    
    # Verify content of one file
    forest_asv_file = output_dir / "asv_Forest.tsv"
    assert forest_asv_file.exists()
    loaded_asv = pd.read_csv(forest_asv_file, sep='\t', index_col=0)
    assert len(loaded_asv) == 5
    assert 'Forest' in str(loaded_asv.index)