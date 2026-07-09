"""
Unit tests for base schema validation in code/data/models.py.

Tests cover:
- Enum validation for MaterialType and Symmetry
- Pydantic model validation for EbsdSample and TextureDescriptor
- Custom field validators (e.g., confidence_index >= 0)
- Model validators for logical consistency (e.g., volume fractions sum)
"""
import pytest
import numpy as np
from datetime import datetime
from typing import List, Dict, Any

from code.data.models import (
    MaterialType,
    Symmetry,
    TextureComponent,
    EbsdSample,
    TextureDescriptor,
    EbsdDatasetMetadata,
    ModelInput,
)
from pydantic import ValidationError


class TestMaterialType:
    """Tests for MaterialType enum."""

    def test_valid_material_types(self):
        """Test that valid material types can be instantiated."""
        assert MaterialType.ALUMINUM == "Al"
        assert MaterialType.COPPER == "Cu"
        assert MaterialType.NICKEL == "Ni"

    def test_invalid_material_type(self):
        """Test that invalid material types raise ValidationError."""
        with pytest.raises(ValidationError):
            MaterialType("Titanium")


class TestSymmetry:
    """Tests for Symmetry enum."""

    def test_valid_symmetries(self):
        """Test that valid symmetries can be instantiated."""
        assert Symmetry.FCC == "FCC"
        assert Symmetry.BCC == "BCC"
        assert Symmetry.HCP == "HCP"

    def test_invalid_symmetry(self):
        """Test that invalid symmetries raise ValidationError."""
        with pytest.raises(ValidationError):
            Symmetry("Rhombohedral")


class TestEbsdSample:
    """Tests for EbsdSample model validation."""

    def test_valid_ebsd_sample(self):
        """Test creation of a valid EbsdSample."""
        sample = EbsdSample(
            sample_id="sample_001",
            material=MaterialType.ALUMINUM,
            reduction=0.5,
            confidence_index=0.85,
            euler_angles=np.array([45.0, 35.0, 45.0]),
            symmetry=Symmetry.FCC,
            timestamp=datetime.now(),
        )
        assert sample.sample_id == "sample_001"
        assert sample.reduction == 0.5
        assert sample.confidence_index == 0.85

    def test_confidence_index_negative(self):
        """Test that negative confidence_index raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            EbsdSample(
                sample_id="sample_002",
                material=MaterialType.COPPER,
                reduction=0.3,
                confidence_index=-0.1,
                euler_angles=np.array([30.0, 20.0, 10.0]),
                symmetry=Symmetry.FCC,
                timestamp=datetime.now(),
            )
        assert "confidence_index" in str(exc_info.value)

    def test_confidence_index_zero(self):
        """Test that zero confidence_index is valid (boundary condition)."""
        sample = EbsdSample(
            sample_id="sample_003",
            material=MaterialType.NICKEL,
            reduction=0.2,
            confidence_index=0.0,
            euler_angles=np.array([10.0, 10.0, 10.0]),
            symmetry=Symmetry.FCC,
            timestamp=datetime.now(),
        )
        assert sample.confidence_index == 0.0

    def test_reduction_negative(self):
        """Test that negative reduction raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            EbsdSample(
                sample_id="sample_004",
                material=MaterialType.ALUMINUM,
                reduction=-0.1,
                confidence_index=0.5,
                euler_angles=np.array([45.0, 35.0, 45.0]),
                symmetry=Symmetry.FCC,
                timestamp=datetime.now(),
            )
        assert "reduction" in str(exc_info.value)

    def test_reduction_exceeds_one(self):
        """Test that reduction > 1.0 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            EbsdSample(
                sample_id="sample_005",
                material=MaterialType.COPPER,
                reduction=1.5,
                confidence_index=0.5,
                euler_angles=np.array([45.0, 35.0, 45.0]),
                symmetry=Symmetry.FCC,
                timestamp=datetime.now(),
            )
        assert "reduction" in str(exc_info.value)

    def test_missing_required_fields(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            EbsdSample(
                sample_id="sample_006",
                material=MaterialType.ALUMINUM,
                # Missing reduction, confidence_index, euler_angles, symmetry, timestamp
            )


class TestTextureDescriptor:
    """Tests for TextureDescriptor model validation."""

    def test_valid_texture_descriptor(self):
        """Test creation of a valid TextureDescriptor."""
        descriptor = TextureDescriptor(
            sample_id="sample_001",
            texture_index=1.5,
            brass_volume_fraction=0.25,
            copper_volume_fraction=0.15,
            s_volume_fraction=0.10,
            goss_volume_fraction=0.05,
            random_volume_fraction=0.45,
        )
        assert descriptor.sample_id == "sample_001"
        assert descriptor.texture_index == 1.5
        assert abs(descriptor.brass_volume_fraction - 0.25) < 1e-6

    def test_volume_fractions_sum_to_one(self):
        """Test that volume fractions sum to 1.0 within tolerance."""
        descriptor = TextureDescriptor(
            sample_id="sample_007",
            texture_index=1.2,
            brass_volume_fraction=0.3,
            copper_volume_fraction=0.2,
            s_volume_fraction=0.2,
            goss_volume_fraction=0.1,
            random_volume_fraction=0.2,
        )
        total = (
            descriptor.brass_volume_fraction
            + descriptor.copper_volume_fraction
            + descriptor.s_volume_fraction
            + descriptor.goss_volume_fraction
            + descriptor.random_volume_fraction
        )
        assert abs(total - 1.0) < 1e-6

    def test_volume_fractions_exceed_one(self):
        """Test that volume fractions summing > 1.0 + tolerance raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            TextureDescriptor(
                sample_id="sample_008",
                texture_index=1.0,
                brass_volume_fraction=0.5,
                copper_volume_fraction=0.4,
                s_volume_fraction=0.3,
                goss_volume_fraction=0.2,
                random_volume_fraction=0.2,
            )
        assert "sum" in str(exc_info.value).lower() or "volume" in str(exc_info.value).lower()

    def test_volume_fractions_negative(self):
        """Test that negative volume fractions raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            TextureDescriptor(
                sample_id="sample_009",
                texture_index=1.0,
                brass_volume_fraction=-0.1,
                copper_volume_fraction=0.2,
                s_volume_fraction=0.2,
                goss_volume_fraction=0.1,
                random_volume_fraction=0.6,
            )
        assert "brass_volume_fraction" in str(exc_info.value)

    def test_texture_index_negative(self):
        """Test that negative texture_index raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            TextureDescriptor(
                sample_id="sample_010",
                texture_index=-0.5,
                brass_volume_fraction=0.2,
                copper_volume_fraction=0.2,
                s_volume_fraction=0.2,
                goss_volume_fraction=0.1,
                random_volume_fraction=0.3,
            )
        assert "texture_index" in str(exc_info.value)


class TestEbsdDatasetMetadata:
    """Tests for EbsdDatasetMetadata model validation."""

    def test_valid_metadata(self):
        """Test creation of valid metadata."""
        metadata = EbsdDatasetMetadata(
            dataset_id="test_dataset_001",
            source="HuggingFace",
            material=MaterialType.ALUMINUM,
            symmetry=Symmetry.FCC,
            sample_count=100,
            created_at=datetime.now(),
        )
        assert metadata.dataset_id == "test_dataset_001"
        assert metadata.sample_count == 100

    def test_missing_optional_fields(self):
        """Test that optional fields can be omitted."""
        metadata = EbsdDatasetMetadata(
            dataset_id="test_dataset_002",
            source="Local",
            material=MaterialType.COPPER,
            symmetry=Symmetry.FCC,
            sample_count=50,
            created_at=datetime.now(),
        )
        assert metadata.description is None
        assert metadata.version is None


class TestModelInput:
    """Tests for ModelInput model validation."""

    def test_valid_model_input(self):
        """Test creation of valid model input."""
        input_data = ModelInput(
            reduction=0.5,
            material=MaterialType.ALUMINUM,
            texture_index=1.5,
            brass_volume_fraction=0.25,
            copper_volume_fraction=0.15,
            s_volume_fraction=0.10,
            goss_volume_fraction=0.05,
        )
        assert input_data.reduction == 0.5
        assert input_data.material == MaterialType.ALUMINUM

    def test_missing_optional_texture_components(self):
        """Test that optional texture components can be omitted."""
        input_data = ModelInput(
            reduction=0.3,
            material=MaterialType.NICKEL,
            texture_index=1.2,
            # Missing volume fractions
        )
        assert input_data.brass_volume_fraction is None
        assert input_data.copper_volume_fraction is None

    def test_invalid_material_in_model_input(self):
        """Test that invalid material in ModelInput raises ValidationError."""
        with pytest.raises(ValidationError):
            ModelInput(
                reduction=0.4,
                material="InvalidMaterial",
                texture_index=1.0,
            )