import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from code.data_models.rna_seq_sample import RNASeqSample
from code.data_models.splicing_event import SplicingEvent
from code.data_models.enrichment_result import EnrichmentResult
from code.data_models.phylogenetic_tree import PhylogeneticTree

def test_rna_seq_sample_creation():
    sample = RNASeqSample(
        accession_id="SRR123456",
        species="Homo_sapiens",
        fastq_path="/data/SRR123456.fastq.gz",
        replicate_group="rep1"
    )
    assert sample.accession_id == "SRR123456"
    assert sample.species == "Homo_sapiens"

def test_splicing_event_creation():
    event = SplicingEvent(
        event_id="SE_001",
        gene_id="GENE_X",
        delta_psi=0.15,
        fdr=0.03,
        flank_seq="ATCGATCG",
        phyloP_score=2.5,
        accelerated_flag=True
    )
    assert event.event_id == "SE_001"
    assert event.accelerated_flag is True

def test_enrichment_result_creation():
    result = EnrichmentResult(
        lineage="Human",
        odds_ratio=1.5,
        p_raw=0.04,
        p_corrected_phylo=0.06,
        p_fdr=0.05,
        p_empirical=0.045
    )
    assert result.lineage == "Human"
    assert result.odds_ratio == 1.5

def test_phylogenetic_tree_creation():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.nwk', delete=False) as f:
        f.write("(Human,Chimp);")
        temp_path = f.name

    try:
        tree = PhylogeneticTree(
            tree_file_path=temp_path,
            source="test_source"
        )
        assert tree.tree_file_path == temp_path
        assert tree.source == "test_source"
        assert tree.topology_hash is not None
    finally:
        import os
        os.unlink(temp_path)

def test_model_equality_and_hashing():
    # Test that distinct objects with same values are equal (dataclass default)
    s1 = RNASeqSample("A", "B", "C", "D")
    s2 = RNASeqSample("A", "B", "C", "D")
    assert s1 == s2

def test_placeholder_flag():
    # Verify that SplicingEvent handles the placeholder flag correctly
    event = SplicingEvent(
        event_id="SE_001",
        gene_id="GENE_X",
        delta_psi=0.15,
        fdr=0.03,
        flank_seq="ATCG",
        phyloP_score=2.5,
        accelerated_flag=False
    )
    # The flag is not explicitly in the constructor, but the attribute exists
    # We verify the attribute access works as defined in the model
    assert hasattr(event, 'accelerated_flag')
    assert event.accelerated_flag is False