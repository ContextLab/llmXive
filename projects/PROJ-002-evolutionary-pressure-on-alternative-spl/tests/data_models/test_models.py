import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import json
from code.data_models.models import RNASeqSample, SplicingEvent, EnrichmentResult, PhylogeneticTree, Species

class TestRNASeqSample:
    def test_create_sample(self):
        sample = RNASeqSample(
            sample_id="S001",
            species=Species.HUMAN,
            sra_accession="SRP010775"
        )
        assert sample.sample_id == "S001"
        assert sample.species == Species.HUMAN
        assert sample.sra_accession == "SRP010775"
        assert sample.alignment_status == "pending"

    def test_to_dict(self):
        sample = RNASeqSample(
            sample_id="S001",
            species=Species.HUMAN,
            sra_accession="SRP010775",
            read_count=1000000
        )
        d = sample.to_dict()
        assert d["sample_id"] == "S001"
        assert d["species"] == "human"
        assert d["read_count"] == 1000000

    def test_round_trip_json(self):
        sample = RNASeqSample(
            sample_id="S001",
            species=Species.CHIMP,
            sra_accession="SRP009050"
        )
        json_str = sample.to_json()
        restored = RNASeqSample.from_dict(json.loads(json_str))
        assert restored.sample_id == sample.sample_id
        assert restored.species == sample.species

class TestSplicingEvent:
    def test_create_event(self):
        event = SplicingEvent(
            event_id="E001",
            gene_id="ENSG000001",
            gene_name="BRCA1",
            event_type="SE",
            chromosome="chr17",
            start=1000,
            end=2000,
            strand="+"
        )
        assert event.event_type == "SE"
        assert event.is_lineage_specific is False

    def test_set_psi_values(self):
        event = SplicingEvent(
            event_id="E001",
            gene_id="ENSG000001",
            gene_name="BRCA1",
            event_type="SE",
            chromosome="chr17",
            start=1000,
            end=2000,
            strand="+"
        )
        event.psi_values[Species.HUMAN] = 0.85
        event.psi_values[Species.CHIMP] = 0.45
        assert event.psi_values[Species.HUMAN] == 0.85
        assert event.psi_values[Species.CHIMP] == 0.45

    def test_lineage_specific_detection(self):
        event = SplicingEvent(
            event_id="E001",
            gene_id="ENSG000001",
            gene_name="BRCA1",
            event_type="SE",
            chromosome="chr17",
            start=1000,
            end=2000,
            strand="+"
        )
        event.is_lineage_specific = True
        event.lineage_species = Species.HUMAN
        event.delta_psi = 0.40
        assert event.is_lineage_specific is True
        assert event.lineage_species == Species.HUMAN

class TestEnrichmentResult:
    def test_create_result(self):
        result = EnrichmentResult(
            lineage=Species.HUMAN,
            regression_method="phyloglm",
            coefficient=1.2,
            std_error=0.3,
            z_score=4.0,
            p_value=0.0001,
            fdr_adjusted_pvalue=0.001,
            odds_ratio=3.5,
            sample_size=50,
            control_size=100
        )
        assert result.odds_ratio == 3.5
        assert result.lineage == Species.HUMAN

    def test_to_dict(self):
        result = EnrichmentResult(
            lineage=Species.CHIMP,
            regression_method="phyloglm",
            coefficient=0.5,
            std_error=0.1,
            z_score=5.0,
            p_value=0.00001,
            fdr_adjusted_pvalue=0.0001,
            odds_ratio=1.65,
            sample_size=30,
            control_size=60
        )
        d = result.to_dict()
        assert d["lineage"] == "chimp"
        assert d["odds_ratio"] == 1.65
        assert "timestamp" in d

class TestPhylogeneticTree:
    def test_create_tree(self):
        newick = "((human:1, chimp:1):2, (macaque:1.5, marmoset:1.5):1.5);"
        tree = PhylogeneticTree(
            name="primate_tree",
            newick_string=newick,
            taxa=["human", "chimp", "macaque", "marmoset"]
        )
        assert tree.name == "primate_tree"
        assert len(tree.taxa) == 4

    def test_to_nwk_file(self):
        newick = "((human:1, chimp:1):2, macaque:3);"
        tree = PhylogeneticTree(
            name="test_tree",
            newick_string=newick,
            taxa=["human", "chimp", "macaque"]
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.nwk"
            tree.to_nwk_file(path)
            assert path.exists()
            with open(path, 'r') as f:
                content = f.read()
            assert newick in content

    def test_from_newick_file(self):
        newick = "((human:1, chimp:1):2, macaque:3);"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.nwk"
            with open(path, 'w') as f:
                f.write(newick)
            
            tree = PhylogeneticTree.from_newick_file(path, name="loaded_tree")
            assert tree.name == "loaded_tree"
            assert tree.newick_string == newick
            assert "human" in tree.taxa
            assert "chimp" in tree.taxa
            assert "macaque" in tree.taxa