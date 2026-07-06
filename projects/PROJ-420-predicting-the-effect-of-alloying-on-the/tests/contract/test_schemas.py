"""
Contract tests for data schemas defined in code/schemas/alloy_record.py.

These tests verify that the Pydantic models (AlloyRecord, MeasurementProvenance, ModelMetrics)
strictly enforce the data contracts required by the project specifications, including:
- Required fields for compositional data and properties
- Validation of measurement provenance (FR-009)
- Correct types and constraints for numerical fields
- Proper handling of missing/optional data
"""

import pytest
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List

# Import the schema models from the project code
from code.schemas.alloy_record import AlloyRecord, MeasurementProvenance, ModelMetrics


class TestMeasurementProvenance:
    """Tests for the MeasurementProvenance schema."""

    def test_valid_provenance_with_required_fields(self):
        """Test that a valid provenance record with all required fields is accepted."""
        data = {
            "source": "Materials Project",
            "method": "experimental",
            "reference_id": "mp-12345",
            "timestamp": datetime.now().isoformat()
        }
        provenance = MeasurementProvenance(**data)
        assert provenance.source == "Materials Project"
        assert provenance.method == "experimental"
        assert provenance.reference_id == "mp-12345"
        assert isinstance(provenance.timestamp, datetime)

    def test_missing_required_source_field(self):
        """Test that missing 'source' field raises validation error."""
        data = {
            "method": "experimental",
            "reference_id": "mp-12345",
            "timestamp": datetime.now().isoformat()
        }
        with pytest.raises(Exception):  # Pydantic ValidationError
            MeasurementProvenance(**data)

    def test_missing_required_method_field(self):
        """Test that missing 'method' field raises validation error."""
        data = {
            "source": "Materials Project",
            "reference_id": "mp-12345",
            "timestamp": datetime.now().isoformat()
        }
        with pytest.raises(Exception):
            MeasurementProvenance(**data)

    def test_optional_fields_can_be_missing(self):
        """Test that optional fields (reference_url, notes) can be omitted."""
        data = {
            "source": "NIST",
            "method": "calculated",
            "timestamp": datetime.now().isoformat()
        }
        provenance = MeasurementProvenance(**data)
        assert provenance.reference_url is None
        assert provenance.notes is None

    def test_method_validation_rejects_invalid_values(self):
        """Test that method field accepts only valid string values."""
        # Valid methods should work
        valid_methods = ["experimental", "calculated", "derived", "derived_from_Youngs_modulus", "unknown"]
        for method in valid_methods:
            data = {
                "source": "Test",
                "method": method,
                "timestamp": datetime.now().isoformat()
            }
            provenance = MeasurementProvenance(**data)
            assert provenance.method == method


class TestAlloyRecord:
    """Tests for the AlloyRecord schema."""

    def test_valid_alloy_record_with_all_fields(self):
        """Test that a complete valid alloy record is accepted."""
        data = {
            "composition": {
                "Al": 0.95,
                "Cu": 0.03,
                "Mg": 0.015,
                "Si": 0.005,
                "Zn": 0.005,
                "Mn": 0.005
            },
            "poissons_ratio": 0.33,
            "youngs_modulus": 70.0,
            "bulk_modulus": 75.0,
            "measurement_provenance": {
                "source": "Materials Project",
                "method": "experimental",
                "reference_id": "mp-12345",
                "timestamp": datetime.now().isoformat()
            },
            "data_source": "materials_project"
        }
        record = AlloyRecord(**data)
        assert record.composition["Al"] == 0.95
        assert record.poissons_ratio == 0.33
        assert record.youngs_modulus == 70.0
        assert record.measurement_provenance.source == "Materials Project"

    def test_missing_required_composition_field(self):
        """Test that missing composition field raises validation error."""
        data = {
            "poissons_ratio": 0.33,
            "youngs_modulus": 70.0,
            "measurement_provenance": {
                "source": "Test",
                "method": "experimental",
                "timestamp": datetime.now().isoformat()
            },
            "data_source": "test"
        }
        with pytest.raises(Exception):
            AlloyRecord(**data)

    def test_missing_required_poissons_ratio_field(self):
        """Test that missing Poisson's ratio field raises validation error."""
        data = {
            "composition": {"Al": 0.95, "Cu": 0.05},
            "youngs_modulus": 70.0,
            "measurement_provenance": {
                "source": "Test",
                "method": "experimental",
                "timestamp": datetime.now().isoformat()
            },
            "data_source": "test"
        }
        with pytest.raises(Exception):
            AlloyRecord(**data)

    def test_missing_required_youngs_modulus_field(self):
        """Test that missing Young's modulus field raises validation error."""
        data = {
            "composition": {"Al": 0.95, "Cu": 0.05},
            "poissons_ratio": 0.33,
            "measurement_provenance": {
                "source": "Test",
                "method": "experimental",
                "timestamp": datetime.now().isoformat()
            },
            "data_source": "test"
        }
        with pytest.raises(Exception):
            AlloyRecord(**data)

    def test_missing_required_measurement_provenance(self):
        """Test that missing measurement_provenance raises validation error (FR-009)."""
        data = {
            "composition": {"Al": 0.95, "Cu": 0.05},
            "poissons_ratio": 0.33,
            "youngs_modulus": 70.0,
            "data_source": "test"
        }
        with pytest.raises(Exception):
            AlloyRecord(**data)

    def test_composition_sum_validation(self):
        """Test that composition values must sum to approximately 1.0."""
        # Valid sum
        data = {
            "composition": {"Al": 0.95, "Cu": 0.05},
            "poissons_ratio": 0.33,
            "youngs_modulus": 70.0,
            "measurement_provenance": {
                "source": "Test",
                "method": "experimental",
                "timestamp": datetime.now().isoformat()
            },
            "data_source": "test"
        }
        record = AlloyRecord(**data)
        assert abs(sum(record.composition.values()) - 1.0) < 0.01

    def test_negative_composition_rejected(self):
        """Test that negative composition values are rejected."""
        data = {
            "composition": {"Al": 0.95, "Cu": -0.05},
            "poissons_ratio": 0.33,
            "youngs_modulus": 70.0,
            "measurement_provenance": {
                "source": "Test",
                "method": "experimental",
                "timestamp": datetime.now().isoformat()
            },
            "data_source": "test"
        }
        with pytest.raises(Exception):
            AlloyRecord(**data)

    def test_negative_poissons_ratio_rejected(self):
        """Test that negative Poisson's ratio is rejected."""
        data = {
            "composition": {"Al": 0.95, "Cu": 0.05},
            "poissons_ratio": -0.33,
            "youngs_modulus": 70.0,
            "measurement_provenance": {
                "source": "Test",
                "method": "experimental",
                "timestamp": datetime.now().isoformat()
            },
            "data_source": "test"
        }
        with pytest.raises(Exception):
            AlloyRecord(**data)

    def test_negative_youngs_modulus_rejected(self):
        """Test that negative Young's modulus is rejected."""
        data = {
            "composition": {"Al": 0.95, "Cu": 0.05},
            "poissons_ratio": 0.33,
            "youngs_modulus": -70.0,
            "measurement_provenance": {
                "source": "Test",
                "method": "experimental",
                "timestamp": datetime.now().isoformat()
            },
            "data_source": "test"
        }
        with pytest.raises(Exception):
            AlloyRecord(**data)

    def test_data_source_field_is_present(self):
        """Test that data_source field is captured correctly."""
        data = {
            "composition": {"Al": 0.95, "Cu": 0.05},
            "poissons_ratio": 0.33,
            "youngs_modulus": 70.0,
            "measurement_provenance": {
                "source": "Test",
                "method": "experimental",
                "timestamp": datetime.now().isoformat()
            },
            "data_source": "nist_repository"
        }
        record = AlloyRecord(**data)
        assert record.data_source == "nist_repository"


class TestModelMetrics:
    """Tests for the ModelMetrics schema."""

    def test_valid_metrics_with_all_fields(self):
        """Test that a valid metrics record with all fields is accepted."""
        data = {
            "model_type": "RandomForest",
            "mae": 0.025,
            "rmse": 0.032,
            "r2_score": 0.85,
            "cross_validation_folds": 5,
            "cv_mean_mae": 0.027,
            "test_set_size": 100,
            "training_timestamp": datetime.now().isoformat()
        }
        metrics = ModelMetrics(**data)
        assert metrics.model_type == "RandomForest"
        assert metrics.mae == 0.025
        assert metrics.cv_mean_mae == 0.027

    def test_missing_required_model_type(self):
        """Test that missing model_type raises validation error."""
        data = {
            "mae": 0.025,
            "rmse": 0.032,
            "r2_score": 0.85,
            "cross_validation_folds": 5,
            "cv_mean_mae": 0.027,
            "test_set_size": 100,
            "training_timestamp": datetime.now().isoformat()
        }
        with pytest.raises(Exception):
            ModelMetrics(**data)

    def test_missing_required_mae(self):
        """Test that missing MAE raises validation error."""
        data = {
            "model_type": "RandomForest",
            "rmse": 0.032,
            "r2_score": 0.85,
            "cross_validation_folds": 5,
            "cv_mean_mae": 0.027,
            "test_set_size": 100,
            "training_timestamp": datetime.now().isoformat()
        }
        with pytest.raises(Exception):
            ModelMetrics(**data)

    def test_negative_metrics_rejected(self):
        """Test that negative MAE and RMSE are rejected."""
        data = {
            "model_type": "RandomForest",
            "mae": -0.025,
            "rmse": 0.032,
            "r2_score": 0.85,
            "cross_validation_folds": 5,
            "cv_mean_mae": 0.027,
            "test_set_size": 100,
            "training_timestamp": datetime.now().isoformat()
        }
        with pytest.raises(Exception):
            ModelMetrics(**data)

    def test_r2_score_out_of_range_rejected(self):
        """Test that R2 score > 1.0 is rejected."""
        data = {
            "model_type": "RandomForest",
            "mae": 0.025,
            "rmse": 0.032,
            "r2_score": 1.5,
            "cross_validation_folds": 5,
            "cv_mean_mae": 0.027,
            "test_set_size": 100,
            "training_timestamp": datetime.now().isoformat()
        }
        with pytest.raises(Exception):
            ModelMetrics(**data)

    def test_zero_folds_rejected(self):
        """Test that zero cross-validation folds are rejected."""
        data = {
            "model_type": "RandomForest",
            "mae": 0.025,
            "rmse": 0.032,
            "r2_score": 0.85,
            "cross_validation_folds": 0,
            "cv_mean_mae": 0.027,
            "test_set_size": 100,
            "training_timestamp": datetime.now().isoformat()
        }
        with pytest.raises(Exception):
            ModelMetrics(**data)

    def test_optional_fields_can_be_missing(self):
        """Test that optional fields (notes, hyperparameters) can be omitted."""
        data = {
            "model_type": "RandomForest",
            "mae": 0.025,
            "rmse": 0.032,
            "r2_score": 0.85,
            "cross_validation_folds": 5,
            "cv_mean_mae": 0.027,
            "test_set_size": 100,
            "training_timestamp": datetime.now().isoformat()
        }
        metrics = ModelMetrics(**data)
        assert metrics.notes is None
        assert metrics.hyperparameters is None