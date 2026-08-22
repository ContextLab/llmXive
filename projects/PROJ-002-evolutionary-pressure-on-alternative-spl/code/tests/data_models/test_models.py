"""Unit tests for data model classes."""

import pytest
from datetime import datetime
from code.data_models.models import RNASeqSample, SplicingEvent, EnrichmentResult, PhylogeneticTree

def test_rna_seq_sample_creation():
    """Test RNASeqSample instantiation and serialization."""
    sample = RNASeqSample(
        sample_id="S001",
        species="Homo_sapiens",
        assembly="GRCh38",
        sra_accession="SRR123456",
        fastq_path="/data/SRR123456.fastq.gz",
        replicates=["S002", "S003"]
    )
    assert sample.sample_id == "S001"
    assert sample.species == "Homo_sapiens"
    assert sample.replicates == ["S002", "S003"]
    assert sample.created_at is not None

    # Test serialization
    data = sample.to_dict()
    assert data["sample_id"] == "S001"
    assert "created_at" in data

    # Test deserialization
    sample2 = RNASeqSample.from_dict(data)
    assert sample2.sample_id == sample.sample_id
    assert sample2.species == sample.species

def test_splicing_event_creation():
    """Test SplicingEvent instantiation and serialization."""
    event = SplicingEvent(
        event_id="E001",
        event_type="SE",
        gene_id="ENSG000001",
        gene_name="GENE1",
        chromosome="chr1",
        start=1000,
        end=2000,
        strand="+",
        psi_values={"S001": 0.5, "S002": 0.6},
        is_lineage_specific=True,
        lineage="Human"
    )
    assert event.event_id == "E001"
    assert event.is_lineage_specific is True
    assert event.psi_values["S001"] == 0.5

    # Test serialization
    data = event.to_dict()
    assert data["event_type"] == "SE"
    assert data["is_lineage_specific"] is True

    # Test deserialization
    event2 = SplicingEvent.from_dict(data)
    assert event2.event_id == event.event_id
    assert event2.lineage == event.lineage

def test_enrichment_result_creation():
    """Test EnrichmentResult instantiation and serialization."""
    result = EnrichmentResult(
        result_id="R001",
        lineage="Human",
        method="phyloglm",
        predictor="mean_phyloP",
        response="is_lineage_specific",
        coefficient=2.5,
        p_value=0.001,
        fdr=0.01,
        n_events=150,
        n_controls=300
    )
    assert result.lineage == "Human"
    assert result.coefficient == 2.5
    assert result.p_value == 0.001

    # Test serialization
    data = result.to_dict()
    assert data["method"] == "phyloglm"
    assert data["n_events"] == 150

    # Test deserialization
    result2 = EnrichmentResult.from_dict(data)
    assert result2.result_id == result.result_id
    assert result2.odds_ratio == result.odds_ratio

def test_phylogenetic_tree_creation():
    """Test PhylogeneticTree instantiation and parsing."""
    newick_str = "((Human:1.0,Chimp:1.0):2.0,(Macaque:3.0,Marmoset:3.0):0.0);";
    tree = PhylogeneticTree(
        tree_id="primate_tree",
        newick=newick_str
    )
    assert tree.tree_id == "primate_tree"
    assert "Human" in tree.species
    assert "Chimp" in tree.species
    assert tree.root_name is not None

    # Test serialization
    data = tree.to_dict()
    assert data["newick"] == newick_str

    # Test deserialization
    tree2 = PhylogeneticTree.from_dict(data)
    assert tree2.tree_id == tree.tree_id

def test_model_equality_and_hashing():
    """Test that models support equality and hashing correctly."""
    sample1 = RNASeqSample(
        sample_id="S001",
        species="Homo_sapiens",
        assembly="GRCh38",
        sra_accession="SRR123456"
    )
    sample2 = RNASeqSample(
        sample_id="S001",
        species="Homo_sapiens",
        assembly="GRCh38",
        sra_accession="SRR123456"
    )
    sample3 = RNASeqSample(
        sample_id="S002",
        species="Homo_sapiens",
        assembly="GRCh38",
        sra_accession="SRR123456"
    )

    assert sample1 == sample2
    assert sample1 != sample3
    assert hash(sample1) == hash(sample2)
    assert hash(sample1) != hash(sample3)

    # Test in sets/dicts
    sample_set = {sample1, sample2, sample3}
    assert len(sample_set) == 2  # sample1 and sample2 are the same

def test_placeholder_flag():
    """Test that placeholder flag is correctly set and serialized."""
    event = SplicingEvent(
        event_id="E001",
        event_type="SE",
        gene_id="ENSG000001",
        gene_name="GENE1",
        chromosome="chr1",
        start=1000,
        end=2000,
        strand="+",
        placeholder=True
    )
    assert event.placeholder is True
    assert event.to_dict()["placeholder"] is True

    event2 = SplicingEvent.from_dict(event.to_dict())
    assert event2.placeholder is True