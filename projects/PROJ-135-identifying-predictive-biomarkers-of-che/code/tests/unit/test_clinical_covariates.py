"""
Unit tests for Clinical Covariate Extraction (T039b)
"""
import os
import sys
import json
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add code to path if running from root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.clinical_covariates import (
    load_raw_clinical_metadata,
    clean_and_format_covariates,
    write_covariates_to_csv
)

@pytest.fixture
def temp_raw_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_dir = Path(tmpdir) / "data" / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a mock clinical JSON file
        clinical_data = [
            {"sample_id": "S1", "age": 50, "stage": "I", "response": "Responder"},
            {"sample_id": "S2", "age": None, "stage": "II", "response": "Non-Responder"},
            {"sample_id": "S3", "age": 65, "stage": None, "response": "Responder"},
            {"sample_id": "S4", "age": 40, "stage": "III", "response": None}, # Should be dropped
            {"sample_id": "S5", "age": 55, "stage": "I", "response": "Responder"},
        ]
        
        with open(raw_dir / "GSE123_clinical.json", 'w') as f:
            json.dump(clinical_data, f)
        
        yield raw_dir

def test_load_raw_clinical_metadata(temp_raw_dir):
    df = load_raw_clinical_metadata(temp_raw_dir)
    assert len(df) == 5
    assert 'sample_id' in df.columns
    assert 'age' in df.columns
    assert 'stage' in df.columns
    assert 'response' in df.columns or 'response_label' in df.columns

def test_clean_and_format_covariates(temp_raw_dir):
    df_raw = load_raw_clinical_metadata(temp_raw_dir)
    df_clean = clean_and_format_covariates(df_raw)
    
    # Check dropped sample (S4 had no response)
    assert len(df_clean) == 4
    assert 'S4' not in df_clean['sample_id'].values
    
    # Check imputation for age (S2 had None)
    s2_row = df_clean[df_clean['sample_id'] == 'S2']
    assert not s2_row['age'].isna().all()
    
    # Check imputation for stage (S3 had None)
    s3_row = df_clean[df_clean['sample_id'] == 'S3']
    assert not s3_row['stage'].isna().all()
    
    # Check columns
    assert list(df_clean.columns) == ['sample_id', 'age', 'stage', 'response_label']
    
    # Check sorting
    assert df_clean['sample_id'].is_monotonic_increasing

def test_write_covariates_to_csv(temp_raw_dir):
    df_raw = load_raw_clinical_metadata(temp_raw_dir)
    df_clean = clean_and_format_covariates(df_raw)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "test_output.csv"
        write_covariates_to_csv(df_clean, out_path)
        
        assert out_path.exists()
        df_out = pd.read_csv(out_path)
        assert len(df_out) == 4
        assert list(df_out.columns) == ['sample_id', 'age', 'stage', 'response_label']