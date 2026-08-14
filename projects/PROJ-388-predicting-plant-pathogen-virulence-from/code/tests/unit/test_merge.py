import os
import csv
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
import numpy as np
import pyarrow.parquet as pq

from src.data.merge import (
    load_genomic_features,
    load_phenotypic_scores,
    align_genomic_phenotypic,
    detect_aggregation_need,
    aggregate_by_species,
    write_merged_dataset,
    write_species_aggregates
)

@pytest.fixture
def temp_dir():
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)

@pytest.fixture
def genomic_csv(temp_dir):
    path = temp_dir / "genomic.csv"
    data = [
        ["isolate_id", "species_name", "feature_A", "feature_B"],
        ["iso1", "Fusarium", 1, 0],
        ["iso2", "Fusarium", 0, 1],
        ["iso3", "Pseudomonas", 1, 1],
        ["iso4", "Xanthomonas", 0, 0]
    ]
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(data)
    return path

@pytest.fixture
def phenotypic_csv(temp_dir):
    path = temp_dir / "phenotypic.csv"
    data = [
        ["isolate_id", "species_name", "phenotype_score"],
        ["iso1", "Fusarium", 0.8],
        ["iso2", "Fusarium", 0.6],
        ["iso3", "Pseudomonas", 0.9],
        # iso4 missing
    ]
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(data)
    return path

@pytest.fixture
def low_linkage_phenotypic_csv(temp_dir):
    path = temp_dir / "low_linkage_phenotypic.csv"
    data = [
        ["isolate_id", "species_name", "phenotype_score"],
        ["iso1", "Fusarium", 0.8],
        # iso2, iso3, iso4 missing
    ]
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(data)
    return path

def test_load_genomic_features(temp_dir, genomic_csv):
    # Create a parquet file for testing
    df = pd.DataFrame({
        "isolate_id": ["iso1", "iso2"],
        "species_name": ["Fusarium", "Fusarium"],
        "feature_A": [1, 0]
    })
    path = temp_dir / "test_genomic.parquet"
    df.to_parquet(path)
    
    result = load_genomic_features(str(path))
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2
    assert "feature_A" in result.columns

def test_load_phenotypic_scores(temp_dir, phenotypic_csv):
    # Create a parquet file for testing
    df = pd.DataFrame({
        "isolate_id": ["iso1", "iso2"],
        "phenotype_score": [0.8, 0.6]
    })
    path = temp_dir / "test_phenotypic.parquet"
    df.to_parquet(path)
    
    result = load_phenotypic_scores(str(path))
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2
    assert "phenotype_score" in result.columns

def test_align_and_merge_isolate_level(temp_dir, genomic_csv, phenotypic_csv):
    # Convert CSVs to Parquet for the function
    gen_df = pd.read_csv(str(genomic_csv))
    phen_df = pd.read_csv(str(phenotypic_csv))
    
    gen_path = temp_dir / "gen.parquet"
    phen_path = temp_dir / "phen.parquet"
    gen_df.to_parquet(gen_path)
    phen_df.to_parquet(phen_path)
    
    loaded_gen = load_genomic_features(str(gen_path))
    loaded_phen = load_phenotypic_scores(str(phen_path))
    
    merged = align_genomic_phenotypic(loaded_gen, loaded_phen)
    
    assert len(merged) == 3  # iso4 should be dropped
    assert "phenotype_score" in merged.columns
    assert merged["phenotype_score"].isna().sum() == 0

def test_detect_aggregation_need_high_linkage(temp_dir):
    # Create a dataframe with 10 rows, 9 have phenotypes
    df = pd.DataFrame({
        "species_name": ["Fusarium"] * 10,
        "phenotype_score": [0.5] * 9 + [np.nan]
    })
    needs_agg, linked, total = detect_aggregation_need(df)
    assert needs_agg is False
    assert linked == 9
    assert total == 10

def test_detect_aggregation_need_low_linkage(temp_dir):
    # Create a dataframe with 10 rows, 4 have phenotypes
    df = pd.DataFrame({
        "species_name": ["Fusarium"] * 10,
        "phenotype_score": [0.5] * 4 + [np.nan] * 6
    })
    needs_agg, linked, total = detect_aggregation_need(df)
    assert needs_agg is True
    assert linked == 4
    assert total == 10

def test_aggregate_by_species(temp_dir):
    df = pd.DataFrame({
        "species_name": ["Fusarium", "Fusarium", "Pseudomonas"],
        "phenotype_score": [0.8, 0.6, 0.9],
        "feature_A": [1, 0, 1],
        "isolate_id": ["iso1", "iso2", "iso3"]
    })
    
    result = aggregate_by_species(df)
    
    assert len(result) == 2
    assert "species_name" in result.columns
    assert "avg_phenotype" in result.columns
    assert "isolate_count" in result.columns
    
    # Check Fusarium average
    fusarium_row = result[result["species_name"] == "Fusarium"]
    assert abs(fusarium_row["avg_phenotype"].values[0] - 0.7) < 1e-6
    assert fusarium_row["isolate_count"].values[0] == 2

def test_write_merged_dataset(temp_dir):
    df = pd.DataFrame({
        "isolate_id": ["iso1"],
        "phenotype_score": [0.8]
    })
    path = temp_dir / "merged.parquet"
    write_merged_dataset(df, str(path))
    
    assert path.exists()
    loaded = pq.read_table(str(path)).to_pandas()
    assert len(loaded) == 1

def test_write_species_aggregates(temp_dir):
    df = pd.DataFrame({
        "species_name": ["Fusarium"],
        "avg_phenotype": [0.7],
        "isolate_count": [2]
    })
    path = temp_dir / "aggregates.parquet"
    write_species_aggregates(df, str(path))
    
    assert path.exists()
    loaded = pq.read_table(str(path)).to_pandas()
    assert len(loaded) == 1
    assert "species_name" in loaded.columns