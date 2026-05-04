"""
Contract test for AnomalyDetectorService interface.

Validates that AnomalyDetectorService conforms to specs/contracts/anomaly_detector.schema.yaml
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

# Import services (will be created in T072)
try:
    from services.anomaly_detector import AnomalyDetectorService
except ImportError:
    # Service not yet implemented - test will be skipped
    AnomalyDetectorService = None

class TestAnomalyDetectorSchema:
    """Validate AnomalyDetectorService interface matches schema."""

    @pytest.mark.skipif(AnomalyDetectorService is None, reason="Service not yet implemented")
    def test_service_interface(self):
        """AnomalyDetectorService must have required methods."""
        # Check required interface methods exist
        required_methods = [
            'load_model',
            'process_stream',
            'update_model',
            'compute_score',
            'get_uncertainty',
            'save_checkpoint',
            '__init__'
        ]
        
        for method_name in required_methods:
            assert hasattr(AnomalyDetectorService, method_name), \
                f"Missing required method: {method_name}"

    @pytest.mark.skipif(AnomalyDetectorService is None, reason="Service not yet implemented")
    def test_service_initialization(self):
        """Service must initialize with config."""
        service = AnomalyDetectorService(config_path="config.yaml")
        
        assert service is not None
        assert hasattr(service, 'config')
        assert hasattr(service, 'model')

    @pytest.mark.skipif(AnomalyDetectorService is None, reason="Service not yet implemented")
    def test_process_stream_output(self):
        """process_stream must return valid anomaly scores."""
        service = AnomalyDetectorService(config_path="config.yaml")
        
        # Create test stream
        test_data = np.random.randn(100, 1)
        
        # Process stream
        scores = service.process_stream(test_data)
        
        # Validate output
        assert isinstance(scores, list)
        assert len(scores) == 100
        
        # Each score should have required fields
        for score in scores:
            assert hasattr(score, 'anomaly_score')
            assert hasattr(score, 'is_anomaly')
            assert hasattr(score, 'uncertainty')

    @pytest.mark.skipif(AnomalyDetectorService is None, reason="Service not yet implemented")
    def test_checkpoint_save_load(self, tmp_path):
        """save_checkpoint and load_model must work together."""
        service = AnomalyDetectorService(config_path="config.yaml")
        
        # Train on some data
        train_data = np.random.randn(50, 1)
        service.process_stream(train_data)
        
        # Save checkpoint
        checkpoint_path = tmp_path / "checkpoint.pkl"
        service.save_checkpoint(str(checkpoint_path))
        
        # Load checkpoint
        service.load_model(str(checkpoint_path))
        
        # Verify model state is restored
        assert service.model is not None
