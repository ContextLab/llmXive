import pytest
from code.src.detection.schema import (
    LLMCodeDetectionResult,
    ConfidenceLevel,
)


def test_llm_detection_result_creation():
    """Test basic creation of LLMCodeDetectionResult."""
    result = LLMCodeDetectionResult(
        pr_id="PR-123",
        file_path="src/main.py",
        line_start=10,
        line_end=25,
        confidence=ConfidenceLevel.HIGH,
        detection_method="heuristic",
        is_llm_generated=True,
    )

    assert result.pr_id == "PR-123"
    assert result.file_path == "src/main.py"
    assert result.line_start == 10
    assert result.line_end == 25
    assert result.confidence == ConfidenceLevel.HIGH
    assert result.detection_method == "heuristic"
    assert result.is_llm_generated is True
    assert result.metadata == {}


def test_llm_detection_result_json_roundtrip():
    """Test JSON serialization and deserialization."""
    original = LLMCodeDetectionResult(
        pr_id="PR-456",
        file_path="utils/helper.py",
        line_start=5,
        line_end=15,
        confidence=ConfidenceLevel.MEDIUM,
        detection_method="model",
        is_llm_generated=False,
        metadata={"source": "test", "score": 0.85},
    )

    json_str = original.to_json()
    restored = LLMCodeDetectionResult.from_json(json_str)

    assert restored.pr_id == original.pr_id
    assert restored.file_path == original.file_path
    assert restored.line_start == original.line_start
    assert restored.line_end == original.line_end
    assert restored.confidence == original.confidence
    assert restored.detection_method == original.detection_method
    assert restored.is_llm_generated == original.is_llm_generated
    assert restored.metadata == original.metadata


def test_llm_detection_result_to_dict():
    """Test conversion to dictionary."""
    result = LLMCodeDetectionResult(
        pr_id="PR-789",
        file_path="test.py",
        line_start=1,
        line_end=10,
        confidence=ConfidenceLevel.LOW,
        detection_method="heuristic",
        is_llm_generated=True,
        metadata={"key": "value"},
    )

    result_dict = result.to_dict()

    assert result_dict["pr_id"] == "PR-789"
    assert result_dict["file_path"] == "test.py"
    assert result_dict["line_start"] == 1
    assert result_dict["line_end"] == 10
    assert result_dict["confidence"] == "low"
    assert result_dict["detection_method"] == "heuristic"
    assert result_dict["is_llm_generated"] is True
    assert result_dict["metadata"] == {"key": "value"}


def test_llm_detection_result_from_dict_invalid_confidence():
    """Test that invalid confidence level raises ValueError."""
    invalid_data = {
        "pr_id": "PR-100",
        "file_path": "file.py",
        "line_start": 1,
        "line_end": 5,
        "confidence": "invalid_level",
        "detection_method": "heuristic",
        "is_llm_generated": True,
    }

    with pytest.raises(ValueError, match="Invalid confidence level"):
        LLMCodeDetectionResult.from_dict(invalid_data)


def test_llm_detection_result_missing_optional_fields():
    """Test that missing optional fields (metadata) default to empty dict."""
    data = {
        "pr_id": "PR-200",
        "file_path": "file.py",
        "line_start": 1,
        "line_end": 5,
        "confidence": "high",
        "detection_method": "heuristic",
        "is_llm_generated": True,
    }

    result = LLMCodeDetectionResult.from_dict(data)
    assert result.metadata == {}


def test_llm_detection_result_missing_required_fields():
    """Test that missing required fields raise ValueError."""
    # Missing pr_id
    data_missing_pr_id = {
        "file_path": "file.py",
        "line_start": 1,
        "line_end": 5,
        "confidence": "high",
        "detection_method": "heuristic",
        "is_llm_generated": True,
    }

    with pytest.raises(ValueError, match="Missing required field: pr_id"):
        LLMCodeDetectionResult.from_dict(data_missing_pr_id)

    # Missing confidence
    data_missing_confidence = {
        "pr_id": "PR-300",
        "file_path": "file.py",
        "line_start": 1,
        "line_end": 5,
        "detection_method": "heuristic",
        "is_llm_generated": True,
    }

    with pytest.raises(ValueError, match="Missing required field: confidence"):
        LLMCodeDetectionResult.from_dict(data_missing_confidence)

    # Missing file_path
    data_missing_file = {
        "pr_id": "PR-300",
        "line_start": 1,
        "line_end": 5,
        "confidence": "high",
        "detection_method": "heuristic",
        "is_llm_generated": True,
    }

    with pytest.raises(ValueError, match="Missing required field: file_path"):
        LLMCodeDetectionResult.from_dict(data_missing_file)

    # Missing line_start
    data_missing_start = {
        "pr_id": "PR-300",
        "file_path": "file.py",
        "line_end": 5,
        "confidence": "high",
        "detection_method": "heuristic",
        "is_llm_generated": True,
    }

    with pytest.raises(ValueError, match="Missing required field: line_start"):
        LLMCodeDetectionResult.from_dict(data_missing_start)

    # Missing line_end
    data_missing_end = {
        "pr_id": "PR-300",
        "file_path": "file.py",
        "line_start": 1,
        "confidence": "high",
        "detection_method": "heuristic",
        "is_llm_generated": True,
    }

    with pytest.raises(ValueError, match="Missing required field: line_end"):
        LLMCodeDetectionResult.from_dict(data_missing_end)

    # Missing detection_method
    data_missing_method = {
        "pr_id": "PR-300",
        "file_path": "file.py",
        "line_start": 1,
        "line_end": 5,
        "confidence": "high",
        "is_llm_generated": True,
    }

    with pytest.raises(ValueError, match="Missing required field: detection_method"):
        LLMCodeDetectionResult.from_dict(data_missing_method)

    # Missing is_llm_generated
    data_missing_flag = {
        "pr_id": "PR-300",
        "file_path": "file.py",
        "line_start": 1,
        "line_end": 5,
        "confidence": "high",
        "detection_method": "heuristic",
    }

    with pytest.raises(ValueError, match="Missing required field: is_llm_generated"):
        LLMCodeDetectionResult.from_dict(data_missing_flag)