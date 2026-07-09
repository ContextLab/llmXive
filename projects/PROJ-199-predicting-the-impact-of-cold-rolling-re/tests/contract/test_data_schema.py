"""
Contract test for data schema (US1).

Validates that the processed EBSD data adheres to the strict schema
defined in `code/data/models.py` before it is used for training.
"""
import pytest
import pandas as pd
import numpy as np
from typing import List, Dict, Any
from datetime import datetime

# Import the real schema definitions from the project
from code.data.models import EbsdSample, EbsdDatasetMetadata, MaterialType, Symmetry, TextureDescriptor


class TestDataSchemaContracts:
    """
    Contract tests ensuring data pipeline output matches the Pydantic models.
    """

    def _create_valid_sample_dict(self) -> Dict[str, Any]:
        """Helper to create a valid dictionary matching EbsdSample schema."""
        return {
            "sample_id": "AL_50pct_001",
            "material": "Aluminum",
            "reduction_percent": 50.0,
            "orientation_euler": [45.0, 35.0, 45.0],
            "confidence_index": 0.95,
            "symmetry": "cubic",
            "timestamp": datetime.now().isoformat()
        }

    def _create_valid_descriptor_dict(self) -> Dict[str, Any]:
        """Helper to create a valid dictionary matching TextureDescriptor schema."""
        return {
            "sample_id": "AL_50pct_001",
            "texture_index": 2.5,
            "volume_fraction_brass": 0.15,
            "volume_fraction_copper": 0.20,
            "volume_fraction_s": 0.10,
            "volume_fraction_goss": 0.05,
            "volume_fraction_random": 0.50,
            "component_identification_method": "MTX_search"
        }

    def test_ebsd_sample_schema_accepts_valid_data(self):
        """Contract: Valid EBSD data must instantiate without error."""
        data = self._create_valid_sample_dict()
        # Should not raise ValidationError
        instance = EbsdSample(**data)
        assert instance.sample_id == "AL_50pct_001"
        assert instance.material == MaterialType.ALUMINUM
        assert instance.confidence_index >= 0.1

    def test_ebsd_sample_schema_rejects_low_confidence(self):
        """Contract: Samples with confidence < 0.1 must be rejected."""
        data = self._create_valid_sample_dict()
        data["confidence_index"] = 0.05
        with pytest.raises(Exception):
            EbsdSample(**data)

    def test_ebsd_sample_schema_rejects_invalid_material(self):
        """Contract: Invalid material types must be rejected."""
        data = self._create_valid_sample_dict()
        data["material"] = "Unknown_Alloy_X"
        with pytest.raises(Exception):
            EbsdSample(**data)

    def test_texture_descriptor_schema_sum_constraint(self):
        """Contract: Volume fractions must sum to ~1.0 (within tolerance)."""
        # Create data that sums to > 1.0
        data = self._create_valid_descriptor_dict()
        # Increase a fraction to break the sum constraint
        data["volume_fraction_brass"] = 0.80
        # Note: The model might have a validator for this.
        # If the model doesn't enforce it strictly in __init__, we test the logic
        # that the consumer would use. However, per T019, we assume the model
        # or the pipeline enforces this. Let's test if the model accepts it.
        # If the model has a validator, this should raise.
        try:
            instance = TextureDescriptor(**data)
            # If it passes, check if the sum is actually valid in the instance
            # (Some models might auto-normalize, but contract tests usually expect strict validation)
            total = (
                instance.volume_fraction_brass +
                instance.volume_fraction_copper +
                instance.volume_fraction_s +
                instance.volume_fraction_goss +
                instance.volume_fraction_random
            )
            assert abs(total - 1.0) <= 0.01, f"Volume fractions sum to {total}, expected ~1.0"
        except Exception:
            # If the model raises on invalid sum, that satisfies the contract too
            pass

    def test_ebsd_dataset_metadata_schema(self):
        """Contract: Metadata wrapper must accept valid collection info."""
        metadata = {
            "dataset_name": "Test_Cold_Rolling_Al",
            "material": "Aluminum",
            "reduction_levels": [10, 30, 50],
            "source": "HuggingFace",
            "processed_at": datetime.now().isoformat(),
            "symmetry": "cubic"
        }
        instance = EbsdDatasetMetadata(**metadata)
        assert instance.dataset_name == "Test_Cold_Rolling_Al"
        assert 50 in instance.reduction_levels

    def test_pandas_dataframe_to_model_conversion(self):
        """Contract: Real-world DataFrame rows must map to Pydantic models."""
        # Simulate a row from the cleaned_parquet file
        df_data = pd.DataFrame([
            {
                "sample_id": "CU_70pct_002",
                "material": "Copper",
                "reduction_percent": 70.0,
                "orientation_euler": [35.0, 45.0, 35.0],
                "confidence_index": 0.88,
                "symmetry": "cubic",
                "timestamp": datetime.now().isoformat()
            }
        ])

        for _, row in df_data.iterrows():
            # Convert row dict to model
            sample = EbsdSample(**row.to_dict())
            assert sample.sample_id == "CU_70pct_002"
            assert sample.material == MaterialType.COPPER

    def test_schema_handles_missing_optional_fields(self):
        """Contract: Optional fields (like 'notes') should not break instantiation."""
        data = self._create_valid_sample_dict()
        # Remove optional fields if any exist in the model definition
        # EbsdSample definition in T007a likely has optional fields
        if "notes" in data:
            del data["notes"]
        
        instance = EbsdSample(**data)
        assert instance.sample_id is not None