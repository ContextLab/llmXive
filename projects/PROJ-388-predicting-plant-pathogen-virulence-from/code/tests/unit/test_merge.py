import os
import csv
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
import pyarrow.parquet as pq

from src.data.merge import (
    load_genomic_features,
    load_phenotypic_scores,
    align_and_merge,
    write_merged_dataset,
    MergeResult
)
from src.models.genomic_feature import GenomicFeature

@pytest.fixture
def temp_dir():
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)

@pytest.fixture
def genomic_csv(temp_dir):
    path = temp_dir / "genomic_features.csv"
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['isolate_id', 'feature_id', 'type', 'presence_binary', 'pwm_count', 'source'])
        writer.writerow(['strain_001', 'virA', 'gene', 1, 10, 'PHI-base'])
        writer.writerow(['strain_001', 'virB', 'gene', 0, 5, 'PHI-base'])
        writer.writerow(['strain_002', 'virA', 'gene', 1, 12, 'PHI-base'])
        writer.writerow(['strain_003', 'virA', 'gene', 1, 8, 'PHI-base'])
    return path

@pytest.fixture
def phenotypic_csv(temp_dir):
    path = temp_dir / "phenotypic_scores.csv"
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['isolate_id', 'score'])
        writer.writerow(['strain_001', 0.85])
        writer.writerow(['strain_002', 0.92])
        writer.writerow(['strain_004', 0.50]) # Missing in genomic
    return path

@pytest.fixture
def low_linkage_phenotypic_csv(temp_dir):
    path = temp_dir / "phenotypic_low_linkage.csv"
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['isolate_id', 'score'])
        # Only one match with genomic_csv
        writer.writerow(['strain_001', 0.85])
        writer.writerow(['strain_005', 0.60])
        writer.writerow(['strain_006', 0.70])
        writer.writerow(['strain_007', 0.75])
        writer.writerow(['strain_008', 0.80])
    return path

def test_load_genomic_features(genomic_csv):
    features = load_genomic_features(genomic_csv)
    assert len(features) == 4
    assert features[0].feature_id == 'virA'
    assert features[0].presence_binary == 1

def test_load_phenotypic_scores(phenotypic_csv):
    scores = load_phenotypic_scores(phenotypic_csv)
    assert len(scores) == 3
    assert scores['strain_001'] == 0.85
    assert 'strain_004' in scores

def test_align_and_merge_isolate_level(genomic_csv, phenotypic_csv):
    df, result = align_and_merge(genomic_csv, phenotypic_csv)
    assert len(df) == 2 # strain_001 and strain_002 match. strain_003 has no score.
    assert result.processed_count == 2
    assert result.missing_count == 1 # strain_003
    assert not result.is_aggregated

def test_align_and_merge_aggregate_level(genomic_csv, low_linkage_phenotypic_csv):
    # Only 1 match out of 3 genomic isolates -> 33% linkage < 50%
    # Should aggregate by species (if map provided) or handle gracefully.
    # For this test, we assume no map, so it might fail or just drop.
    # But the logic in align_and_merge checks linkage and aggregates if map is provided.
    # Without map, it just drops. Let's test the drop behavior first.
    
    # To test aggregation, we need a map.
    isolate_to_species_map = {
        'strain_001': 'SpeciesA',
        'strain_005': 'SpeciesB',
        'strain_006': 'SpeciesB',
        'strain_007': 'SpeciesC',
        'strain_008': 'SpeciesC'
    }
    
    df, result = align_and_merge(genomic_csv, low_linkage_phenotypic_csv, isolate_to_species_map)
    # Linkage is 1/3 = 33%. Should aggregate.
    assert result.is_aggregated
    # The resulting dataframe should have species-level rows.
    # We expect at least 'SpeciesA' to be present.
    assert 'species' in df.columns or 'species_name' in df.columns

def test_write_merged_dataset(temp_dir, genomic_csv, phenotypic_csv):
    df, result = align_and_merge(genomic_csv, phenotypic_csv)
    output_path = temp_dir / "merged.parquet"
    write_merged_dataset(df, output_path, result)
    
    assert output_path.exists()
    table = pq.read_table(output_path)
    assert table.num_rows == len(df)

def test_missing_phenotype_handling(genomic_csv, phenotypic_csv):
    # strain_003 in genomic has no score in phenotypic
    df, result = align_and_merge(genomic_csv, phenotypic_csv)
    # strain_003 should be dropped
    assert 'strain_003' not in df['isolate_id'].values
    assert result.missing_count == 1
