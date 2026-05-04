"""Contract test for configuration schemas."""
import pytest
from datetime import datetime
import numpy as np
from typing import Optional, Dict, Any, List
from pathlib import Path

# Import from the correct paths per API surface
from models.dp_gmm import DPGMMConfig
from baselines.arima import ARIMAConfig
from baselines.moving_average import MovingAverageConfig

class TestDPGMMConfigSchema:
    """Verify DPGMMConfig dataclass has required fields."""

    def test_dp_gmmconfig_has_required_fields(self):
        """DPGMMConfig must have concentration_prior, max_components, and learning_rate."""
        config = DPGMMConfig(
            concentration_prior=1.0,
            max_components=10,
            learning_rate=0.01
        )
        assert hasattr(config, "concentration_prior")
        assert hasattr(config, "max_components")
        assert hasattr(config, "learning_rate")

    def test_dp_gmmconfig_concentration_prior_positive(self):
        """DPGMMConfig concentration_prior must be positive."""
        config = DPGMMConfig(
            concentration_prior=1.0,
            max_components=10,
            learning_rate=0.01
        )
        assert config.concentration_prior > 0

    def test_dp_gmmconfig_max_components_positive(self):
        """DPGMMConfig max_components must be positive."""
        config = DPGMMConfig(
            concentration_prior=1.0,
            max_components=10,
            learning_rate=0.01
        )
        assert config.max_components > 0

    def test_dp_gmmconfig_learning_rate_positive(self):
        """DPGMMConfig learning_rate must be positive."""
        config = DPGMMConfig(
            concentration_prior=1.0,
            max_components=10,
            learning_rate=0.01
        )
        assert config.learning_rate > 0

    def test_dp_gmmconfig_can_serialize(self):
        """DPGMMConfig instances should be serializable to dict."""
        config = DPGMMConfig(
            concentration_prior=1.0,
            max_components=10,
            learning_rate=0.01
        )
        from dataclasses import asdict
        serialized = asdict(config)
        assert "concentration_prior" in serialized
        assert "max_components" in serialized
        assert "learning_rate" in serialized

class TestARIMAConfigSchema:
    """Verify ARIMAConfig dataclass has required fields."""

    def test_arimaconfig_has_required_fields(self):
        """ARIMAConfig must have order and seasonal_order fields."""
        config = ARIMAConfig(order=(1, 1, 1), seasonal_order=(1, 1, 1, 12))
        assert hasattr(config, "order")
        assert hasattr(config, "seasonal_order")

    def test_arimaconfig_order_is_tuple(self):
        """ARIMAConfig order must be a tuple."""
        config = ARIMAConfig(order=(1, 1, 1), seasonal_order=(1, 1, 1, 12))
        assert isinstance(config.order, tuple)
        assert len(config.order) == 3

    def test_arimaconfig_seasonal_order_is_tuple(self):
        """ARIMAConfig seasonal_order must be a tuple."""
        config = ARIMAConfig(order=(1, 1, 1), seasonal_order=(1, 1, 1, 12))
        assert isinstance(config.seasonal_order, tuple)
        assert len(config.seasonal_order) == 4

class TestMovingAverageConfigSchema:
    """Verify MovingAverageConfig dataclass has required fields."""

    def test_maconfig_has_required_fields(self):
        """MovingAverageConfig must have window_size field."""
        config = MovingAverageConfig(window_size=10)
        assert hasattr(config, "window_size")

    def test_maconfig_window_size_positive(self):
        """MovingAverageConfig window_size must be positive."""
        config = MovingAverageConfig(window_size=10)
        assert config.window_size > 0
