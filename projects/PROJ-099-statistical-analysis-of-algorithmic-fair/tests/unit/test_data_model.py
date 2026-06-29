"""
Unit tests for the data model classes.

These tests verify that Dataset, Model, FairnessMetric, and
DatasetCharacteristic classes work correctly and maintain
data integrity.
"""

import pytest
from code.data_model import (
    Dataset,
    Model,
    FairnessMetric,
    DatasetCharacteristic,
)


class TestDatasetCharacteristic:
    """Tests for the DatasetCharacteristic class."""

    def test_creation_with_defaults(self):
        """Test that DatasetCharacteristic can be created with defaults."""
        char = DatasetCharacteristic(dataset_id="test_001")
        assert char.dataset_id == "test_001"
        assert char.base_rate_difference == 0.0
        assert char.class_imbalance_ratio == 1.0
        assert char.feature_dimensionality == 0
        assert char.protected_attribute_name == ""
        assert char.sample_size == 0

    def test_creation_with_values(self):
        """Test that DatasetCharacteristic stores provided values."""
        char = DatasetCharacteristic(
            dataset_id="adult_001",
            base_rate_difference=0.15,
            class_imbalance_ratio=2.5,
            feature_dimensionality=14,
            protected_attribute_name="gender",
            sample_size=32561,
        )
        assert char.dataset_id == "adult_001"
        assert char.base_rate_difference == 0.15
        assert char.class_imbalance_ratio == 2.5
        assert char.feature_dimensionality == 14
        assert char.protected_attribute_name == "gender"
        assert char.sample_size == 32561

    def test_class_imbalance_ratio_minimum(self):
        """Test that class_imbalance_ratio is clamped to minimum 1.0."""
        char = DatasetCharacteristic(
            dataset_id="test_001",
            class_imbalance_ratio=0.5,
        )
        assert char.class_imbalance_ratio == 1.0

    def test_to_dict(self):
        """Test conversion to dictionary."""
        char = DatasetCharacteristic(
            dataset_id="test_001",
            base_rate_difference=0.15,
        )
        d = char.to_dict()
        assert d["dataset_id"] == "test_001"
        assert d["base_rate_difference"] == 0.15

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "dataset_id": "test_001",
            "base_rate_difference": 0.15,
            "class_imbalance_ratio": 2.0,
            "feature_dimensionality": 10,
            "protected_attribute_name": "race",
            "sample_size": 1000,
        }
        char = DatasetCharacteristic.from_dict(data)
        assert char.dataset_id == "test_001"
        assert char.base_rate_difference == 0.15
        assert char.class_imbalance_ratio == 2.0

    def test_repr(self):
        """Test string representation."""
        char = DatasetCharacteristic(
            dataset_id="test_001",
            base_rate_difference=0.15,
            class_imbalance_ratio=2.0,
            feature_dimensionality=10,
            sample_size=1000,
        )
        repr_str = repr(char)
        assert "DatasetCharacteristic" in repr_str
        assert "test_001" in repr_str


class TestFairnessMetric:
    """Tests for the FairnessMetric class."""

    def test_creation_required_fields(self):
        """Test that FairnessMetric can be created with required fields."""
        metric = FairnessMetric(
            metric_name="demographic_parity_difference",
            metric_value=0.125,
            protected_attribute="gender",
            dataset_id="adult_001",
            model_id="lr_adult_001",
        )
        assert metric.metric_name == "demographic_parity_difference"
        assert metric.metric_value == 0.125
        assert metric.protected_attribute == "gender"
        assert metric.dataset_id == "adult_001"
        assert metric.model_id == "lr_adult_001"

    def test_creation_with_optional_fields(self):
        """Test that FairnessMetric stores optional fields."""
        metric = FairnessMetric(
            metric_name="demographic_parity_difference",
            metric_value=0.125,
            protected_attribute="gender",
            dataset_id="adult_001",
            model_id="lr_adult_001",
            formula=r"|P(Y=1|A=0) - P(Y=1|A=1)|",
            citation="Feldman et al., 2015",
            confidence_interval=(0.10, 0.15),
        )
        assert metric.formula == r"|P(Y=1|A=0) - P(Y=1|A=1)|"
        assert metric.citation == "Feldman et al., 2015"
        assert metric.confidence_interval == (0.10, 0.15)

    def test_invalid_metric_value_type(self):
        """Test that non-numeric metric_value raises TypeError."""
        with pytest.raises(TypeError):
            FairnessMetric(
                metric_name="test",
                metric_value="invalid",
                protected_attribute="gender",
                dataset_id="test",
                model_id="test",
            )

    def test_invalid_protected_attribute_type(self):
        """Test that non-string protected_attribute raises TypeError."""
        with pytest.raises(TypeError):
            FairnessMetric(
                metric_name="test",
                metric_value=0.1,
                protected_attribute=123,
                dataset_id="test",
                model_id="test",
            )

    def test_to_dict(self):
        """Test conversion to dictionary."""
        metric = FairnessMetric(
            metric_name="demographic_parity_difference",
            metric_value=0.125,
            protected_attribute="gender",
            dataset_id="adult_001",
            model_id="lr_adult_001",
            formula="test_formula",
            citation="test_citation",
        )
        d = metric.to_dict()
        assert d["metric_name"] == "demographic_parity_difference"
        assert d["metric_value"] == 0.125
        assert d["formula"] == "test_formula"

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "metric_name": "demographic_parity_difference",
            "metric_value": 0.125,
            "protected_attribute": "gender",
            "dataset_id": "adult_001",
            "model_id": "lr_adult_001",
            "formula": "test",
            "citation": "test",
            "confidence_interval": [0.10, 0.15],
        }
        metric = FairnessMetric.from_dict(data)
        assert metric.metric_name == "demographic_parity_difference"
        assert metric.confidence_interval == (0.10, 0.15)

    def test_repr(self):
        """Test string representation."""
        metric = FairnessMetric(
            metric_name="demographic_parity_difference",
            metric_value=0.125,
            protected_attribute="gender",
            dataset_id="adult_001",
            model_id="lr_adult_001",
            confidence_interval=(0.10, 0.15),
        )
        repr_str = repr(metric)
        assert "FairnessMetric" in repr_str
        assert "demographic_parity_difference" in repr_str


class TestModel:
    """Tests for the Model class."""

    def test_creation_required_fields(self):
        """Test that Model can be created with required fields."""
        model = Model(
            model_id="lr_adult_001",
            model_type="LogisticRegression",
            dataset_id="adult_001",
        )
        assert model.model_id == "lr_adult_001"
        assert model.model_type == "LogisticRegression"
        assert model.dataset_id == "adult_001"
        assert model.metrics == []
        assert model.parameters == {}
        assert model.trained is False

    def test_creation_with_values(self):
        """Test that Model stores provided values."""
        model = Model(
            model_id="rf_adult_001",
            model_type="RandomForest",
            dataset_id="adult_001",
            trained=True,
            path="data/processed/models/rf_adult_001.pkl",
            parameters={"n_estimators": 100, "max_depth": 10},
        )
        assert model.trained is True
        assert model.path == "data/processed/models/rf_adult_001.pkl"
        assert model.parameters["n_estimators"] == 100

    def test_add_metric(self):
        """Test adding metrics to a model."""
        model = Model(
            model_id="lr_adult_001",
            model_type="LogisticRegression",
            dataset_id="adult_001",
        )
        metric = FairnessMetric(
            metric_name="demographic_parity_difference",
            metric_value=0.125,
            protected_attribute="gender",
            dataset_id="adult_001",
            model_id="lr_adult_001",
        )
        model.add_metric(metric)
        assert len(model.metrics) == 1
        assert model.metrics[0] == metric

    def test_get_metrics_by_name(self):
        """Test filtering metrics by name."""
        model = Model(
            model_id="lr_adult_001",
            model_type="LogisticRegression",
            dataset_id="adult_001",
        )
        metric1 = FairnessMetric(
            metric_name="demographic_parity_difference",
            metric_value=0.125,
            protected_attribute="gender",
            dataset_id="adult_001",
            model_id="lr_adult_001",
        )
        metric2 = FairnessMetric(
            metric_name="equalized_odds_difference",
            metric_value=0.08,
            protected_attribute="gender",
            dataset_id="adult_001",
            model_id="lr_adult_001",
        )
        model.add_metric(metric1)
        model.add_metric(metric2)
        dp_metrics = model.get_metrics_by_name("demographic_parity_difference")
        assert len(dp_metrics) == 1
        assert dp_metrics[0] == metric1

    def test_to_dict(self):
        """Test conversion to dictionary."""
        model = Model(
            model_id="lr_adult_001",
            model_type="LogisticRegression",
            dataset_id="adult_001",
            trained=True,
        )
        model.add_metric(
            FairnessMetric(
                metric_name="demographic_parity_difference",
                metric_value=0.125,
                protected_attribute="gender",
                dataset_id="adult_001",
                model_id="lr_adult_001",
            )
        )
        d = model.to_dict()
        assert d["model_id"] == "lr_adult_001"
        assert d["model_type"] == "LogisticRegression"
        assert len(d["metrics"]) == 1

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "model_id": "lr_adult_001",
            "model_type": "LogisticRegression",
            "dataset_id": "adult_001",
            "trained": True,
            "metrics": [
                {
                    "metric_name": "demographic_parity_difference",
                    "metric_value": 0.125,
                    "protected_attribute": "gender",
                    "dataset_id": "adult_001",
                    "model_id": "lr_adult_001",
                }
            ],
        }
        model = Model.from_dict(data)
        assert model.model_id == "lr_adult_001"
        assert len(model.metrics) == 1

    def test_repr(self):
        """Test string representation."""
        model = Model(
            model_id="lr_adult_001",
            model_type="LogisticRegression",
            dataset_id="adult_001",
        )
        repr_str = repr(model)
        assert "Model" in repr_str
        assert "lr_adult_001" in repr_str
        assert "LogisticRegression" in repr_str


class TestDataset:
    """Tests for the Dataset class."""

    def test_creation_required_fields(self):
        """Test that Dataset can be created with required fields."""
        dataset = Dataset(
            dataset_id="adult_001",
            name="UCI Adult",
        )
        assert dataset.dataset_id == "adult_001"
        assert dataset.name == "UCI Adult"
        assert dataset.raw_path is None
        assert dataset.checksum is None

    def test_creation_with_values(self):
        """Test that Dataset stores provided values."""
        dataset = Dataset(
            dataset_id="adult_001",
            name="UCI Adult",
            raw_path="data/raw/adult.csv",
            processed_path="data/processed/adult_processed.csv",
            protected_attribute="gender",
            outcome="income",
            predictions="income_pred",
            checksum="a" * 64,
            sample_size=32561,
        )
        assert dataset.raw_path == "data/raw/adult.csv"
        assert dataset.protected_attribute == "gender"
        assert dataset.sample_size == 32561

    def test_invalid_checksum_format(self):
        """Test that invalid checksum format raises ValueError."""
        with pytest.raises(ValueError):
            Dataset(
                dataset_id="test_001",
                name="Test",
                checksum="invalid",
            )

    def test_valid_checksum_format(self):
        """Test that valid checksum format is accepted."""
        dataset = Dataset(
            dataset_id="test_001",
            name="Test",
            checksum="a" * 64,
        )
        assert dataset.checksum == "a" * 64

    def test_set_characteristics(self):
        """Test setting dataset characteristics."""
        dataset = Dataset(
            dataset_id="adult_001",
            name="UCI Adult",
            protected_attribute="gender",
            sample_size=32561,
        )
        dataset.set_characteristics(
            base_rate_difference=0.15,
            class_imbalance_ratio=2.5,
            feature_dimensionality=14,
        )
        assert dataset.characteristics is not None
        assert dataset.characteristics.base_rate_difference == 0.15
        assert dataset.characteristics.class_imbalance_ratio == 2.5
        assert dataset.characteristics.feature_dimensionality == 14

    def test_to_dict(self):
        """Test conversion to dictionary."""
        dataset = Dataset(
            dataset_id="adult_001",
            name="UCI Adult",
            raw_path="data/raw/adult.csv",
            protected_attribute="gender",
            sample_size=32561,
        )
        dataset.set_characteristics(base_rate_difference=0.15)
        d = dataset.to_dict()
        assert d["dataset_id"] == "adult_001"
        assert d["name"] == "UCI Adult"
        assert "characteristics" in d

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "dataset_id": "adult_001",
            "name": "UCI Adult",
            "raw_path": "data/raw/adult.csv",
            "protected_attribute": "gender",
            "sample_size": 32561,
            "characteristics": {
                "dataset_id": "adult_001",
                "base_rate_difference": 0.15,
                "class_imbalance_ratio": 2.5,
                "feature_dimensionality": 14,
                "protected_attribute_name": "gender",
                "sample_size": 32561,
            },
        }
        dataset = Dataset.from_dict(data)
        assert dataset.dataset_id == "adult_001"
        assert dataset.characteristics is not None
        assert dataset.characteristics.base_rate_difference == 0.15

    def test_repr(self):
        """Test string representation."""
        dataset = Dataset(
            dataset_id="adult_001",
            name="UCI Adult",
            sample_size=32561,
        )
        repr_str = repr(dataset)
        assert "Dataset" in repr_str
        assert "adult_001" in repr_str
        assert "UCI Adult" in repr_str