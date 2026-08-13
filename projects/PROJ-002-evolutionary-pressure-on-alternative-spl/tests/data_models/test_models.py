"""
Unit tests for the data models module.

Tests verify that data models correctly handle:
- Creation and validation
- Serialization/deserialization
- Edge cases
- Data integrity
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
import numpy as np

from code.data_models.models import RNASeqSample, SplicingEvent, EnrichmentResult, PhylogeneticTree


class TestRNASeqSample:
    """Tests for RNASeqSample data model."""
    
    def test_create_sample(self):
        """Test basic sample creation."""
        sample = RNASeqSample(
            sample_id="SAMPLE001",
            species="Homo_sapiens",
            assembly="GRCh38",
            sra_accession="SRX123456"
        )
        assert sample.sample_id == "SAMPLE001"
        assert sample.species == "Homo_sapiens"
        assert sample.replicate_index == 1
        assert sample.validate() is True
    
    def test_sample_to_dict(self):
        """Test sample dictionary conversion."""
        sample = RNASeqSample(
            sample_id="SAMPLE001",
            species="Homo_sapiens",
            assembly="GRCh38"
        )
        sample.total_reads = 1000000
        sample.mapped_reads = 950000
        sample.mapping_rate = 0.95
        
        d = sample.to_dict()
        assert d['sample_id'] == "SAMPLE001"
        assert d['total_reads'] == 1000000
        assert d['mapping_rate'] == 0.95
        assert 'created_at' in d
    
    def test_sample_serialization(self):
        """Test JSON serialization and deserialization."""
        sample = RNASeqSample(
            sample_id="SAMPLE001",
            species="Homo_sapiens",
            assembly="GRCh38"
        )
        json_str = sample.to_json()
        restored = RNASeqSample.from_json(json_str)
        
        assert restored.sample_id == sample.sample_id
        assert restored.species == sample.species
        assert restored.created_at == sample.created_at
    
    def test_sample_validation_failure(self):
        """Test sample validation with invalid data."""
        sample = RNASeqSample(
            sample_id="",
            species="Homo_sapiens",
            assembly="GRCh38"
        )
        assert sample.validate() is False
    
    def test_sample_validation_replicate_index(self):
        """Test sample validation with invalid replicate index."""
        sample = RNASeqSample(
            sample_id="SAMPLE001",
            species="Homo_sapiens",
            assembly="GRCh38",
            replicate_index=0
        )
        assert sample.validate() is False
    
    def test_sample_from_dict(self):
        """Test creating sample from dictionary."""
        data = {
            'sample_id': 'SAMPLE001',
            'species': 'Homo_sapiens',
            'assembly': 'GRCh38',
            'replicate_index': 2,
            'total_reads': 500000
        }
        sample = RNASeqSample.from_dict(data)
        assert sample.sample_id == 'SAMPLE001'
        assert sample.replicate_index == 2
        assert sample.total_reads == 500000

class TestSplicingEvent:
    """Tests for SplicingEvent data model."""
    
    def test_create_event(self):
        """Test basic event creation."""
        event = SplicingEvent(
            event_id="SE001",
            event_type="SE",
            gene_id="ENSG000001",
            gene_name="GENE1",
            chromosome="chr1",
            start=1000,
            end=2000,
            strand="+"
        )
        assert event.event_id == "SE001"
        assert event.event_type == "SE"
        assert event.validate() is True
    
    def test_event_psi_values(self):
        """Test PSI value handling."""
        event = SplicingEvent(
            event_id="SE001",
            event_type="SE",
            gene_id="ENSG000001",
            gene_name="GENE1",
            chromosome="chr1",
            start=1000,
            end=2000,
            strand="+",
            psi_values={"sample1": 0.5, "sample2": 0.7}
        )
        assert event.psi_values["sample1"] == 0.5
        assert event.psi_values["sample2"] == 0.7
    
    def test_calculate_delta_psi(self):
        """Test delta PSI calculation."""
        event = SplicingEvent(
            event_id="SE001",
            event_type="SE",
            gene_id="ENSG000001",
            gene_name="GENE1",
            chromosome="chr1",
            start=1000,
            end=2000,
            strand="+",
            psi_values={
                "human1": 0.8, "human2": 0.9,
                "chimp1": 0.3, "chimp2": 0.4
            }
        )
        delta = event.calculate_delta_psi(
            group1_samples=["human1", "human2"],
            group2_samples=["chimp1", "chimp2"]
        )
        # (0.8 + 0.9)/2 - (0.3 + 0.4)/2 = 0.85 - 0.35 = 0.5
        assert abs(delta - 0.5) < 1e-6
    
    def test_event_to_bed(self):
        """Test BED format conversion."""
        event = SplicingEvent(
            event_id="SE001",
            event_type="SE",
            gene_id="ENSG000001",
            gene_name="GENE1",
            chromosome="chr1",
            start=1001,
            end=2000,
            strand="+"
        )
        bed = event.to_bed()
        # BED is 0-based, so start should be 1000
        parts = bed.split('\t')
        assert parts[0] == "chr1"
        assert parts[1] == "1000"  # 0-based
        assert parts[2] == "2000"
        assert parts[3] == "SE001"
        assert parts[5] == "+"
    
    def test_event_validation_invalid_psi(self):
        """Test event validation with invalid PSI values."""
        event = SplicingEvent(
            event_id="SE001",
            event_type="SE",
            gene_id="ENSG000001",
            gene_name="GENE1",
            chromosome="chr1",
            start=1000,
            end=2000,
            strand="+",
            psi_values={"sample1": 1.5}  # Invalid: > 1.0
        )
        assert event.validate() is False
    
    def test_event_serialization(self):
        """Test event JSON serialization."""
        event = SplicingEvent(
            event_id="SE001",
            event_type="SE",
            gene_id="ENSG000001",
            gene_name="GENE1",
            chromosome="chr1",
            start=1000,
            end=2000,
            strand="+",
            psi_values={"sample1": 0.5},
            delta_psi=0.2,
            p_value=0.01,
            fdr=0.03,
            is_lineage_specific=True,
            lineage="human"
        )
        json_str = event.to_json()
        restored = SplicingEvent.from_json(json_str)
        
        assert restored.event_id == event.event_id
        assert restored.is_lineage_specific == event.is_lineage_specific
        assert restored.lineage == event.lineage
    
    def test_event_hash_and_equality(self):
        """Test event hashing and equality."""
        event1 = SplicingEvent(
            event_id="SE001",
            event_type="SE",
            gene_id="ENSG000001",
            gene_name="GENE1",
            chromosome="chr1",
            start=1000,
            end=2000,
            strand="+"
        )
        event2 = SplicingEvent(
            event_id="SE001",
            event_type="A5SS",  # Different type
            gene_id="ENSG000002",
            gene_name="GENE2",
            chromosome="chr2",
            start=1000,
            end=2000,
            strand="+"
        )
        event3 = SplicingEvent(
            event_id="SE002",
            event_type="SE",
            gene_id="ENSG000001",
            gene_name="GENE1",
            chromosome="chr1",
            start=1000,
            end=2000,
            strand="+"
        )
        
        assert event1 == event2  # Same event_id
        assert event1 != event3  # Different event_id
        assert hash(event1) == hash(event2)

class TestEnrichmentResult:
    """Tests for EnrichmentResult data model."""
    
    def test_create_result(self):
        """Test basic result creation."""
        result = EnrichmentResult(
            lineage="human",
            test_type="phylogenetic_logistic_regression",
            total_events=1000,
            accelerated_events=150,
            control_events=850,
            odds_ratio=2.5,
            p_value=0.001,
            fdr=0.005
        )
        assert result.lineage == "human"
        assert result.odds_ratio == 2.5
        assert result.is_significant() is True
    
    def test_result_significance(self):
        """Test significance checking at different alpha levels."""
        result = EnrichmentResult(
            lineage="human",
            test_type="test",
            total_events=100,
            accelerated_events=10,
            control_events=90,
            p_value=0.03,
            fdr=0.05
        )
        assert result.is_significant(alpha=0.05) is True
        assert result.is_significant(alpha=0.01) is False
    
    def test_result_serialization(self):
        """Test result JSON serialization."""
        result = EnrichmentResult(
            lineage="chimp",
            test_type="permutation",
            total_events=500,
            accelerated_events=75,
            control_events=425,
            odds_ratio=1.8,
            p_value=0.02,
            fdr=0.04,
            confidence_interval=(1.2, 2.5)
        )
        json_str = result.to_json()
        restored = EnrichmentResult.from_json(json_str)
        
        assert restored.lineage == result.lineage
        assert restored.confidence_interval == result.confidence_interval
    
    def test_result_to_dataframe_row(self):
        """Test conversion to DataFrame row format."""
        result = EnrichmentResult(
            lineage="human",
            test_type="test",
            total_events=100,
            accelerated_events=10,
            control_events=90,
            confidence_interval=(1.5, 3.5)
        )
        row = result.to_dataframe_row()
        assert 'ci_lower' in row
        assert 'ci_upper' in row
        assert row['ci_lower'] == 1.5
        assert row['ci_upper'] == 3.5

class TestPhylogeneticTree:
    """Tests for PhylogeneticTree data model."""
    
    def test_create_tree(self):
        """Test basic tree creation."""
        newick = "((Human:0.1,Chimp:0.1):0.2,Macaque:0.3);"
        tree = PhylogeneticTree(
            tree_id="primate_tree",
            newick_string=newick,
            species=["Human", "Chimp", "Macaque"]
        )
        assert tree.tree_id == "primate_tree"
        assert tree.get_species_count() == 3
        assert tree.validate() is True
    
    def test_tree_validation_balanced_parens(self):
        """Test tree validation with unbalanced parentheses."""
        # Missing closing paren
        invalid_newick = "((Human:0.1,Chimp:0.1):0.2,Macaque:0.3"
        tree = PhylogeneticTree(
            tree_id="invalid_tree",
            newick_string=invalid_newick
        )
        assert tree.validate() is False
    
    def test_tree_serialization(self):
        """Test tree JSON serialization."""
        newick = "((Human:0.1,Chimp:0.1):0.2,Macaque:0.3)"
        tree = PhylogeneticTree(
            tree_id="test_tree",
            newick_string=newick,
            species=["Human", "Chimp", "Macaque"],
            metadata={"source": "test"}
        )
        json_str = tree.to_json()
        restored = PhylogeneticTree.from_json(json_str)
        
        assert restored.tree_id == tree.tree_id
        assert restored.newick_string == tree.newick_string
        assert restored.metadata == tree.metadata
    
    def test_tree_nwk_file_io(self):
        """Test Newick file read/write."""
        newick = "((Human:0.1,Chimp:0.1):0.2,Macaque:0.3)"
        tree = PhylogeneticTree(
            tree_id="file_tree",
            newick_string=newick,
            species=["Human", "Chimp", "Macaque"]
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.nwk', delete=False) as f:
            temp_path = f.name
        
        try:
            tree.to_nwk_file(temp_path)
            loaded_tree = PhylogeneticTree.from_nwk_file(temp_path, tree_id="loaded")
            
            assert loaded_tree.newick_string == newick
        finally:
            Path(temp_path).unlink()
    
    def test_tree_hash_and_equality(self):
        """Test tree hashing and equality."""
        newick = "((Human:0.1,Chimp:0.1):0.2,Macaque:0.3)"
        tree1 = PhylogeneticTree(
            tree_id="tree1",
            newick_string=newick,
            species=["Human", "Chimp", "Macaque"]
        )
        tree2 = PhylogeneticTree(
            tree_id="tree2",
            newick_string=newick,
            species=["Human", "Chimp", "Macaque"]
        )
        tree3 = PhylogeneticTree(
            tree_id="tree1",
            newick_string="((Human:0.2,Chimp:0.2):0.3,Macaque:0.4)",
            species=["Human", "Chimp", "Macaque"]
        )
        
        assert tree1 != tree2  # Different tree_id
        assert tree1 != tree3  # Different newick_string
        assert hash(tree1) != hash(tree2)