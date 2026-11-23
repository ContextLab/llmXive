"""
Unit tests for manifest validation in ingest.py
"""
import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path

from code.ingest import load_manifest, validate_manifest

# Create a temporary schema file for testing
TEST_SCHEMA = """
type: object
required:
  - doi
  - dataset_name
properties:
  doi:
    type: string
  dataset_name:
    type: string
  dataset_url:
    type: string
"""

def test_load_manifest_csv():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("doi,dataset_name\n10.123/test,TestSet\n")
        temp_path = f.name
    
    try:
        df = load_manifest(temp_path)
        assert len(df) == 1
        assert df.iloc[0]['doi'] == '10.123/test'
    finally:
        os.unlink(temp_path)

def test_validate_manifest_valid():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as sf:
        sf.write(TEST_SCHEMA)
        schema_path = sf.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as df:
        df.write("doi,dataset_name\n10.123/test,TestSet\n")
        manifest_path = df.name
    
    try:
        manifest_df = load_manifest(manifest_path)
        is_valid, errors = validate_manifest(manifest_df, schema_path)
        assert is_valid
        assert len(errors) == 0
    finally:
        os.unlink(schema_path)
        os.unlink(manifest_path)

def test_validate_manifest_invalid():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as sf:
        sf.write(TEST_SCHEMA)
        schema_path = sf.name
    
    # Missing required field 'dataset_name'
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as df:
        df.write("doi\n10.123/test\n")
        manifest_path = df.name
    
    try:
        manifest_df = load_manifest(manifest_path)
        is_valid, errors = validate_manifest(manifest_df, schema_path)
        assert not is_valid
        assert len(errors) > 0
        assert "dataset_name" in str(errors[0])
    finally:
        os.unlink(schema_path)
        os.unlink(manifest_path)