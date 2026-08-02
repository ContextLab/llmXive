import os
import sys
import pytest
import pandas as pd
import pyarrow.parquet as pq
from pathlib import Path
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from data.consolidate import load_all_processed_datasets, write_consolidated_parquet
from data.preprocess import process_ebsd_dataset
from data.generate_synthetic import generate_synthetic_dataset

@pytest.fixture
def temp_data_dir():
    """Create a temporary data directory structure for testing."""
    temp_dir = tempfile.mkdtemp()
    data_dir = Path(temp_dir) / "data"
    interim_dir = data_dir / "interim"
    processed_dir = data_dir / "processed"
    
    interim_dir.mkdir(parents=True)
    processed_dir.mkdir(parents=True)
    
    # Create test materials
    for material in ["Al", "Cu"]:
        material_dir = interim_dir / material
        material_dir.mkdir()
        
        # Generate synthetic data for testing
        for reduction in [20, 40, 60]:
            df = generate_synthetic_dataset(material, reduction, n_points=100)
            output_file = material_dir / f"{material}_reduction_{reduction}_processed.parquet"
            df.to_parquet(output_file)
    
    yield data_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)

@pytest.fixture
def monkeypatch_config(monkeypatch, temp_data_dir):
    """Monkeypatch config functions to use temp directory."""
    def mock_get_data_path():
        return temp_data_dir / "data"
    
    def mock_get_reductions():
        return [20, 40, 60]
    
    def mock_get_seed():
        return 42
    
    monkeypatch.setattr("data.consolidate.get_data_path", mock_get_data_path)
    monkeypatch.setattr("data.consolidate.get_reductions", mock_get_reductions)
    monkeypatch.setattr("data.consolidate.get_seed", mock_get_seed)
    monkeypatch.setattr("config.get_data_path", mock_get_data_path)
    monkeypatch.setattr("config.get_reductions", mock_get_reductions)
    monkeypatch.setattr("config.get_seed", mock_get_seed)

def test_load_all_processed_datasets(monkeypatch_config, temp_data_dir):
    """Test loading all processed datasets."""
    df = load_all_processed_datasets()
    
    assert not df.empty, "DataFrame should not be empty"
    assert 'material' in df.columns, "DataFrame should have 'material' column"
    assert 'reduction' in df.columns, "DataFrame should have 'reduction' column"
    assert 'confidence' in df.columns, "DataFrame should have 'confidence' column"
    
    materials = sorted(df['material'].unique())
    assert materials == ['Al', 'Cu'], f"Expected materials ['Al', 'Cu'], got {materials}"
    
    reductions = sorted(df['reduction'].unique())
    assert reductions == [20, 40, 60], f"Expected reductions [20, 40, 60], got {reductions}"

def test_write_consolidated_parquet(monkeypatch_config, temp_data_dir):
    """Test writing consolidated Parquet file."""
    df = load_all_processed_datasets()
    output_path = temp_data_dir / "data" / "processed" / "cleaned_ebsd.parquet"
    
    written_path = write_consolidated_parquet(df, output_path)
    
    assert written_path.exists(), f"Output file should exist: {written_path}"
    
    # Verify we can read it back
    read_df = pd.read_parquet(written_path)
    assert len(read_df) == len(df), "Sample count should match"
    assert list(read_df.columns) == list(df.columns), "Columns should match"
    
    # Verify metadata
    table = pq.read_table(written_path)
    metadata = table.schema.metadata
    assert b'llmXive_metadata' in metadata, "Metadata should be present"

def test_consolidation_with_exclusion(monkeypatch_config, temp_data_dir):
    """Test that consolidation properly handles exclusion logic."""
    df = load_all_processed_datasets()
    
    # Verify exclusion was applied (check for reliability metrics if available)
    assert 'reliability_score' not in df.columns or df['reliability_score'].notna().all(), \
        "Reliability scores should be present if calculated"
    
    # Verify no samples with reliability_score < 0.5 (if the metric exists)
    if 'reliability_score' in df.columns:
        low_reliability = df[df['reliability_score'] < 0.5]
        assert len(low_reliability) == 0, "Low reliability samples should be excluded"

def test_consolidation_empty_result(monkeypatch_config, temp_data_dir):
    """Test handling of empty result."""
    # Modify config to request non-existent reductions
    import config
    original_get_reductions = config.get_reductions
    
    def mock_get_reductions():
        return [999]  # Non-existent reduction
    
    config.get_reductions = mock_get_reductions
    
    try:
        df = load_all_processed_datasets()
        assert df.empty, "DataFrame should be empty for non-existent reductions"
    finally:
        config.get_reductions = original_get_reductions

def test_metadata_preservation(monkeypatch_config, temp_data_dir):
    """Test that metadata is preserved in Parquet output."""
    df = load_all_processed_datasets()
    output_path = temp_data_dir / "data" / "processed" / "cleaned_ebsd.parquet"
    
    write_consolidated_parquet(df, output_path)
    
    table = pq.read_table(output_path)
    metadata = table.schema.metadata
    
    assert b'llmXive_metadata' in metadata
    import json
    meta_dict = json.loads(metadata[b'llmXive_metadata'].decode('utf-8'))
    
    assert 'total_samples' in meta_dict
    assert meta_dict['total_samples'] == len(df)
    assert 'materials' in meta_dict
    assert 'reductions' in meta_dict