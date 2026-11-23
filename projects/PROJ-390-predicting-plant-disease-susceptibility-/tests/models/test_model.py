"""
Tests for the Model data model.
"""
import pytest
from src.models.model import Model


class TestModelCreation:
    def test_create_model(self):
        """Test creation of a valid Model instance."""
        model = Model(
            model_id="RF_001",
            model_type="RandomForest",
            hyperparameters={"n_estimators": 100, "max_depth": 10},
            training_date="2023-10-01T12:00:00",
            metrics={"auc": 0.85, "accuracy": 0.82}
        )
        assert model.model_id == "RF_001"
        assert model.model_type == "RandomForest"
        assert model.metrics["auc"] == 0.85

    def test_auto_set_training_date(self):
        """Test that training_date is auto-generated if missing."""
        model = Model(
            model_id="SVM_001",
            model_type="SVM",
            hyperparameters={"C": 1.0},
            training_date="",  # Empty
            metrics={"auc": 0.75}
        )
        assert model.training_date != ""

    def test_invalid_model_id(self):
        """Test that empty model_id raises error."""
        with pytest.raises(ValueError):
            Model(
                model_id="",
                model_type="RandomForest",
                hyperparameters={},
                training_date="2023-01-01",
                metrics={}
            )


class TestModelMethods:
    def test_to_dict(self):
        """Test dictionary serialization."""
        model = Model(
            model_id="RF_002",
            model_type="RandomForest",
            hyperparameters={"n": 50},
            training_date="2023-01-01",
            metrics={"acc": 0.9}
        )
        d = model.to_dict()
        assert d["model_id"] == "RF_002"
        assert "metrics" in d

    def test_add_metric(self):
        """Test adding a metric."""
        model = Model(
            model_id="RF_003",
            model_type="RandomForest",
            hyperparameters={},
            training_date="2023-01-01",
            metrics={}
        )
        model.add_metric("f1", 0.88)
        assert model.metrics["f1"] == 0.88

    def test_add_feature_importance(self):
        """Test adding feature importance."""
        model = Model(
            model_id="RF_004",
            model_type="RandomForest",
            hyperparameters={},
            training_date="2023-01-01",
            metrics={}
        )
        model.add_feature_importance("feature_A", 0.45)
        assert len(model.feature_importance) == 1
        assert model.feature_importance[0]["feature_name"] == "feature_A"

    def test_to_json(self):
        """Test JSON serialization."""
        model = Model(
            model_id="RF_005",
            model_type="RandomForest",
            hyperparameters={},
            training_date="2023-01-01",
            metrics={"auc": 0.9}
        )
        json_str = model.to_json()
        assert "RF_005" in json_str
        assert "auc" in json_str
