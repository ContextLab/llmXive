"""
Tests for the base data models in code/ingestion/models.py.
"""
import pytest
from datetime import datetime
from code.ingestion.models import MoleculeRecord, ModelMetrics, FeatureImportance


class TestMoleculeRecord:
    def test_creation(self):
        """Test basic creation of a MoleculeRecord."""
        record = MoleculeRecord(
            smiles="CCO",
            space_group="P2_1/c",
            lattice_a=5.0,
            lattice_b=5.0,
            lattice_c=5.0,
            alpha=90.0,
            beta=90.0,
            gamma=90.0,
            molecular_weight=46.07,
            fingerprint_bits=[1, 5, 12, 99],
            source_id="COD-12345"
        )
        assert record.smiles == "CCO"
        assert record.space_group == "P2_1/c"
        assert len(record.fingerprint_bits) == 4
        assert isinstance(record.processed_at, datetime)

    def test_to_dict(self):
        """Test serialization to dictionary."""
        record = MoleculeRecord(
            smiles="C",
            space_group="Fm-3m",
            lattice_a=3.5,
            lattice_b=3.5,
            lattice_c=3.5,
            alpha=90.0,
            beta=90.0,
            gamma=90.0,
            molecular_weight=12.01,
            fingerprint_bits=[0],
            source_id="COD-999"
        )
        d = record.to_dict()
        assert d["smiles"] == "C"
        assert d["source_id"] == "COD-999"
        assert "processed_at" in d

    def test_from_dict_round_trip(self):
        """Test deserialization from dictionary."""
        original = MoleculeRecord(
            smiles="CC(=O)O",
            space_group="P2_1",
            lattice_a=4.0,
            lattice_b=4.0,
            lattice_c=4.0,
            alpha=90.0,
            beta=90.0,
            gamma=90.0,
            molecular_weight=60.05,
            fingerprint_bits=[10, 20],
            source_id="COD-555"
        )
        data = original.to_dict()
        reconstructed = MoleculeRecord.from_dict(data)
        assert reconstructed.smiles == original.smiles
        assert reconstructed.source_id == original.source_id
        assert reconstructed.fingerprint_bits == original.fingerprint_bits


class TestModelMetrics:
    def test_classification_metrics(self):
        """Test creation of classification metrics."""
        metrics = ModelMetrics(
            model_name="RandomForest",
            metric_type="classification",
            accuracy=0.85,
            macro_f1=0.82,
            train_size=800,
            test_size=200
        )
        assert metrics.accuracy == 0.85
        assert metrics.r_squared is None  # Not applicable for classification

    def test_regression_metrics(self):
        """Test creation of regression metrics."""
        metrics = ModelMetrics(
            model_name="Ridge",
            metric_type="regression",
            r_squared=0.92,
            mae=1.5,
            train_size=500,
            test_size=100
        )
        assert metrics.r_squared == 0.92
        assert metrics.accuracy is None  # Not applicable for regression

    def test_to_json(self):
        """Test JSON serialization."""
        metrics = ModelMetrics(
            model_name="GBM",
            metric_type="classification",
            accuracy=0.90,
            macro_f1=0.88,
            train_size=1000,
            test_size=250,
            metadata={"n_estimators": 100}
        )
        json_str = metrics.to_json()
        assert "GBM" in json_str
        assert "0.90" in json_str
        assert "n_estimators" in json_str


class TestFeatureImportance:
    def test_basic_creation(self):
        """Test basic creation of a FeatureImportance record."""
        feat = FeatureImportance(
            feature_id=123,
            importance_score=0.45,
            method="permutation",
            rank=1
        )
        assert feat.feature_id == 123
        assert feat.importance_score == 0.45
        assert feat.collision_flag is False

    def test_collision_flag(self):
        """Test setting collision flag."""
        feat = FeatureImportance(
            feature_id=456,
            importance_score=0.30,
            method="shap",
            substructure="c1ccccc1",
            collision_flag=True,
            rank=5
        )
        assert feat.collision_flag is True
        assert feat.substructure == "c1ccccc1"

    def test_to_dict(self):
        """Test dictionary serialization."""
        feat = FeatureImportance(
            feature_id=789,
            importance_score=0.12,
            method="permutation",
            rank=10
        )
        d = feat.to_dict()
        assert d["feature_id"] == 789
        assert d["rank"] == 10
        assert d["collision_flag"] is False