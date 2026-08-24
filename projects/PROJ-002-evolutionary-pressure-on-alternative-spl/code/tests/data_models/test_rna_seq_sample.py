import pytest
from datetime import datetime
from code.data_models.rna_seq_sample import RNASeqSample


def test_rna_seq_sample_creation():
    """Test basic creation of an RNASeqSample object."""
    sample = RNASeqSample(
        accession_id="SRR123456",
        species="Homo_sapiens",
        fastq_path="/data/fastq/SRR123456.fastq.gz",
        replicate_group="rep1"
    )
    assert sample.accession_id == "SRR123456"
    assert sample.species == "Homo_sapiens"
    assert sample.fastq_path == "/data/fastq/SRR123456.fastq.gz"
    assert sample.replicate_group == "rep1"
    assert isinstance(sample.created_at, datetime)


def test_rna_seq_sample_to_dict():
    """Test conversion of RNASeqSample to dictionary."""
    sample = RNASeqSample(
        accession_id="SRR123456",
        species="Pan_troglodytes",
        fastq_path="s3://bucket/fastq/SRR123456.fastq.gz",
        replicate_group="rep2"
    )
    d = sample.to_dict()
    assert d['accession_id'] == "SRR123456"
    assert d['species'] == "Pan_troglodytes"
    assert d['fastq_path'] == "s3://bucket/fastq/SRR123456.fastq.gz"
    assert d['replicate_group'] == "rep2"
    assert 'created_at' in d


def test_rna_seq_sample_from_dict():
    """Test creation of RNASeqSample from dictionary."""
    data = {
        'accession_id': 'SRR789012',
        'species': 'Macaca_mulatta',
        'fastq_path': '/data/macaque/SRR789012.fastq.gz',
        'replicate_group': 'rep3',
        'created_at': '2023-10-27T10:00:00'
    }
    sample = RNASeqSample.from_dict(data)
    assert sample.accession_id == 'SRR789012'
    assert sample.species == 'Macaca_mulatta'
    assert sample.replicate_group == 'rep3'
    assert isinstance(sample.created_at, datetime)


def test_rna_seq_sample_round_trip():
    """Test that to_dict and from_dict preserve data."""
    original = RNASeqSample(
        accession_id="SRR111222",
        species="Callithrix_jacchus",
        fastq_path="http://example.com/SRR111222.fastq.gz",
        replicate_group="rep4"
    )
    data = original.to_dict()
    restored = RNASeqSample.from_dict(data)
    
    assert restored.accession_id == original.accession_id
    assert restored.species == original.species
    assert restored.fastq_path == original.fastq_path
    assert restored.replicate_group == original.replicate_group
    # created_at should match if ISO format is consistent
    assert restored.created_at == original.created_at
