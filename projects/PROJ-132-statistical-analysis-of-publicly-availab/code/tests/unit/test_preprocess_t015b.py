"""
Tests for T015b: Preprocessing pipeline implementation.
Verifies filtering, aggregation, and output generation.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil
from datetime import datetime, timedelta
import json

from src.data.preprocess import (
    filter_migratory_species,
    filter_date_range,
    assign_grid_cell,
    aggregate_to_weekly_grid,
    compute_phenology_metrics,
    mark_insufficient_cells,
    run_preprocessing_pipeline
)
from src.config import GRID_RES

@pytest.fixture
def sample_ebird_data():
    """Create sample eBird data for testing."""
    data = {
        'species_name': ['Turdus migratorius', 'Turdus migratorius', 'Cardinalis cardinalis', 'Turdus migratorius'],
        'latitude': [40.0, 40.5, 41.0, 39.5],
        'longitude': [-75.0, -75.5, -76.0, -74.5],
        'date': [
            datetime(2021, 3, 15),
            datetime(2021, 3, 22),
            datetime(2021, 4, 1),
            datetime(2022, 3, 10)
        ],
        'count': [5, 3, 8, 2],
        'checklist_id': ['chk001', 'chk002', 'chk003', 'chk004'],
        'temp': [10.0, 12.0, 15.0, 8.0],
        'precip': [0.0, 5.0, 2.0, 0.0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def clo_migratory_list(tmp_path):
    """Create a temporary CLO migratory list file."""
    clo_df = pd.DataFrame({
        'scientific_name': ['Turdus migratorius', 'Cardinalis cardinalis', 'Quercus alba'],
        'common_name': ['American Robin', 'Northern Cardinal', 'White Oak']
    })
    clo_path = tmp_path / 'clo_migratory_list.csv'
    clo_df.to_csv(clo_path, index=False)
    return clo_path

@pytest.fixture
def temp_data_dir():
    """Create temporary directories for test data."""
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp)

def test_filter_migratory_species(sample_ebird_data, clo_migratory_list):
    """Test filtering to migratory species."""
    filtered = filter_migratory_species(sample_ebird_data, clo_migratory_list)
    
    # All species in sample are migratory, so all should be retained
    assert len(filtered) == len(sample_ebird_data)
    assert 'species_name' in filtered.columns

def test_filter_date_range(sample_ebird_data):
    """Test filtering to 2020-2024 date range."""
    filtered = filter_date_range(sample_ebird_data, 2020, 2024)
    
    # All dates in sample are within range
    assert len(filtered) == len(sample_ebird_data)
    assert filtered['date'].dt.year.min() >= 2020
    assert filtered['date'].dt.year.max() <= 2024

def test_assign_grid_cell():
    """Test grid cell assignment with GRID_RES=0.5."""
    row = pd.Series({'latitude': 40.2, 'longitude': -75.3})
    cell_id = assign_grid_cell(row)
    
    # Expected: floor(40.2/0.5)*0.5 = 40.0, floor(-75.3/0.5)*0.5 = -75.5
    assert cell_id == '40.0_-75.5'

def test_aggregate_to_weekly_grid(sample_ebird_data, clo_migratory_list):
    """Test aggregation to weekly grid counts."""
    filtered = filter_migratory_species(sample_ebird_data, clo_migratory_list)
    filtered = filter_date_range(filtered)
    aggregated = aggregate_to_weekly_grid(filtered)
    
    assert 'grid_cell' in aggregated.columns
    assert 'week' in aggregated.columns
    assert 'count' in aggregated.columns
    assert len(aggregated) > 0

def test_compute_phenology_metrics(sample_ebird_data, clo_migratory_list):
    """Test phenology metric computation."""
    filtered = filter_migratory_species(sample_ebird_data, clo_migratory_list)
    filtered = filter_date_range(filtered)
    aggregated = aggregate_to_weekly_grid(filtered)
    
    # Compute metrics on the filtered data
    metrics = compute_phenology_metrics(filtered)
    
    assert 'first_arrival' in metrics.columns
    assert 'median_arrival' in metrics.columns
    assert 'stopover_duration' in metrics.columns

def test_mark_insufficient_cells(sample_ebird_data, clo_migratory_list):
    """Test marking of insufficient data cells."""
    filtered = filter_migratory_species(sample_ebird_data, clo_migratory_list)
    filtered = filter_date_range(filtered)
    aggregated = aggregate_to_weekly_grid(filtered)
    
    df_marked, metadata = mark_insufficient_cells(aggregated, min_count=5)
    
    assert 'data_quality' in df_marked.columns
    assert 'insufficient' in df_marked['data_quality'].values or 'sufficient' in df_marked['data_quality'].values
    assert isinstance(metadata, pd.DataFrame)

def test_run_preprocessing_pipeline(temp_data_dir, clo_migratory_list):
    """Test full preprocessing pipeline execution."""
    # Create sample eBird data file
    sample_df = pd.DataFrame({
        'species_name': ['Turdus migratorius'] * 10,
        'latitude': [40.0 + i * 0.1 for i in range(10)],
        'longitude': [-75.0 + i * 0.1 for i in range(10)],
        'date': [datetime(2021, 3, 15 + i) for i in range(10)],
        'count': [5] * 10,
        'checklist_id': [f'chk{i:03d}' for i in range(10)],
        'temp': [10.0] * 10,
        'precip': [0.0] * 10
    })
    
    ebird_path = temp_data_dir / 'ebird_sample.parquet'
    sample_df.to_parquet(ebird_path)
    
    output_dir = temp_data_dir / 'processed'
    provenance_dir = temp_data_dir / 'provenance'
    
    # Run pipeline
    results = run_preprocessing_pipeline(
        ebird_data_path=ebird_path,
        clo_list_path=clo_migratory_list,
        output_dir=output_dir,
        provenance_dir=provenance_dir
    )
    
    # Verify outputs
    assert output_dir.exists()
    assert provenance_dir.exists()
    assert (output_dir / 'aggregated_ebird.parquet').exists()
    assert (output_dir / 'metadata_insufficient_cells.json').exists()
    assert (provenance_dir / 'row_mapping.json').exists()
    
    # Verify results structure
    assert 'total_records' in results
    assert 'species_count' in results
    assert 'grid_cells' in results
    
    # Verify provenance file content
    with open(provenance_dir / 'row_mapping.json', 'r') as f:
        provenance = json.load(f)
        assert 'generated_at' in provenance
        assert 'total_records_processed' in provenance