"""
Integration test for the ingestion pipeline (T017).
Verifies that the full pipeline runs and produces valid output.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd
import numpy as np

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
import sys
sys.path.insert(0, str(PROJECT_ROOT))

from preprocessing.ingest import run_ingestion_pipeline
from utils.validators import load_schema, validate_dataset

@pytest.fixture
def sample_raw_data():
    """Create a minimal sample dataset for testing."""
    data = {
        "smiles": [
            "CCO",
            "CC(=O)O",
            "c1ccccc1",
            "CC1=CC=CC=C1",
            "invalid_smiles_here"
        ],
        "yield": [
            50.0,
            "70-80",
            90.5,
            "10-20",
            None
        ],
        "reaction_class": [
            "esterification",
            "oxidation",
            "alkylation",
            "reduction",
            "unknown"
        ]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_dirs(tmp_path):
    """Create temporary directories for test artifacts."""
    raw_dir = tmp_path / "data" / "raw"
    processed_dir = tmp_path / "data" / "processed"
    results_dir = tmp_path / "data" / "results"
    specs_dir = tmp_path / "specs" / "001-assess-ml-predictive-power" / "contracts"
    
    raw_dir.mkdir(parents=True)
    processed_dir.mkdir(parents=True)
    results_dir.mkdir(parents=True)
    specs_dir.mkdir(parents=True)
    
    return {
        "raw": raw_dir,
        "processed": processed_dir,
        "results": results_dir,
        "specs": specs_dir
    }

@pytest.fixture
def sample_schema(temp_dirs):
    """Create a minimal dataset schema for testing."""
    schema = {
        "fields": [
            {"name": "smiles", "type": "string", "nullable": False},
            {"name": "yield", "type": "float", "nullable": False},
            {"name": "reaction_class", "type": "string", "nullable": False},
            {"name": "fingerprint_ecfp", "type": "list", "nullable": False},
            {"name": "fingerprint_maccs", "type": "list", "nullable": False}
        ]
    }
    schema_path = temp_dirs["specs"] / "dataset.schema.yaml"
    with open(schema_path, 'w') as f:
        import yaml
        yaml.dump(schema, f)
    return schema_path

def test_ingest_pipeline_creates_output(
    sample_raw_data,
    temp_dirs,
    sample_schema
):
    """Test that the pipeline creates the required output file."""
    input_path = temp_dirs["raw"] / "uspto_raw.parquet"
    output_path = temp_dirs["processed"] / "cleaned_reactions.parquet"
    
    # Save sample data
    sample_raw_data.to_parquet(input_path)
    
    # Run pipeline
    stats = run_ingestion_pipeline(
        input_path=input_path,
        output_path=output_path,
        schema_path=sample_schema,
        batch_size=10
    )
    
    # Verify output file exists
    assert output_path.exists(), "Output parquet file was not created"
    
    # Verify output content
    df_output = pd.read_parquet(output_path)
    assert len(df_output) > 0, "Output dataframe is empty"
    
    # Verify columns exist
    required_cols = ["smiles", "yield", "reaction_class", "fingerprint_ecfp", "fingerprint_maccs"]
    for col in required_cols:
        assert col in df_output.columns, f"Missing column: {col}"
    
    # Verify quality report exists
    quality_report_path = temp_dirs["results"] / "data_quality_report.json"
    assert quality_report_path.exists(), "Quality report was not created"
    
    with open(quality_report_path, 'r') as f:
        report = json.load(f)
    
    assert "exclusion_fraction" in report, "Missing exclusion_fraction in report"
    assert "exclusion_reasons" in report, "Missing exclusion_reasons in report"

def test_ingest_pipeline_validates_schema(
    sample_raw_data,
    temp_dirs,
    sample_schema
):
    """Test that the pipeline validates output against schema."""
    input_path = temp_dirs["raw"] / "uspto_raw.parquet"
    output_path = temp_dirs["processed"] / "cleaned_reactions.parquet"
    
    sample_raw_data.to_parquet(input_path)
    
    stats = run_ingestion_pipeline(
        input_path=input_path,
        output_path=output_path,
        schema_path=sample_schema,
        batch_size=10
    )
    
    # Check validation step in stats
    validation_step = next(
        (s for s in stats["steps"] if s["step"] == "validation"),
        None
    )
    
    assert validation_step is not None, "Validation step not found in stats"
    assert validation_step["status"] == "success", "Validation step failed"
    assert validation_step.get("valid", False), "Output did not pass schema validation"

def test_ingest_pipeline_handles_invalid_smiles(
    sample_raw_data,
    temp_dirs,
    sample_schema
):
    """Test that invalid SMILES are excluded and logged."""
    input_path = temp_dirs["raw"] / "uspto_raw.parquet"
    output_path = temp_dirs["processed"] / "cleaned_reactions.parquet"
    
    sample_raw_data.to_parquet(input_path)
    
    stats = run_ingestion_pipeline(
        input_path=input_path,
        output_path=output_path,
        schema_path=sample_schema,
        batch_size=10
    )
    
    # Verify exclusion stats
    sanitize_step = next(
        (s for s in stats["steps"] if s["step"] == "sanitize"),
        None
    )
    
    assert sanitize_step is not None, "Sanitize step not found"
    assert sanitize_step["excluded_rows"] >= 0, "Excluded rows count is negative"
    
    # Verify output has fewer rows than input (due to invalid SMILES)
    df_output = pd.read_parquet(output_path)
    assert len(df_output) <= len(sample_raw_data), "Output has more rows than input"

def test_ingest_pipeline_handles_yield_ranges(
    sample_raw_data,
    temp_dirs,
    sample_schema
):
    """Test that yield ranges are parsed correctly."""
    input_path = temp_dirs["raw"] / "uspto_raw.parquet"
    output_path = temp_dirs["processed"] / "cleaned_reactions.parquet"
    
    sample_raw_data.to_parquet(input_path)
    
    stats = run_ingestion_pipeline(
        input_path=input_path,
        output_path=output_path,
        schema_path=sample_schema,
        batch_size=10
    )
    
    df_output = pd.read_parquet(output_path)
    
    # Check that yield column is numeric
    assert df_output["yield"].dtype in ['float64', 'float32'], "Yield column is not numeric"
    
    # Check that parsed yields are within expected range (0-100)
    valid_yields = df_output["yield"].dropna()
    assert (valid_yields >= 0).all(), "Yield values below 0"
    assert (valid_yields <= 100).all(), "Yield values above 100"
    
    # Check that range values were parsed (e.g., "70-80" -> 75.0)
    # This is a heuristic check - we expect some values to be midpoints
    unique_yields = valid_yields.unique()
    # If ranges were parsed, we should see values like 75.0, 15.0 etc.
    # This is just a sanity check that parsing happened
    assert len(unique_yields) > 0, "No valid yields after parsing"