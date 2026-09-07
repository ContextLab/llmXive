import pytest
from code.src.detection.schema import (
    LLMCodeDetectionResult,
    ConfidenceLevel
)


def test_llm_detection_result_creation():
    """Test basic creation of LLMCodeDetectionResult."""
    result = LLMCodeDetectionResult(
        pr_id="PR-123",
        file_path="src/main.py",
        line_start=10,
        line_end=25,
        confidence=ConfidenceLevel.HIGH,
        confidence_score=0.95,
        detection_method="heuristic_pattern_match",
        snippet_preview="def generate_code(): ..."
    )
    
    assert result.pr_id == "PR-123"
    assert result.file_path == "src/main.py"
    assert result.line_start == 10
    assert result.line_end == 25
    assert result.confidence == ConfidenceLevel.HIGH
    assert result.confidence_score == 0.95
    assert result.detection_method == "heuristic_pattern_match"
    assert result.is_llm_generated is True
    assert result.snippet_preview == "def generate_code(): ..."
    assert isinstance(result.metadata, dict)


def test_llm_detection_result_json_roundtrip():
    """Test that LLMCodeDetectionResult can be serialized and deserialized correctly."""
    original = LLMCodeDetectionResult(
        pr_id="PR-456",
        file_path="utils/helper.py",
        line_start=1,
        line_end=50,
        confidence=ConfidenceLevel.MEDIUM,
        confidence_score=0.75,
        detection_method="ml_model_v2",
        snippet_preview="import os",
        is_llm_generated=True,
        metadata={"source": "test_runner", "version": "1.0"}
    )
    
    json_str = original.to_json()
    restored = LLMCodeDetectionResult.from_json(json_str)
    
    assert restored.pr_id == original.pr_id
    assert restored.file_path == original.file_path
    assert restored.line_start == original.line_start
    assert restored.line_end == original.line_end
    assert restored.confidence == original.confidence
    assert restored.confidence_score == original.confidence_score
    assert restored.detection_method == original.detection_method
    assert restored.is_llm_generated == original.is_llm_generated
    assert restored.metadata == original.metadata


def test_llm_detection_result_to_dict():
    """Test conversion to dictionary."""
    result = LLMCodeDetectionResult(
        pr_id="PR-789",
        file_path="data/processor.py",
        line_start=100,
        line_end=150,
        confidence=ConfidenceLevel.LOW,
        confidence_score=0.35,
        detection_method="regex_pattern",
        is_llm_generated=False
    )
    
    data = result.to_dict()
    
    assert data["pr_id"] == "PR-789"
    assert data["file_path"] == "data/processor.py"
    assert data["line_start"] == 100
    assert data["line_end"] == 150
    assert data["confidence"] == "low"
    assert data["confidence_score"] == 0.35
    assert data["detection_method"] == "regex_pattern"
    assert data["is_llm_generated"] is False


def test_llm_detection_result_from_dict_invalid_confidence():
    """Test that invalid confidence level raises ValueError."""
    invalid_data = {
        "pr_id": "PR-999",
        "file_path": "test.py",
        "line_start": 1,
        "line_end": 10,
        "confidence": "invalid_level",
        "confidence_score": 0.5,
        "detection_method": "test"
    }
    
    with pytest.raises(ValueError, match="Invalid confidence level"):
        LLMCodeDetectionResult.from_dict(invalid_data)


def test_llm_detection_result_missing_optional_fields():
    """Test that missing optional fields default correctly."""
    minimal_data = {
        "pr_id": "PR-MIN",
        "file_path": "minimal.py",
        "line_start": 1,
        "line_end": 5,
        "confidence": "high",
        "confidence_score": 0.9,
        "detection_method": "test_method"
    }
    
    result = LLMCodeDetectionResult.from_dict(minimal_data)
    
    assert result.snippet_preview is None
    assert result.is_llm_generated is True
    assert result.metadata == {}
    assert result.pr_id == "PR-MIN"


def test_llm_detection_result_missing_required_fields():
    """Test that missing required fields raise ValueError."""
    incomplete_data = {
        "pr_id": "PR-NO-END",
        "file_path": "incomplete.py",
        # Missing line_end, confidence, etc.
    }
    
    with pytest.raises(ValueError, match="Missing required field"):
        LLMCodeDetectionResult.from_dict(incomplete_data)