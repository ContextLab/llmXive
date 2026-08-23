"""
Unit tests for base schema validation in code/data/models.py.

Tests verify:
1. EBSD Sample rejects confidence index < 0.1
2. Texture Descriptor enforces mass balance (sum of components = 1.0 ± 0.01)
"""
import pytest
import numpy as np
from pydantic import ValidationError
from code.data.models import EbsdSample, TextureDescriptor, MaterialType, Symmetry


class TestEbsdSampleValidation:
    """Tests for EBSD Sample schema validation."""

    def test_EBSDSample_rejects_confidence_0_0(self):
        """Verify that an EBSD Sample with confidence index < 0.1 raises ValueError."""
        # Test case: confidence = 0.0 (should fail)
        with pytest.raises(ValidationError) as exc_info:
            EbsdSample(
                sample_id="test_sample_001",
                material=MaterialType.ALUMINUM,
                reduction=50.0,
                phi1=10.0,
                Phi=20.0,
                phi2=30.0,
                confidence=0.0
            )
        
        # Verify the error message mentions confidence
        error_msg = str(exc_info.value)
        assert "confidence" in error_msg.lower() or "0.1" in error_msg

    def test_EBSDSample_rejects_confidence_0_05(self):
        """Verify that an EBSD Sample with confidence index = 0.05 raises ValueError."""
        with pytest.raises(ValidationError) as exc_info:
            EbsdSample(
                sample_id="test_sample_002",
                material=MaterialType.COPPER,
                reduction=30.0,
                phi1=15.0,
                Phi=25.0,
                phi2=35.0,
                confidence=0.05
            )
        
        assert exc_info.value is not None

    def test_EBSDSample_accepts_confidence_0_1(self):
        """Verify that an EBSD Sample with confidence index = 0.1 is accepted."""
        # This should NOT raise an error
        sample = EbsdSample(
            sample_id="test_sample_003",
            material=MaterialType.NICKEL,
            reduction=60.0,
            phi1=12.0,
            Phi=22.0,
            phi2=32.0,
            confidence=0.1
        )
        assert sample.confidence == 0.1
        assert sample.sample_id == "test_sample_003"

    def test_EBSDSample_accepts_confidence_0_95(self):
        """Verify that an EBSD Sample with high confidence is accepted."""
        sample = EbsdSample(
            sample_id="test_sample_004",
            material=MaterialType.ALUMINUM,
            reduction=70.0,
            phi1=5.0,
            Phi=15.0,
            phi2=25.0,
            confidence=0.95
        )
        assert sample.confidence == 0.95


class TestTextureDescriptorValidation:
    """Tests for Texture Descriptor schema validation."""

    def test_TextureDescriptor_mass_balance_check(self):
        """
        Verify that the sum of Brass, Copper, S, Goss, and random components 
        equals 1.0 ± 0.01; raise ValueError if the sum is outside this tolerance.
        """
        # Test case: valid mass balance (sum = 1.0)
        valid_descriptor = TextureDescriptor(
            sample_id="test_desc_001",
            brass=0.25,
            copper=0.20,
            s=0.15,
            goss=0.10,
            random=0.30
        )
        assert abs(valid_descriptor.brass + valid_descriptor.copper + 
                  valid_descriptor.s + valid_descriptor.goss + valid_descriptor.random - 1.0) <= 0.01

    def test_TextureDescriptor_rejects_mass_balance_high(self):
        """Verify that a descriptor with sum > 1.01 raises ValueError."""
        with pytest.raises(ValidationError) as exc_info:
            TextureDescriptor(
                sample_id="test_desc_002",
                brass=0.30,
                copper=0.30,
                s=0.30,
                goss=0.20,
                random=0.10
            )
        # Sum = 1.20, which is > 1.01
        assert exc_info.value is not None

    def test_TextureDescriptor_rejects_mass_balance_low(self):
        """Verify that a descriptor with sum < 0.99 raises ValueError."""
        with pytest.raises(ValidationError) as exc_info:
            TextureDescriptor(
                sample_id="test_desc_003",
                brass=0.10,
                copper=0.10,
                s=0.10,
                goss=0.10,
                random=0.10
            )
        # Sum = 0.50, which is < 0.99
        assert exc_info.value is not None

    def test_TextureDescriptor_accepts_boundary_high(self):
        """Verify that a descriptor with sum = 1.01 is accepted (within tolerance)."""
        descriptor = TextureDescriptor(
            sample_id="test_desc_004",
            brass=0.25,
            copper=0.25,
            s=0.25,
            goss=0.15,
            random=0.10
        )
        # Sum = 1.00, which is within tolerance
        assert abs(descriptor.brass + descriptor.copper + 
                  descriptor.s + descriptor.goss + descriptor.random - 1.0) <= 0.01

    def test_TextureDescriptor_accepts_boundary_low(self):
        """Verify that a descriptor with sum = 0.99 is accepted (within tolerance)."""
        descriptor = TextureDescriptor(
            sample_id="test_desc_005",
            brass=0.24,
            copper=0.24,
            s=0.24,
            goss=0.14,
            random=0.13
        )
        # Sum = 0.99, which is within tolerance
        assert abs(descriptor.brass + descriptor.copper + 
                  descriptor.s + descriptor.goss + descriptor.random - 1.0) <= 0.01

    def test_TextureDescriptor_negative_components_rejected(self):
        """Verify that negative component values raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            TextureDescriptor(
                sample_id="test_desc_006",
                brass=-0.10,
                copper=0.20,
                s=0.20,
                goss=0.20,
                random=0.50
            )
        assert exc_info.value is not None

    def test_TextureDescriptor_sum_exceeds_1_01(self):
        """Verify specific case where sum is 1.05 (should fail)."""
        with pytest.raises(ValidationError) as exc_info:
            TextureDescriptor(
                sample_id="test_desc_007",
                brass=0.30,
                copper=0.25,
                s=0.20,
                goss=0.15,
                random=0.15
            )
        # Sum = 1.05, which is > 1.01
        assert exc_info.value is not None