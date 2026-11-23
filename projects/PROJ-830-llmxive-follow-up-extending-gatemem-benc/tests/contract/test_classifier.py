"""
Contract tests for the intent classifier module.

Verifies that the classifier meets CPU-only and memory constraints.
"""
import pytest
import torch
import logging
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.gatekeeper.classifiers import FrozenDistilBERTClassifier, run_intent_classification
from code.utils.profiling import get_process_memory_mb

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture
def classifier():
    """Create a classifier instance for testing."""
    return FrozenDistilBERTClassifier()

@pytest.fixture
def test_episodes():
    """Provide test episodes."""
    return [
        {"id": "test_001", "text": "Access patient medical records"},
        {"id": "test_002", "text": "Delete my account data"},
        {"id": "test_003", "text": "What is the weather?"}
    ]

class TestClassifierCPUOnly:
    """Tests for CPU-only execution constraint."""
    
    def test_classifier_runs_on_cpu(self, classifier):
        """Verify classifier is configured for CPU."""
        assert classifier.device == "cpu", "Classifier must run on CPU"
    
    def test_no_cuda_usage(self, classifier):
        """Verify no CUDA tensors are used."""
        # Check model device
        model_device = next(classifier.model.parameters()).device
        assert model_device.type == "cpu", "Model must be on CPU"
    
    def test_inference_on_cpu(self, classifier, test_episodes):
        """Verify inference runs on CPU without CUDA errors."""
        results = run_intent_classification(classifier, test_episodes)
        
        assert len(results) == len(test_episodes), "Should classify all episodes"
        
        for result in results:
            assert result.label is not None, "Label should be assigned"
            assert 0.0 <= result.score <= 1.0, "Score must be between 0 and 1"

class TestClassifierMemory:
    """Tests for memory usage constraints."""
    
    def test_memory_under_limit(self, classifier, test_episodes):
        """Verify memory usage stays under 2GB."""
        initial_mem = get_process_memory_mb()
        
        # Run classification
        results = run_intent_classification(classifier, test_episodes)
        
        final_mem = get_process_memory_mb()
        memory_used = final_mem - initial_mem
        
        # Log memory usage
        logger.info(f"Memory used: {memory_used:.2f} MB")
        logger.info(f"Final memory: {final_mem:.2f} MB")
        
        # Check against 2GB limit (with some tolerance)
        assert final_mem < 2000, f"Memory usage {final_mem:.2f}MB exceeds 2GB limit"

class TestClassifierOutput:
    """Tests for classifier output structure."""
    
    def test_result_structure(self, classifier, test_episodes):
        """Verify classification result structure."""
        results = run_intent_classification(classifier, test_episodes)
        
        for result in results:
            assert hasattr(result, "episode_id"), "Result must have episode_id"
            assert hasattr(result, "label"), "Result must have label"
            assert hasattr(result, "score"), "Result must have score"
            assert hasattr(result, "inference_time_ms"), "Result must have inference time"
            assert hasattr(result, "peak_memory_mb"), "Result must have peak memory"
            
            assert isinstance(result.label, str), "Label must be string"
            assert isinstance(result.score, float), "Score must be float"
            assert isinstance(result.inference_time_ms, float), "Time must be float"
            assert isinstance(result.peak_memory_mb, float), "Memory must be float"
    
    def test_all_episodes_classified(self, classifier, test_episodes):
        """Verify all episodes get classified."""
        results = run_intent_classification(classifier, test_episodes)
        
        result_ids = {r.episode_id for r in results}
        input_ids = {ep["id"] for ep in test_episodes}
        
        assert result_ids == input_ids, "All episodes must be classified"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
