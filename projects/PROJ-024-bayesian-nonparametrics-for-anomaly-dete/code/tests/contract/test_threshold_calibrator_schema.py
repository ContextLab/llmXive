"""
Contract test for ThresholdCalibratorService interface.

Validates that ThresholdCalibratorService conforms to specs/contracts/threshold_calibrator.schema.yaml
"""
import pytest
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
from datetime import datetime

# Project root for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
import sys
sys.path.insert(0, str(PROJECT_ROOT / "code"))

# Import services (will be created in T073)
try:
    from services.threshold_calibrator import ThresholdCalibratorService
except ImportError:
    # Service not yet implemented - test will be skipped
    ThresholdCalibratorService = None

class TestThresholdCalibratorSchema:
    """Validate ThresholdCalibratorService interface matches schema."""

    @pytest.mark.skipif(ThresholdCalibratorService is None, reason="Service not yet implemented")
    def test_service_interface(self):
        """ThresholdCalibratorService must have required methods."""
        # Check required interface methods exist
        required_methods = [
            'calibrate',
            'validate_threshold',
            'get_decision_boundary',
            'update_decision_boundary',
            'compute_expected_bounds',
            '__init__'
        ]
        
        for method_name in required_methods:
            assert hasattr(ThresholdCalibratorService, method_name), \
                f"Missing required method: {method_name}"

    @pytest.mark.skipif(ThresholdCalibratorService is None, reason="Service not yet implemented")
    def test_service_initialization(self):
        """Service must initialize with config."""
        service = ThresholdCalibratorService(config_path="config.yaml")
        
        assert service is not None
        assert hasattr(service, 'config')
        assert hasattr(service, 'threshold')

    @pytest.mark.skipif(ThresholdCalibratorService is None, reason="Service not yet implemented")
    def test_calibration_output(self):
        """calibrate must return valid threshold."""
        service = ThresholdCalibratorService(config_path="config.yaml")
        
        # Create test scores
        test_scores = np.random.randn(100)
        
        # Calibrate threshold
        threshold = service.calibrate(test_scores)
        
        # Validate output
        assert isinstance(threshold, (int, float, np.number))
        assert threshold > 0

    @pytest.mark.skipif(ThresholdCalibratorService is None, reason="Service not yet implemented")
    def test_decision_boundary(self):
        """get_decision_boundary must return valid boundary."""
        service = ThresholdCalibratorService(config_path="config.yaml")
        
        boundary = service.get_decision_boundary()
        
        assert isinstance(boundary, dict)
        assert 'threshold' in boundary
        assert 'method' in boundary
        assert 'confidence' in boundary

    @pytest.mark.skipif(ThresholdCalibratorService is None, reason="Service not yet implemented")
    def test_expected_bounds(self):
        """compute_expected_bounds must return valid range."""
        service = ThresholdCalibratorService(config_path="config.yaml")
        
        test_scores = np.random.randn(100)
        bounds = service.compute_expected_bounds(test_scores)
        
        assert isinstance(bounds, dict)
        assert 'lower' in bounds
        assert 'upper' in bounds
        assert bounds['lower'] <= bounds['upper']