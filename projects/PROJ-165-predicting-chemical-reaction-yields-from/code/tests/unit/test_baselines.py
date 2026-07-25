"""
Unit tests for baseline models in src/models/baselines.py.

Tests verify:
1. Model construction with valid parameters
2. Forward pass produces correct output shape
3. Input dimension validation
4. Masking functionality in SpectrumBaseline
"""
import pytest
import torch
import torch.nn as nn
import numpy as np
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.models.baselines import (
    FingerprintBaseline,
    SpectrumBaseline,
    ConditionBaseline,
    create_baseline_model
)


class TestFingerprintBaseline:
    """Tests for FingerprintBaseline model."""

    def test_model_construction(self):
        """Test that model constructs with correct dimensions."""
        model = FingerprintBaseline(fingerprint_dim=2048, hidden_dim=512)
        assert isinstance(model, nn.Module)
        assert model.fingerprint_dim == 2048
        assert model.hidden_dim == 512

    def test_forward_pass_shape(self):
        """Test forward pass produces correct output shape."""
        batch_size = 32
        fingerprint_dim = 2048
        model = FingerprintBaseline(fingerprint_dim=fingerprint_dim)
        
        fingerprints = torch.randn(batch_size, fingerprint_dim)
        output = model(fingerprints)
        
        assert output.shape == (batch_size, 1)

    def test_forward_single_sample(self):
        """Test forward pass with single sample (no batch dim)."""
        model = FingerprintBaseline(fingerprint_dim=2048)
        
        fingerprints = torch.randn(2048)
        output = model(fingerprints)
        
        assert output.shape == (1, 1)

    def test_wrong_input_dimension(self):
        """Test that wrong input dimension raises ValueError."""
        model = FingerprintBaseline(fingerprint_dim=2048)
        
        # Wrong dimension
        fingerprints = torch.randn(32, 1024)
        
        with pytest.raises(ValueError) as excinfo:
            model(fingerprints)
        
        assert "Expected fingerprint dimension 2048" in str(excinfo.value)


class TestSpectrumBaseline:
    """Tests for SpectrumBaseline model."""

    def test_model_construction(self):
        """Test that model constructs with correct dimensions."""
        model = SpectrumBaseline(spectrum_length=1024, num_channels=2)
        assert isinstance(model, nn.Module)
        assert model.spectrum_length == 1024
        assert model.num_channels == 2

    def test_forward_pass_shape(self):
        """Test forward pass produces correct output shape."""
        batch_size = 32
        spectrum_length = 1024
        num_channels = 2
        model = SpectrumBaseline(spectrum_length=spectrum_length, num_channels=num_channels)
        
        spectra = torch.randn(batch_size, num_channels, spectrum_length)
        output = model(spectra)
        
        assert output.shape == (batch_size, 1)

    def test_forward_with_mask(self):
        """Test forward pass with channel masking."""
        batch_size = 32
        spectrum_length = 1024
        num_channels = 2
        model = SpectrumBaseline(spectrum_length=spectrum_length, num_channels=num_channels)
        
        spectra = torch.randn(batch_size, num_channels, spectrum_length)
        mask = torch.tensor([[True, False], [True, True]] * (batch_size // 2))
        if batch_size % 2 != 0:
            mask = torch.cat([mask, torch.tensor([[True, False]])], dim=0)
        
        output = model(spectra, mask=mask)
        
        assert output.shape == (batch_size, 1)

    def test_wrong_channel_count(self):
        """Test that wrong channel count raises ValueError."""
        model = SpectrumBaseline(spectrum_length=1024, num_channels=2)
        
        # Wrong number of channels
        spectra = torch.randn(32, 3, 1024)
        
        with pytest.raises(ValueError) as excinfo:
            model(spectra)
        
        assert "Expected 2 spectral channels" in str(excinfo.value)

    def test_2d_input_expansion(self):
        """Test that 2D input is automatically expanded to 3D."""
        model = SpectrumBaseline(spectrum_length=1024, num_channels=1)
        
        # 2D input (batch, length)
        spectra = torch.randn(32, 1024)
        output = model(spectra)
        
        assert output.shape == (32, 1)


class TestConditionBaseline:
    """Tests for ConditionBaseline model."""

    def test_model_construction(self):
        """Test that model constructs with correct dimensions."""
        model = ConditionBaseline(solvent_dim=10, catalyst_dim=10)
        assert isinstance(model, nn.Module)
        assert model.total_input_dim == 21  # 10 + 10 + 1 (temp)

    def test_forward_pass_shape(self):
        """Test forward pass produces correct output shape."""
        batch_size = 32
        solvent_dim = 10
        catalyst_dim = 10
        model = ConditionBaseline(solvent_dim=solvent_dim, catalyst_dim=catalyst_dim)
        
        solvent_emb = torch.randn(batch_size, solvent_dim)
        catalyst_emb = torch.randn(batch_size, catalyst_dim)
        temperature = torch.randn(batch_size, 1)
        
        output = model(solvent_emb, catalyst_emb, temperature)
        
        assert output.shape == (batch_size, 1)

    def test_forward_single_temp_dim(self):
        """Test forward pass with 1D temperature input."""
        batch_size = 32
        solvent_dim = 10
        catalyst_dim = 10
        model = ConditionBaseline(solvent_dim=solvent_dim, catalyst_dim=catalyst_dim)
        
        solvent_emb = torch.randn(batch_size, solvent_dim)
        catalyst_emb = torch.randn(batch_size, catalyst_dim)
        temperature = torch.randn(batch_size)  # 1D
        
        output = model(solvent_emb, catalyst_emb, temperature)
        
        assert output.shape == (batch_size, 1)

    def test_wrong_input_dimension(self):
        """Test that wrong input dimension raises ValueError."""
        model = ConditionBaseline(solvent_dim=10, catalyst_dim=10)
        
        solvent_emb = torch.randn(32, 10)
        catalyst_emb = torch.randn(32, 10)
        temperature = torch.randn(32, 1)
        
        # Change solvent dimension
        solvent_emb_wrong = torch.randn(32, 5)
        
        with pytest.raises(ValueError) as excinfo:
            model(solvent_emb_wrong, catalyst_emb, temperature)
        
        assert "Expected total condition dimension 21" in str(excinfo.value)


class TestCreateBaselineModel:
    """Tests for the create_baseline_model factory function."""

    def test_create_fingerprint_model(self):
        """Test creation of fingerprint baseline."""
        model = create_baseline_model('fingerprint', fingerprint_dim=2048)
        assert isinstance(model, FingerprintBaseline)
        assert model.fingerprint_dim == 2048

    def test_create_spectrum_model(self):
        """Test creation of spectrum baseline."""
        model = create_baseline_model('spectrum', spectrum_length=1024, num_channels=2)
        assert isinstance(model, SpectrumBaseline)
        assert model.spectrum_length == 1024
        assert model.num_channels == 2

    def test_create_condition_model(self):
        """Test creation of condition baseline."""
        model = create_baseline_model('condition', solvent_dim=10, catalyst_dim=10)
        assert isinstance(model, ConditionBaseline)
        assert model.total_input_dim == 21

    def test_invalid_model_type(self):
        """Test that invalid model type raises ValueError."""
        with pytest.raises(ValueError) as excinfo:
            create_baseline_model('invalid_type')
        
        assert "Unknown baseline model type" in str(excinfo.value)

    def test_custom_hidden_dim(self):
        """Test creation with custom hidden dimension."""
        model = create_baseline_model('fingerprint', hidden_dim=1024)
        assert model.hidden_dim == 1024

    def test_custom_dropout(self):
        """Test creation with custom dropout rate."""
        model = create_baseline_model('spectrum', dropout=0.5)
        # Check that dropout layers have correct p value
        for module in model.modules():
            if isinstance(module, nn.Dropout):
                assert module.p == 0.5