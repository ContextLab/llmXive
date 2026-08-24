"""
Unit tests for the RNASeqSample data model.
"""
import pytest
from pathlib import Path
from datetime import datetime
import tempfile
import os

from code.data_models.rna_seq_sample import RNASeqSample


class TestRNASeqSampleCreation:
    """Tests for RNASeqSample instantiation and basic properties."""

    def test_create_sample_with_required_fields(self):
        """Test creating a sample with all required fields."""
        sample = RNASeqSample(
            accession_id="SRR123456",
            species="Homo_sapiens",
            fastq_path="/data/fastq/sample_1.fastq.gz",
            replicate_group="rep1"
        )
        
        assert sample.accession_id == "SRR123456"
        assert sample.species == "Homo_sapiens"
        assert sample.replicate_group == "rep1"
        assert isinstance(sample.fastq_path, Path)
        assert sample.fastq_path == Path("/data/fastq/sample_1.fastq.gz")
        assert isinstance(sample.created_at, datetime)

    def test_create_sample_with_path_object(self):
        """Test creating a sample with a Path object for fastq_path."""
        path_obj = Path("/data/fastq/sample_2.fastq.gz")
        sample = RNASeqSample(
            accession_id="SRR789012",
            species="Pan_troglodytes",
            fastq_path=path_obj,
            replicate_group="rep2"
        )
        
        assert sample.fastq_path == path_obj
        assert isinstance(sample.fastq_path, Path)

    def test_sample_immutability(self):
        """Test that RNASeqSample instances are immutable (frozen dataclass)."""
        sample = RNASeqSample(
            accession_id="SRR123456",
            species="Homo_sapiens",
            fastq_path="/data/fastq/sample.fastq.gz",
            replicate_group="rep1"
        )
        
        with pytest.raises(dataclasses.FrozenInstanceError):
            sample.accession_id = "SRR999999"


class TestRNASeqSampleProperties:
    """Tests for RNASeqSample computed properties."""

    def test_exists_property_when_file_exists(self):
        """Test the exists property when the file exists."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            sample = RNASeqSample(
                accession_id="SRR123456",
                species="Homo_sapiens",
                fastq_path=tmp_path,
                replicate_group="rep1"
            )
            assert sample.exists is True
        finally:
            os.unlink(tmp_path)

    def test_exists_property_when_file_missing(self):
        """Test the exists property when the file doesn't exist."""
        sample = RNASeqSample(
            accession_id="SRR123456",
            species="Homo_sapiens",
            fastq_path="/nonexistent/path/file.fastq.gz",
            replicate_group="rep1"
        )
        assert sample.exists is False

    def test_file_size_when_exists(self):
        """Test the file_size property when the file exists."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test data" * 100)
            tmp_path = tmp.name
        
        try:
            sample = RNASeqSample(
                accession_id="SRR123456",
                species="Homo_sapiens",
                fastq_path=tmp_path,
                replicate_group="rep1"
            )
            assert sample.file_size == 900  # 9 bytes * 100
        finally:
            os.unlink(tmp_path)

    def test_file_size_when_missing(self):
        """Test the file_size property when the file doesn't exist."""
        sample = RNASeqSample(
            accession_id="SRR123456",
            species="Homo_sapiens",
            fastq_path="/nonexistent/path/file.fastq.gz",
            replicate_group="rep1"
        )
        assert sample.file_size == 0


class TestRNASeqSampleSerialization:
    """Tests for RNASeqSample dictionary conversion."""

    def test_to_dict(self):
        """Test converting sample to dictionary."""
        sample = RNASeqSample(
            accession_id="SRR123456",
            species="Homo_sapiens",
            fastq_path="/data/fastq/sample.fastq.gz",
            replicate_group="rep1"
        )
        
        d = sample.to_dict()
        
        assert d['accession_id'] == "SRR123456"
        assert d['species'] == "Homo_sapiens"
        assert d['fastq_path'] == "/data/fastq/sample.fastq.gz"
        assert d['replicate_group'] == "rep1"
        assert 'created_at' in d

    def test_from_dict(self):
        """Test creating sample from dictionary."""
        data = {
            'accession_id': "SRR123456",
            'species': "Homo_sapiens",
            'fastq_path': "/data/fastq/sample.fastq.gz",
            'replicate_group': "rep1",
            'created_at': datetime.now().isoformat()
        }
        
        sample = RNASeqSample.from_dict(data)
        
        assert sample.accession_id == "SRR123456"
        assert sample.species == "Homo_sapiens"
        assert sample.replicate_group == "rep1"
        assert sample.fastq_path == Path("/data/fastq/sample.fastq.gz")

    def test_round_trip_serialization(self):
        """Test that to_dict -> from_dict preserves data."""
        original = RNASeqSample(
            accession_id="SRR123456",
            species="Homo_sapiens",
            fastq_path="/data/fastq/sample.fastq.gz",
            replicate_group="rep1"
        )
        
        data = original.to_dict()
        restored = RNASeqSample.from_dict(data)
        
        assert original.accession_id == restored.accession_id
        assert original.species == restored.species
        assert original.replicate_group == restored.replicate_group
        assert original.fastq_path == restored.fastq_path


class TestRNASeqSampleStringRepresentation:
    """Tests for string representation."""

    def test_str_representation(self):
        """Test the string representation of a sample."""
        sample = RNASeqSample(
            accession_id="SRR123456",
            species="Homo_sapiens",
            fastq_path="/data/fastq/sample.fastq.gz",
            replicate_group="rep1"
        )
        
        str_repr = str(sample)
        
        assert "SRR123456" in str_repr
        assert "Homo_sapiens" in str_repr
        assert "rep1" in str_repr
        assert "RNASeqSample" in str_repr
