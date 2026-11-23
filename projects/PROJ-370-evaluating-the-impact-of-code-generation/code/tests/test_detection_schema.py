"""
Unit tests for the LLM Code Detection schema.
"""
import pytest
import json
from code.src.detection.schema import (
    LLMCodeDetectionResult,
    ConfidenceLevel
)


class TestLLMCodeDetectionResult:
    """Tests for the LLMCodeDetectionResult dataclass."""

    def test_creation_basic(self):
        """Test creating a basic detection result."""
        result = LLMCodeDetectionResult(
            pr_id="123",
            repo="test/repo",
            file_path="src/main.py",
            is_llm_generated=True,
            confidence=ConfidenceLevel.HIGH,
            confidence_score=0.85
        )
        assert result.pr_id == "123"
        assert result.repo == "test/repo"
        assert result.file_path == "src/main.py"
        assert result.is_llm_generated is True
        assert result.confidence == ConfidenceLevel.HIGH
        assert result.confidence_score == 0.85
        assert result.detected_patterns == []
        assert result.line_start is None
        assert result.line_end is None

    def test_creation_with_details(self):
        """Test creating a result with full details."""
        result = LLMCodeDetectionResult(
            pr_id="456",
            repo="owner/project",
            file_path="utils/helper.py",
            is_llm_generated=False,
            confidence=ConfidenceLevel.LOW,
            confidence_score=0.12,
            detected_patterns=["repetitive_structure"],
            line_start=10,
            line_end=25,
            snippet_preview="def calculate_sum(a, b):",
            metadata={"heuristic_version": "1.0"}
        )
        assert result.is_llm_generated is False
        assert len(result.detected_patterns) == 1
        assert result.line_start == 10
        assert result.line_end == 25
        assert result.snippet_preview is not None
        assert "heuristic_version" in result.metadata

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = LLMCodeDetectionResult(
            pr_id="789",
            repo="test/repo",
            file_path="test.py",
            is_llm_generated=True,
            confidence=ConfidenceLevel.MEDIUM,
            confidence_score=0.55,
            detected_patterns=["pattern_a", "pattern_b"]
        )
        data = result.to_dict()
        assert isinstance(data, dict)
        assert data["pr_id"] == "789"
        assert data["is_llm_generated"] is True
        assert data["confidence"] == "medium"
        assert "pattern_a" in data["detected_patterns"]

    def test_to_json(self):
        """Test conversion to JSON string."""
        result = LLMCodeDetectionResult(
            pr_id="101",
            repo="org/repo",
            file_path="app.py",
            is_llm_generated=True,
            confidence=ConfidenceLevel.VERY_HIGH,
            confidence_score=0.99
        )
        json_str = result.to_json()
        assert isinstance(json_str, str)
        # Verify it's valid JSON
        parsed = json.loads(json_str)
        assert parsed["pr_id"] == "101"
        assert parsed["confidence"] == "very_high"

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "pr_id": "202",
            "repo": "org/repo",
            "file_path": "main.py",
            "is_llm_generated": True,
            "confidence": "high",
            "confidence_score": 0.88,
            "detected_patterns": ["gen_ai_style"],
            "line_start": 5,
            "line_end": 10,
            "snippet_preview": "print('hello')",
            "metadata": {"source": "test"}
        }
        result = LLMCodeDetectionResult.from_dict(data)
        assert result.pr_id == "202"
        assert result.confidence == ConfidenceLevel.HIGH
        assert result.line_start == 5
        assert result.metadata["source"] == "test"

    def test_from_dict_invalid_confidence(self):
        """Test creation from dictionary with invalid confidence string."""
        data = {
            "pr_id": "303",
            "repo": "org/repo",
            "file_path": "main.py",
            "is_llm_generated": False,
            "confidence": "invalid_level",
            "confidence_score": 0.5
        }
        # Should default to LOW or handle gracefully
        result = LLMCodeDetectionResult.from_dict(data)
        assert result.confidence == ConfidenceLevel.LOW

    def test_from_json(self):
        """Test creation from JSON string."""
        json_str = json.dumps({
            "pr_id": "404",
            "repo": "org/repo",
            "file_path": "test.py",
            "is_llm_generated": False,
            "confidence": "low",
            "confidence_score": 0.1
        })
        result = LLMCodeDetectionResult.from_json(json_str)
        assert result.pr_id == "404"
        assert result.is_llm_generated is False

    def test_json_roundtrip(self):
        """Test that object -> JSON -> object preserves data."""
        original = LLMCodeDetectionResult(
            pr_id="505",
            repo="org/repo",
            file_path="src/code.py",
            is_llm_generated=True,
            confidence=ConfidenceLevel.HIGH,
            confidence_score=0.92,
            detected_patterns=["pattern_1"],
            line_start=1,
            line_end=100,
            snippet_preview="def foo(): pass",
            metadata={"key": "value"}
        )
        json_str = original.to_json()
        restored = LLMCodeDetectionResult.from_json(json_str)

        assert restored.pr_id == original.pr_id
        assert restored.repo == original.repo
        assert restored.file_path == original.file_path
        assert restored.is_llm_generated == original.is_llm_generated
        assert restored.confidence == original.confidence
        assert restored.confidence_score == original.confidence_score
        assert restored.detected_patterns == original.detected_patterns
        assert restored.line_start == original.line_start
        assert restored.line_end == original.line_end
        assert restored.snippet_preview == original.snippet_preview
        assert restored.metadata == original.metadata

    def test_confidence_level_enum_values(self):
        """Test that all confidence levels are defined correctly."""
        assert ConfidenceLevel.LOW.value == "low"
        assert ConfidenceLevel.MEDIUM.value == "medium"
        assert ConfidenceLevel.HIGH.value == "high"
        assert ConfidenceLevel.VERY_HIGH.value == "very_high"
        assert str(ConfidenceLevel.MEDIUM) == "medium"
        assert ConfidenceLevel.MEDIUM.to_json() == "medium"

    def test_empty_patterns(self):
        """Test that empty patterns list is handled correctly."""
        result = LLMCodeDetectionResult(
            pr_id="606",
            repo="org/repo",
            file_path="empty.py",
            is_llm_generated=False,
            confidence=ConfidenceLevel.LOW,
            confidence_score=0.0,
            detected_patterns=[]
        )
        assert result.detected_patterns == []
        data = result.to_dict()
        assert data["detected_patterns"] == []