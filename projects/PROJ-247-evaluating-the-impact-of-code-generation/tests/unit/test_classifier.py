import pytest
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.classifier import CodeBERTClassifier, ClassifierError, ModelNotFoundError
from utils.models import LabelType

class MockOnnxSession:
    """Mock ONNX session for testing."""
    def __init__(self, *args, **kwargs):
        pass
    
    def run(self, *args, **kwargs):
        # Return mock logits [human_score, llm_score]
        return [[[-0.5, 2.0]]]  # High confidence for LLM
    
    def get_inputs(self):
        class Input:
            name = "input_ids"
        return [Input()]

def test_classifier_initialization():
    """Test that classifier can be initialized."""
    # This test will fail if model file is missing, which is expected
    # In real tests, we would mock the model loading
    try:
        classifier = CodeBERTClassifier()
        assert classifier.session is not None
    except ModelNotFoundError:
        # Expected if model file doesn't exist
        pytest.skip("Model file not found, skipping classifier test")

def test_predict_with_mock(monkeypatch):
    """Test prediction with mocked ONNX session."""
    # Mock the ONNX session
    monkeypatch.setattr("utils.classifier.ort.InferenceSession", MockOnnxSession)
    
    classifier = CodeBERTClassifier()
    result = classifier.predict("def hello(): pass")
    
    assert 'label' in result
    assert 'confidence' in result
    assert result['confidence'] > 0.0
    assert result['label'] in [LabelType.HUMAN, LabelType.LLM]

def test_low_confidence_exclusion():
    """Test that low confidence predictions are handled."""
    # Mock session returning low confidence
    class LowConfSession:
        def __init__(self, *args, **kwargs):
            pass
        def run(self, *args, **kwargs):
            return [[[-0.1, 0.1]]]  # Low confidence
        def get_inputs(self):
            class Input:
                name = "input_ids"
            return [Input()]
    
    import utils.classifier
    original_session = utils.classifier.ort.InferenceSession
    utils.classifier.ort.InferenceSession = LowConfSession
    
    try:
        classifier = CodeBERTClassifier()
        result = classifier.predict("def hello(): pass")
        # Even low confidence should return a result, filtering happens in curation script
        assert result['confidence'] >= 0.0
    finally:
        utils.classifier.ort.InferenceSession = original_session
