"""
Unit tests for the mock data generator.

Verifies that mock data is generated deterministically and contains
the expected structure and non-null IDs.
"""
import json
import os
import pytest
import tempfile
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.mock_generator import (
    generate_all_mock_data,
    _generate_population_ids,
    _generate_env_ids,
    _generate_compound_ids,
    MOCK_SEED
)

class TestMockGenerator:
    """Test cases for mock_generator module."""

    def test_id_generation_deterministic(self):
        """Verify ID generation is deterministic."""
        pop_ids_1 = _generate_population_ids(10)
        pop_ids_2 = _generate_population_ids(10)
        assert pop_ids_1 == pop_ids_2, "Population IDs should be deterministic"

        env_ids_1 = _generate_env_ids(10)
        env_ids_2 = _generate_env_ids(10)
        assert env_ids_1 == env_ids_2, "Environment IDs should be deterministic"

        comp_ids_1 = _generate_compound_ids(10)
        comp_ids_2 = _generate_compound_ids(10)
        assert comp_ids_1 == comp_ids_2, "Compound IDs should be deterministic"

    def test_id_format(self):
        """Verify ID format matches expectations."""
        pops = _generate_population_ids(5)
        assert all(p.startswith("POP_") for p in pops), "Population IDs must start with POP_"
        assert len(pops) == 5, "Should generate correct number of IDs"

        envs = _generate_env_ids(5)
        assert all(e.startswith("ENV_") for e in envs), "Environment IDs must start with ENV_"

        comps = _generate_compound_ids(5)
        assert len(comps) == 5, "Should generate correct number of compound IDs"

    def test_full_generation_creates_files(self):
        """Verify that generate_all_mock_data creates the expected files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_all_mock_data(tmpdir)
            
            assert "genomic" in result, "Should return genomic file path"
            assert "environmental" in result, "Should return environmental file path"
            assert "compound" in result, "Should return compound file path"
            
            # Check files exist
            assert os.path.exists(result["genomic"]), "Genomic file should exist"
            assert os.path.exists(result["environmental"]), "Environmental file should exist"
            assert os.path.exists(result["compound"]), "Compound file should exist"
            assert os.path.exists(os.path.join(tmpdir, "mock_manifest.json")), "Manifest should exist"

    def test_genomic_data_structure(self):
        """Verify genomic data structure and content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_all_mock_data(tmpdir)
            
            with open(result["genomic"]) as f:
                data = json.load(f)
            
            # Check metadata
            assert "metadata" in data, "Should have metadata"
            assert data["metadata"]["source"] == "mock_generator", "Source should be mock_generator"
            assert data["metadata"]["seed"] == MOCK_SEED, "Seed should match constant"
            
            # Check variants
            assert "variants" in data, "Should have variants"
            assert len(data["variants"]) > 0, "Should have at least one variant"
            
            # Check samples
            assert "samples" in data, "Should have samples"
            assert len(data["samples"]) > 0, "Should have at least one sample"
            
            # Verify non-null population_id
            for sample in data["samples"]:
                assert "population_id" in sample, "Sample must have population_id"
                assert sample["population_id"] is not None, "population_id must not be None"
                assert sample["population_id"] != "", "population_id must not be empty"

    def test_environmental_data_structure(self):
        """Verify environmental data structure and content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_all_mock_data(tmpdir)
            
            with open(result["environmental"]) as f:
                data = json.load(f)
            
            assert "metadata" in data, "Should have metadata"
            assert "environmental_data" in data, "Should have environmental_data"
            assert len(data["environmental_data"]) > 0, "Should have at least one record"
            
            # Verify non-null env_id
            for record in data["environmental_data"]:
                assert "env_id" in record, "Record must have env_id"
                assert record["env_id"] is not None, "env_id must not be None"
                assert record["env_id"] != "", "env_id must not be empty"
                assert "latitude" in record, "Record must have latitude"
                assert "longitude" in record, "Record must have longitude"

    def test_compound_data_structure(self):
        """Verify compound data structure and content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_all_mock_data(tmpdir)
            
            with open(result["compound"]) as f:
                data = json.load(f)
            
            assert "metadata" in data, "Should have metadata"
            assert "compound_profiles" in data, "Should have compound_profiles"
            assert len(data["compound_profiles"]) > 0, "Should have at least one record"
            
            # Verify non-null IDs
            for record in data["compound_profiles"]:
                assert "population_id" in record, "Record must have population_id"
                assert "compound_id" in record, "Record must have compound_id"
                assert record["population_id"] is not None, "population_id must not be None"
                assert record["compound_id"] is not None, "compound_id must not be None"
                assert "concentration_umol_g" in record, "Record must have concentration"

    def test_manifest_checksums(self):
        """Verify manifest contains valid checksums."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_all_mock_data(tmpdir)
            
            manifest_path = os.path.join(tmpdir, "mock_manifest.json")
            with open(manifest_path) as f:
                manifest = json.load(f)
            
            assert "checksums" in manifest, "Manifest must have checksums"
            assert "genomic" in manifest["checksums"], "Should have genomic checksum"
            assert "environmental" in manifest["checksums"], "Should have environmental checksum"
            assert "compound" in manifest["checksums"], "Should have compound checksum"
            
            # Verify checksums are non-empty strings
            for key, checksum in manifest["checksums"].items():
                assert isinstance(checksum, str), f"{key} checksum must be string"
                assert len(checksum) > 0, f"{key} checksum must not be empty"

    def test_deterministic_output(self):
        """Verify that running twice produces identical output."""
        with tempfile.TemporaryDirectory() as tmpdir1:
            with tempfile.TemporaryDirectory() as tmpdir2:
                result1 = generate_all_mock_data(tmpdir1)
                result2 = generate_all_mock_data(tmpdir2)
                
                # Compare file contents
                with open(result1["genomic"]) as f1, open(result2["genomic"]) as f2:
                    assert f1.read() == f2.read(), "Genomic data should be identical"
                
                with open(result1["environmental"]) as f1, open(result2["environmental"]) as f2:
                    assert f1.read() == f2.read(), "Environmental data should be identical"
                
                with open(result1["compound"]) as f1, open(result2["compound"]) as f2:
                    assert f1.read() == f2.read(), "Compound data should be identical"
