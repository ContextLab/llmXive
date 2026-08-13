"""
Unit tests for preprocessing pipeline.
"""
import pytest
import polars as pl
from pathlib import Path
import tempfile
import os

from src.data.preprocess import (
    assign_grid_cell,
    filter_migratory_species,
    compute_phenology_metrics,
    mark_insufficient_cells,
    generate_provenance,
)

def test_assign_grid_cell():
    assert assign_grid_cell(40.5, -74.0, 0.5) == "lat_81_lon_-148"
    assert assign_grid_cell(0.0, 0.0, 0.5) == "lat_0_lon_0"

def test_filter_migratory_species():
    df = pl.DataFrame({
        "species": ["SpeciesA", "SpeciesB", "SpeciesC"],
        "count": [1, 2, 3],
    })
    species_set = {"SpeciesA", "SpeciesC"}
    result = filter_migratory_species(df, species_set)
    assert result.height == 2
    assert result["species"].to_list() == ["SpeciesA", "SpeciesC"]

def test_compute_phenology_metrics():
    # Create sample data with dates
    df = pl.DataFrame({
        "species": ["A", "A", "A", "A", "A"],
        "grid_cell": ["cell1", "cell1", "cell1", "cell1", "cell1"],
        "year": [2020, 2020, 2020, 2020, 2020],
        "date": ["2020-03-01", "2020-03-10", "2020-03-15", "2020-03-20", "2020-03-25"],
        "checklist_id": ["1", "2", "3", "4", "5"],
    })
    df = df.with_columns(pl.col("date").str.to_date())

    # Aggregate to daily first (simulating the pipeline step)
    df_daily = (
        df.group_by(["species", "grid_cell", "year", "date"])
        .agg(pl.col("checklist_id").count().alias("count"))
    )

    # Now compute phenology on daily data
    # We need to adapt the function to accept daily data
    # For this test, we will simulate the group_by step inside the test
    # or call the function on the daily data.
    # The function `compute_phenology_metrics` expects a DataFrame with 'date' column.
    # We will group by species, grid_cell, year and compute.
    # Since the function implementation does the grouping, we pass the daily data.
    # But the function implementation expects the input to be the raw/daily data.
    # Let's adjust the test to match the function's expected input.
    # The function does: group_by -> agg -> compute percentiles.
    # So we pass the daily data.
    result = compute_phenology_metrics(df_daily)
    assert result.height == 1
    assert "first_arrival_date" in result.columns
    assert "stopover_duration" in result.columns
    assert result["stopover_duration"][0] > 0

def test_mark_insufficient_cells():
    df = pl.DataFrame({
        "species": ["A", "B"],
        "grid_cell": ["1", "2"],
        "year": [2020, 2020],
        "observation_count": [5, 15],
    })
    result = mark_insufficient_cells(df)
    assert result["data_quality"].to_list() == ["insufficient", "sufficient"]

def test_generate_provenance():
    df = pl.DataFrame({
        "species": ["A"],
        "grid_cell": ["1"],
        "year": [2020],
        "first_arrival_date": [pl.date(2020, 3, 1)],
        "median_arrival_date": [pl.date(2020, 3, 10)],
        "stopover_duration": [5.0],
        "observation_count": [10],
        "data_quality": ["sufficient"],
    })
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "mapping.json"
        generate_provenance(df, path)
        assert path.exists()
        import json
        with open(path) as f:
            data = json.load(f)
        assert len(data) == 1
        assert "processed_row_id" in data[0]
        assert "original_checklist_id" in data[0]
        assert "species" in data[0]
        assert "grid_cell" in data[0]