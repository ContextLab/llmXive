"""
Unit tests for the merge module.

These tests verify the correct behavior of data merging, aggregation detection,
and species-level aggregation logic.
"""

import os
import csv
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from src.data.merge import (
    detect_aggregation_need,
    aggregate_by_species,
    write_species_aggregates,
    write_aggregated_results,
    load_genomic_features,
    load_phenotypic_scores,
    align_genomic_phenotypic
)
from src.utils.errors import DataFetchError


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


@pytest.fixture
def low_linkage_phenotypic_csv(temp_dir):
    """Create a CSV with low linkage ratio (needs aggregation)."""
    # 10 isolates, 5 species, each species has 2 isolates -> linkage = 10/10 = 1.0
    # But we want low linkage, so let's have 5 species with 1 isolate each -> linkage = 0/5 = 0
    data = [
        {'species_name': 'species_a', 'isolate_id': 'iso_1', 'phenotype_score': 0.8},
        {'species_name': 'species_b', 'isolate_id': 'iso_2', 'phenotype_score': 0.7},
        {'species_name': 'species_c', 'isolate_id': 'iso_3', 'phenotype_score': 0.6},
        {'species_name': 'species_d', 'isolate_id': 'iso_4', 'phenotype_score': 0.9},
        {'species_name': 'species_e', 'isolate_id': 'iso_5', 'phenotype_score': 0.5},
    ]
    csv_path = temp_dir / 'low_linkage_phenotypes.csv'
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    return csv_path


def test_detect_aggregation_need_low_linkage(low_linkage_phenotypic_csv):
    """Test that low linkage ratio triggers aggregation need."""
    df = pd.read_csv(low_linkage_phenotypic_csv)
    
    needs_agg, total, linked = detect_aggregation_need(df, key_col='species_name')
    
    # With 5 species each having 1 isolate, linked = 0, total = 5
    # linkage_ratio = 0/5 = 0.0 < 0.5 -> needs_aggregation = True
    assert needs_agg is True
    assert total == 5
    assert linked == 0


def test_aggregate_by_species(temp_dir):
    """Test species-level aggregation."""
    # Create test data with multiple isolates per species
    data = [
        {'species_name': 'species_a', 'isolate_id': 'iso_1', 'phenotype_score': 0.8},
        {'species_name': 'species_a', 'isolate_id': 'iso_2', 'phenotype_score': 0.6},
        {'species_name': 'species_b', 'isolate_id': 'iso_3', 'phenotype_score': 0.9},
        {'species_name': 'species_b', 'isolate_id': 'iso_4', 'phenotype_score': 0.7},
        {'species_name': 'species_b', 'isolate_id': 'iso_5', 'phenotype_score': 0.5},
    ]
    df = pd.DataFrame(data)
    
    aggregated = aggregate_by_species(df, key_col='species_name')
    
    assert len(aggregated) == 2
    assert 'species_a' in aggregated['species_name'].values
    assert 'species_b' in aggregated['species_name'].values
    
    # Check species_a aggregation (0.8 + 0.6) / 2 = 0.7
    species_a_row = aggregated[aggregated['species_name'] == 'species_a']
    assert abs(species_a_row['avg_phenotype'].values[0] - 0.7) < 0.001
    assert species_a_row['isolate_count'].values[0] == 2
    
    # Check species_b aggregation (0.9 + 0.7 + 0.5) / 3 = 0.7
    species_b_row = aggregated[aggregated['species_name'] == 'species_b']
    assert abs(species_b_row['avg_phenotype'].values[0] - 0.7) < 0.001
    assert species_b_row['isolate_count'].values[0] == 3


def test_write_species_aggregates(temp_dir):
    """Test writing species aggregates to parquet."""
    # Create test data
    data = [
        {'species_name': 'species_a', 'avg_phenotype': 0.7, 'isolate_count': 2, 'variance': 0.02},
        {'species_name': 'species_b', 'avg_phenotype': 0.7, 'isolate_count': 3, 'variance': 0.0267},
    ]
    df = pd.DataFrame(data)
    
    output_path = temp_dir / 'species_aggregates.parquet'
    write_species_aggregates(df, output_path)
    
    assert output_path.exists()
    
    # Read back and verify
    loaded_df = pd.read_parquet(output_path)
    assert len(loaded_df) == 2
    assert 'species_name' in loaded_df.columns
    assert 'avg_phenotype' in loaded_df.columns


def test_write_aggregated_results(temp_dir):
    """Test writing aggregated results with metadata."""
    # Create test data
    data = [
        {'species_name': 'species_a', 'avg_phenotype': 0.7, 'isolate_count': 2, 'variance': 0.02},
    ]
    df = pd.DataFrame(data)
    
    output_path = temp_dir / 'aggregated_results.parquet'
    metadata = {'test_key': 'test_value', 'count': 1}
    
    write_aggregated_results(df, output_path, metadata=metadata)
    
    assert output_path.exists()
    
    # Check metadata file
    metadata_path = output_path.with_suffix('.json')
    assert metadata_path.exists()
    
    import json
    with open(metadata_path, 'r') as f:
        loaded_metadata = json.load(f)
    
    assert loaded_metadata['test_key'] == 'test_value'
    assert loaded_metadata['count'] == 1


def test_load_genomic_features_parquet(temp_dir):
    """Test loading genomic features from parquet."""
    # Create test parquet file
    data = {'feature_id': [1, 2, 3], 'value': [0.1, 0.2, 0.3]}
    df = pd.DataFrame(data)
    path = temp_dir / 'genomic_features.parquet'
    df.to_parquet(path)
    
    loaded = load_genomic_features(path)
    
    assert len(loaded) == 3
    assert 'feature_id' in loaded.columns


def test_load_phenotypic_scores_csv(temp_dir):
    """Test loading phenotypic scores from CSV."""
    # Create test CSV file
    path = temp_dir / 'phenotypic_scores.csv'
    data = [
        {'species_name': 'a', 'phenotype_score': 0.8},
        {'species_name': 'b', 'phenotype_score': 0.9},
    ]
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    
    loaded = load_phenotypic_scores(path)
    
    assert len(loaded) == 2
    assert 'phenotype_score' in loaded.columns


def test_align_genomic_phenotypic(temp_dir):
    """Test alignment of genomic and phenotypic data."""
    # Create test genomic data
    genomic_data = [
        {'species_name': 'a', 'feature1': 0.1, 'isolate_id': 'iso_1'},
        {'species_name': 'a', 'feature1': 0.2, 'isolate_id': 'iso_2'},
        {'species_name': 'b', 'feature1': 0.3, 'isolate_id': 'iso_3'},
    ]
    genomic_df = pd.DataFrame(genomic_data)
    
    # Create test phenotypic data (missing species 'c')
    phenotypic_data = [
        {'species_name': 'a', 'phenotype_score': 0.8},
        {'species_name': 'b', 'phenotype_score': 0.9},
    ]
    phenotypic_df = pd.DataFrame(phenotypic_data)
    
    merged, total, missing = align_genomic_phenotypic(genomic_df, phenotypic_df, key_col='species_name')
    
    # Should have 3 rows (all genomic rows match phenotypic)
    assert len(merged) == 3
    assert total == 3
    assert missing == 0
    
    # Check columns
    assert 'feature1' in merged.columns
    assert 'phenotype_score' in merged.columns


def test_align_genomic_phenotypic_missing(temp_dir):
    """Test alignment with missing phenotypes."""
    # Create test genomic data
    genomic_data = [
        {'species_name': 'a', 'feature1': 0.1, 'isolate_id': 'iso_1'},
        {'species_name': 'b', 'feature1': 0.2, 'isolate_id': 'iso_2'},
        {'species_name': 'c', 'feature1': 0.3, 'isolate_id': 'iso_3'},
    ]
    genomic_df = pd.DataFrame(genomic_data)
    
    # Create test phenotypic data (missing species 'c')
    phenotypic_data = [
        {'species_name': 'a', 'phenotype_score': 0.8},
        {'species_name': 'b', 'phenotype_score': 0.9},
    ]
    phenotypic_df = pd.DataFrame(phenotypic_data)
    
    merged, total, missing = align_genomic_phenotypic(genomic_df, phenotypic_df, key_col='species_name')
    
    # Should have 2 rows (species 'c' dropped)
    assert len(merged) == 2
    assert total == 3
    assert missing == 0  # Inner join removes missing, so missing count is 0 after join


def test_detect_aggregation_need_high_linkage(temp_dir):
    """Test that high linkage ratio does not trigger aggregation."""
    # Create data with high linkage (most isolates belong to species with multiple isolates)
    data = [
        {'species_name': 'species_a', 'isolate_id': 'iso_1', 'phenotype_score': 0.8},
        {'species_name': 'species_a', 'isolate_id': 'iso_2', 'phenotype_score': 0.7},
        {'species_name': 'species_a', 'isolate_id': 'iso_3', 'phenotype_score': 0.6},
        {'species_name': 'species_b', 'isolate_id': 'iso_4', 'phenotype_score': 0.9},
        {'species_name': 'species_b', 'isolate_id': 'iso_5', 'phenotype_score': 0.5},
        {'species_name': 'species_c', 'isolate_id': 'iso_6', 'phenotype_score': 0.4},  # Single isolate
    ]
    df = pd.DataFrame(data)
    
    needs_agg, total, linked = detect_aggregation_need(df, key_col='species_name')
    
    # Total isolates: 6
    # Linked isolates (species with >1): 3 (species_a) + 2 (species_b) = 5
    # Linkage ratio: 5/6 = 0.833 > 0.5 -> needs_aggregation = False
    assert needs_agg is False
    assert total == 6
    assert linked == 5