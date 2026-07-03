"""
Tests for the LLM code detection schema.
"""
import pytest
from code.src.detection.schema import (
    LLMCodeDetectionResult,
    ConfidenceLevel
)


def test_llm_detection_result_creation():
    """Test basic creation of an LLMCodeDetectionResult."""
    result = LLMCodeDetectionResult(
        pr_id="PR-123",
        file_path="src/main.py",
        line_start=10,
        line_end=25,
        detected=True,
        confidence=ConfidenceLevel.HIGH,
        heuristic_name="perplexity_score",
        heuristic_details={"score": 0.15}
    )

    assert result.pr_id == "PR-123"
    assert result.file_path == "src/main.py"
    assert result.line_start == 10
    assert result.line_end == 25
    assert result.detected is True
    assert result.confidence == ConfidenceLevel.HIGH
    assert result.heuristic_name == "perplexity_score"
    assert result.heuristic_details == {"score": 0.15}


def test_llm_detection_result_json_roundtrip():
    """Test that an LLMCodeDetectionResult can be serialized and deserialized."""
    original = LLMCodeDetectionResult(
        pr_id="PR-456",
        file_path="tests/test_utils.py",
        line_start=5,
        line_end=12,
        detected=False,
        confidence=ConfidenceLevel.MEDIUM,
        heuristic_name="ngram_overlap",
        heuristic_details={"overlap": 0.4},
        raw_snippet="def hello():\n    pass",
        metadata={"source": "manual_review"}
    )

    json_str = original.to_json()
    restored = LLMCodeDetectionResult.from_json(json_str)

    assert restored.pr_id == original.pr_id
    assert restored.file_path == original.file_path
    assert restored.line_start == original.line_start
    assert restored.line_end == original.line_end
    assert restored.detected == original.detected
    assert restored.confidence == original.confidence
    assert restored.heuristic_name == original.heuristic_name
    assert restored.heuristic_details == original.heuristic_details
    assert restored.raw_snippet == original.raw_snippet
    assert restored.metadata == original.metadata


def test_llm_detection_result_to_dict():
    """Test the to_dict method."""
    result = LLMCodeDetectionResult(
        pr_id="PR-789",
        file_path="config.yaml",
        line_start=1,
        line_end=1,
        detected=True,
        confidence=ConfidenceLevel.LOW,
        heuristic_name="template_match",
        heuristic_details={"match_id": "tpl-001"}
    )

    d = result.to_dict()

    assert isinstance(d, dict)
    assert d["pr_id"] == "PR-789"
    assert d["detected"] is True
    assert d["confidence"] == "low"  # Enum value string
    assert "heuristic_details" in d


def test_llm_detection_result_from_dict_invalid_confidence():
    """Test handling of invalid confidence in from_dict (should default or handle gracefully)."""
    # Note: The implementation expects a valid string for ConfidenceLevel constructor.
    # If we pass an invalid string, it should raise ValueError.
    data = {
        "pr_id": "PR-999",
        "file_path": "x.py",
        "line_start": 1,
        "line_end": 2,
        "detected": False,
        "confidence": "invalid_level",
        "heuristic_name": "test",
        "heuristic_details": {}
    }

    with pytest.raises(ValueError):
        LLMCodeDetectionResult.from_dict(data)


def test_llm_detection_result_missing_optional_fields():
    """Test creation with missing optional fields (defaults should apply)."""
    data = {
        "pr_id": "PR-000",
        "file_path": "y.py",
        "line_start": 1,
        "line_end": 5,
        "detected": False,
        "confidence": "uncertain",
        "heuristic_name": "default_heuristic"
        # heuristic_details, raw_snippet, metadata are missing
    }

    result = LLMCodeDetectionResult.from_dict(data)

    assert result.heuristic_details == {}
    assert result.raw_snippet is None
    assert result.metadata == {}