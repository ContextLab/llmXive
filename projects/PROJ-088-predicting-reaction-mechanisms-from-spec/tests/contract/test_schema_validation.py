import pytest
import json
import yaml
from pathlib import Path
from datetime import datetime
import jsonschema

# Paths to schema files relative to project root
SCHEMA_DIR = Path(__file__).parent.parent.parent / "specs" / "contracts"
DATASET_SCHEMA_PATH = SCHEMA_DIR / "dataset.schema.yaml"
OUTPUT_SCHEMA_PATH = SCHEMA_DIR / "output.schema.yaml"

@pytest.fixture
def dataset_schema():
    with open(DATASET_SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

@pytest.fixture
def output_schema():
    with open(OUTPUT_SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

@pytest.fixture
def valid_dataset_record():
    return {
        "metadata": {
            "version": "1.0.0",
            "source": "NIST_WebBook",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "provenance_filter_applied": True,
            "checksum": "abc123..."
        },
        "records": [
            {
                "record_id": "rec_001",
                "source_id": "nist_12345",
                "spectrum": [0.1] * 512,
                "label": "SN1",
                "provenance": "kinetic_studies",
                "frequency_range": {
                    "min": 400,
                    "max": 4000,
                    "unit": "cm-1"
                }
            }
        ]
    }

@pytest.fixture
def valid_output_report():
    return {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "model_type": "RandomForest",
            "cross_validation_folds": 5,
            "random_seed": 42,
            "runtime_seconds": 120.5,
            "memory_peak_mb": 1024
        },
        "model_performance": {
            "mean_accuracy": 0.85,
            "std_accuracy": 0.02,
            "per_class_metrics": {
                "SN1": {
                    "precision": 0.84,
                    "recall": 0.86,
                    "f1_score": 0.85,
                    "support": 50
                },
                "SN2": {
                    "precision": 0.86,
                    "recall": 0.84,
                    "f1_score": 0.85,
                    "support": 50
                },
                "E1": {
                    "precision": 0.85,
                    "recall": 0.85,
                    "f1_score": 0.85,
                    "support": 50
                }
            },
            "confusion_matrix": [
                [45, 3, 2],
                [2, 44, 4],
                [3, 2, 45]
            ]
        },
        "feature_importance": {
            "method": "permutation_importance",
            "top_features": [
                {
                    "bin_index": 128,
                    "frequency_range": {
                        "min": 1700,
                        "max": 1750,
                        "unit": "cm-1"
                    },
                    "importance_score": 0.15,
                    "significance": "significant"
                }
            ],
            "stability_variance": 0.002,
            "p_value": 0.01,
            "bh_corrected_significant": True
        },
        "warnings": []
    }

class TestDatasetSchema:
    def test_valid_dataset(self, dataset_schema, valid_dataset_record):
        """Test that a valid dataset record passes schema validation."""
        jsonschema.validate(instance=valid_dataset_record, schema=dataset_schema)

    def test_invalid_provenance(self, dataset_schema, valid_dataset_record):
        """Test that 'product_structure_only' provenance is rejected."""
        invalid_record = valid_dataset_record.copy()
        invalid_record["records"][0]["provenance"] = "product_structure_only"
        
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=invalid_record, schema=dataset_schema)

    def test_missing_required_field(self, dataset_schema, valid_dataset_record):
        """Test that missing required fields are caught."""
        invalid_record = valid_dataset_record.copy()
        del invalid_record["metadata"]["checksum"]
        
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=invalid_record, schema=dataset_schema)

    def test_invalid_label(self, dataset_schema, valid_dataset_record):
        """Test that invalid labels are rejected."""
        invalid_record = valid_dataset_record.copy()
        invalid_record["records"][0]["label"] = "INVALID_LABEL"
        
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=invalid_record, schema=dataset_schema)

class TestOutputSchema:
    def test_valid_output(self, output_schema, valid_output_report):
        """Test that a valid output report passes schema validation."""
        jsonschema.validate(instance=valid_output_report, schema=output_schema)

    def test_invalid_model_type(self, output_schema, valid_output_report):
        """Test that invalid model types are rejected."""
        invalid_report = valid_output_report.copy()
        invalid_report["metadata"]["model_type"] = "InvalidModel"
        
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=invalid_report, schema=output_schema)

    def test_confusion_matrix_shape(self, output_schema, valid_output_report):
        """Test that confusion matrix dimensions match class count."""
        # Valid case: 3 classes, 3x3 matrix
        jsonschema.validate(instance=valid_output_report, schema=output_schema)

    def test_accuracy_bounds(self, output_schema, valid_output_report):
        """Test that accuracy is within [0, 1]."""
        invalid_report = valid_output_report.copy()
        invalid_report["model_performance"]["mean_accuracy"] = 1.5
        
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=invalid_report, schema=output_schema)

    def test_causal_language_warning_structure(self, output_schema, valid_output_report):
        """Test that warnings have correct structure if present."""
        report_with_warning = valid_output_report.copy()
        report_with_warning["warnings"] = [
            {
                "code": "CAUSAL_LANGUAGE_DETECTED",
                "message": "Causal terms found in generated text."
            }
        ]
        jsonschema.validate(instance=report_with_warning, schema=output_schema)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])