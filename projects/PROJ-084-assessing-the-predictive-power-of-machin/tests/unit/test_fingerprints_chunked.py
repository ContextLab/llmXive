"""
Unit tests for chunked fingerprint generation (T016).

Tests verify:
- ECFP4 generates 2048 bits
- MACCS generates 167 bits
- Chunked processing works correctly
- Output schema compliance
"""

import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from rdkit import Chem

# Import functions to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from preprocessing.fingerprints import (
    generate_ecfp4,
    generate_maccs,
    generate_fingerprints_batch,
    process_fingerprints_chunked,
    log_dimensions,
    compute_and_record_checksum
)


class TestECFP4Generation:
    """Tests for ECFP4 fingerprint generation."""

    def test_ecfp4_bit_length(self):
        """Test that ECFP4 generates exactly 2048 bits."""
        smiles = "CCO"  # Ethanol
        fp = generate_ecfp4(smiles)
        assert len(fp) == 2048, f"Expected 2048 bits, got {len(fp)}"
        assert all(isinstance(bit, bool) for bit in fp), "All bits should be boolean"

    def test_ecfp4_empty_molecule(self):
        """Test ECFP4 handling of invalid SMILES."""
        fp = generate_ecfp4("invalid_smiles")
        assert len(fp) == 2048, "Invalid SMILES should return all False"
        assert all(bit is False for bit in fp), "Invalid SMILES should return all False"

    def test_ecfp4_different_molecules(self):
        """Test that different molecules produce different fingerprints."""
        smiles1 = "CCO"
        smiles2 = "CCCO"
        fp1 = generate_ecfp4(smiles1)
        fp2 = generate_ecfp4(smiles2)
        assert fp1 != fp2, "Different molecules should have different fingerprints"


class TestMACCSGeneration:
    """Tests for MACCS fingerprint generation."""

    def test_maccs_bit_length(self):
        """Test that MACCS generates exactly 167 bits."""
        smiles = "CCO"  # Ethanol
        fp = generate_maccs(smiles)
        assert len(fp) == 167, f"Expected 167 bits, got {len(fp)}"
        assert all(isinstance(bit, bool) for bit in fp), "All bits should be boolean"

    def test_maccs_empty_molecule(self):
        """Test MACCS handling of invalid SMILES."""
        fp = generate_maccs("invalid_smiles")
        assert len(fp) == 167, "Invalid SMILES should return all False"
        assert all(bit is False for bit in fp), "Invalid SMILES should return all False"


class TestBatchProcessing:
    """Tests for batch fingerprint generation."""

    def test_batch_processing(self):
        """Test batch processing of multiple reactions."""
        data = {
            'smiles': ['CCO', 'CCCO', 'CCCCO', 'invalid']
        }
        df = pd.DataFrame(data)
        result = generate_fingerprints_batch(df)

        assert 'fingerprint_ecfp' in result.columns
        assert 'fingerprint_maccs' in result.columns
        assert len(result) == 4

        # Check ECFP dimensions
        for i, fp in enumerate(result['fingerprint_ecfp']):
            assert len(fp) == 2048, f"Row {i}: ECFP should have 2048 bits"

        # Check MACCS dimensions
        for i, fp in enumerate(result['fingerprint_maccs']):
            assert len(fp) == 167, f"Row {i}: MACCS should have 167 bits"


class TestChunkedProcessing:
    """Tests for chunked fingerprint processing."""

    def test_chunked_processing_creates_output(self):
        """Test that chunked processing creates output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.parquet"
            output_path = Path(tmpdir) / "output.parquet"

            # Create test data
            data = {
                'smiles': ['CCO'] * 100  # 100 rows
            }
            df = pd.DataFrame(data)
            df.to_parquet(input_path)

            # Process in chunks
            stats = process_fingerprints_chunked(
                input_path=input_path,
                output_path=output_path,
                chunk_size=50
            )

            assert output_path.exists(), "Output file should be created"
            assert stats['total_rows'] == 100
            assert stats['chunks_processed'] == 2

            # Verify output content
            result = pd.read_parquet(output_path)
            assert 'fingerprint_ecfp' in result.columns
            assert 'fingerprint_maccs' in result.columns
            assert len(result) == 100


class TestLoggingAndChecksums:
    """Tests for logging and checksum functionality."""

    def test_log_dimensions_creates_file(self):
        """Test that log_dimensions creates the log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "fingerprint_dimensions.log"
            log_dimensions(log_path)

            assert log_path.exists(), "Log file should be created"
            content = log_path.read_text()
            assert "ECFP4" in content
            assert "2048" in content
            assert "MACCS" in content
            assert "167" in content

    def test_compute_checksum_records_hash(self):
        """Test that checksum computation records hash correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            checksums_file = Path(tmpdir) / "checksums.json"

            test_file.write_text("test content")

            hash_value = compute_and_record_checksum(test_file, checksums_file)

            assert len(hash_value) == 64, "SHA256 hash should be 64 characters"
            assert checksums_file.exists(), "Checksums file should be created"

            with open(checksums_file, 'r') as f:
                checksums = json.load(f)

            assert 'fingerprint_dimensions.log' in checksums
            assert checksums['fingerprint_dimensions.log']['hash'] == hash_value


class TestSchemaCompliance:
    """Tests for schema compliance of fingerprint output."""

    def test_fingerprint_schema_compliance(self):
        """Test that generated fingerprints match the dataset schema."""
        # Load schema
        schema_path = Path(__file__).parent.parent.parent / "specs" / \
                     "001-assess-ml-predictive-power" / "contracts" / "dataset.schema.yaml"

        if not schema_path.exists():
            pytest.skip("Schema file not found, skipping schema compliance test")

        with open(schema_path, 'r') as f:
            import yaml
            schema = yaml.safe_load(f)

        # Generate test fingerprints
        smiles = "CCO"
        ecfp = generate_ecfp4(smiles)
        maccs = generate_maccs(smiles)

        # Validate ECFP
        ecfp_schema = schema['properties']['fingerprint_ecfp']
        assert ecfp_schema['type'] == 'array'
        assert ecfp_schema['items']['type'] == 'boolean'
        assert len(ecfp) == 2048, "ECFP must be 2048 bits per schema"

        # Validate MACCS
        maccs_schema = schema['properties']['fingerprint_maccs']
        assert maccs_schema['type'] == 'array'
        assert maccs_schema['items']['type'] == 'boolean'
        assert len(maccs) == 167, "MACCS must be 167 bits per schema"