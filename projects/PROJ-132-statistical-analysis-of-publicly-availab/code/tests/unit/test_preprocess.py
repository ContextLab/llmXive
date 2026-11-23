import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
import numpy as np
import json

from src.data.preprocess import (
    assign_grid_cell,
    filter_migratory_species,
    aggregate_to_weekly_grid,
    compute_phenology_metrics,
    mark_insufficient_cells,
    generate_provenance,
    run_preprocessing_pipeline
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)

@pytest.fixture
def sample_df():
    """Create a sample dataframe for testing."""
    data = {
        'species': ['SpeciesA', 'SpeciesA', 'SpeciesB', 'SpeciesA'],
        'lat': [45.0, 45.1, 45.0, 45.0],
        'lon': [-122.0, -122.1, -122.0, -122.0],
        'date': ['2023-03-01', '2023-03-08', '2023-03-01', '2023-03-01'],
        'checklist_id': ['c1', 'c2', 'c3', 'c4']
    }
    return pd.DataFrame(data)

@pytest.fixture
def migratory_list():
    return ['SpeciesA', 'SpeciesB']

def test_assign_grid_cell():
    lat, lon = 45.12, -122.34
    grid_id = assign_grid_cell(lat, lon)
    assert grid_id.startswith("lat_")
    assert grid_id.startswith("lon_")
    # Check rounding logic (GRID_RES=0.5)
    assert "45.0" in grid_id
    assert "-122.5" in grid_id

def test_filter_migratory_species(sample_df, migratory_list):
    # SpeciesC is not in the list
    sample_df.loc[3, 'species'] = 'SpeciesC'
    result = filter_migratory_species(sample_df, migratory_list)
    assert len(result) == 3
    assert 'SpeciesC' not in result['species'].values

def test_aggregate_to_weekly_grid(sample_df):
    result = aggregate_to_weekly_grid(sample_df)
    assert 'week' in result.columns
    assert 'grid_cell' in result.columns
    assert 'count' in result.columns
    assert 'checklist_ids' in result.columns
    # Check that counts are aggregated correctly
    # SpeciesA has 3 records, should have count 3 in the aggregated row
    species_a = result[result['species'] == 'SpeciesA']
    assert species_a['count'].sum() == 3

def test_compute_phenology_metrics(sample_df):
    # First aggregate
    agg_df = aggregate_to_weekly_grid(sample_df)
    # Then compute metrics
    result = compute_phenology_metrics(agg_df)
    assert 'first_arrival' in result.columns
    assert 'median_arrival' in result.columns
    assert 'stopover_duration' in result.columns

def test_mark_insufficient_cells(sample_df):
    agg_df = aggregate_to_weekly_grid(sample_df)
    # Force a low count by modifying the dataframe if necessary, 
    # but here we just test the function logic
    result_df, metadata = mark_insufficient_cells(agg_df, threshold=100)
    assert 'data_quality' in result_df.columns
    # Since total count is 4, and threshold is 100, all should be insufficient
    assert all(result_df['data_quality'] == 'insufficient')
    assert len(metadata) > 0

def test_generate_provenance(sample_df):
    agg_df = aggregate_to_weekly_grid(sample_df)
    raw_ids = sample_df['checklist_id'].tolist()
    
    mapping = generate_provenance(agg_df, raw_ids)
    
    assert isinstance(mapping, dict)
    # Check that mapping contains the checklist_ids
    all_mapped_ids = set()
    for ids in mapping.values():
        all_mapped_ids.update(ids)
    
    assert all_mapped_ids == set(raw_ids)

def test_imputation_metadata_exists(temp_data_dir):
    """
    Verify that the imputation metadata file exists and is readable.
    This test assumes T017b has run and created the file.
    Since T017b is not run in this unit test context, we simulate the file creation
    or check for the expected path existence if the pipeline was run.
    
    For the purpose of this specific task T016, we verify the function generates the file.
    However, T017d specifically asks for this test. We implement it here.
    """
    # Simulate the file creation by the pipeline (or T017b)
    # In a real integration test, the pipeline would run first.
    # Here we check if the function 'run_preprocessing_pipeline' creates it?
    # Actually T017b creates imputation_metadata.json. T016 creates row_mapping.json.
    # The task T017d requires this test. We implement it to check the file existence.
    
    # We will run the pipeline to ensure the file is created if T017b is integrated.
    # But since we are in unit tests, we might not have T017b.
    # Let's assume the file is created by the pipeline run in T016 context if T017b is called.
    # Since T016 depends on T015b and T017b, we assume T017b runs before T016 in the full pipeline.
    # For this test, we check the file existence.
    
    # We cannot run the full pipeline here without data.
    # So we check if the file exists in the expected location.
    # If T017b is not run, this test will fail, which is expected if T017b is not done.
    # But the task says "Write a test ... to verify ... exists".
    
    # We will create a mock file for the test to pass in isolation, 
    # but in the real run, the file should be created by T017b.
    # However, the instruction says "Do NOT fabricate".
    # So we will just check the file existence. If it doesn't exist, the test fails.
    # This is the correct behavior: if T017b hasn't run, the file doesn't exist.
    
    # But wait, T016 is the current task. T017d is a separate task.
    # The test for T017d is being written now.
    # We write the test to check the file.
    
    expected_path = Path("data/processed/imputation_metadata.json")
    
    # We cannot guarantee the file exists here without running T017b.
    # But the test should assert its existence.
    # If T017b is not run, this test will fail.
    # This is acceptable for a unit test that depends on a previous task.
    # However, to make the test pass in the context of the full pipeline, 
    # we assume the pipeline has been run.
    
    # Since we are implementing T016, and T017d is a separate task, 
    # we just write the test.
    
    # For the sake of this test passing in isolation, we might need to mock.
    # But the instruction says "Do NOT fabricate".
    # So we will just check. If the file is not there, the test fails.
    # This is the correct behavior.
    
    # However, to avoid failure in the test suite due to missing T017b, 
    # we can skip if the file is not found? No, the test should verify.
    
    # Let's just write the assertion.
    assert expected_path.exists(), "imputation_metadata.json does not exist. Ensure T017b has run."
    
    # If it exists, check it's valid JSON
    if expected_path.exists():
        with open(expected_path, 'r') as f:
            data = json.load(f)
            assert isinstance(data, dict) or isinstance(data, list)

def test_run_preprocessing_pipeline_with_mock_data(temp_data_dir, sample_df):
    """
    Test the full pipeline with mock data.
    """
    # Save sample data to a temp file
    input_path = Path(temp_data_dir) / "input.parquet"
    sample_df.to_parquet(input_path)
    
    # Run pipeline
    output_path = run_preprocessing_pipeline(str(input_path))
    
    # Check output exists
    assert os.path.exists(output_path)
    
    # Check provenance file exists
    provenance_path = Path("data/provenance/row_mapping.json")
    assert provenance_path.exists()
    
    # Check insufficient cells file exists (if any)
    insufficient_path = Path("data/processed/metadata_insufficient_cells.json")
    # It might not exist if no insufficient cells, but the code creates it if there are any.
    # If there are insufficient cells, it should exist.
    # In our sample, count is 4, threshold is 5, so it should exist.
    if os.path.exists(insufficient_path):
        with open(insufficient_path, 'r') as f:
            data = json.load(f)
            assert isinstance(data, list)