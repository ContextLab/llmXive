"""
Tests for the Inference module schema.
"""
import pytest
import json
from code.src.inference.schema import InferenceRequest, InferenceResponse, InferenceStatus
from code.src.detection.schema import LLMCodeDetectionResult, ConfidenceLevel
from code.src.extraction.schema import Severity


class TestInferenceRequest:
    """Tests for the InferenceRequest dataclass."""

    def test_create_basic_request(self):
        """Test creating a basic inference request."""
        request = InferenceRequest(
            pr_id="123",
            repo="test/repo",
            diff_text="diff content",
            file_path="file.py",
            line_start=10,
            line_end=20
        )
        
        assert request.pr_id == "123"
        assert request.repo == "test/repo"
        assert request.diff_text == "diff content"
        assert request.file_path == "file.py"
        assert request.line_start == 10
        assert request.line_end == 20
        assert request.llm_detection_result is None
        assert request.context_window is None
        assert request.metadata == {}

    def test_create_request_with_optional_fields(self):
        """Test creating a request with optional fields."""
        detection = LLMCodeDetectionResult(
            pr_id="123",
            file_path="file.py",
            is_llm_generated=True,
            confidence=ConfidenceLevel.HIGH,
            reason="pattern match"
        )
        
        request = InferenceRequest(
            pr_id="123",
            repo="test/repo",
            diff_text="diff content",
            file_path="file.py",
            line_start=10,
            line_end=20,
            llm_detection_result=detection,
            context_window=4096,
            metadata={"key": "value"}
        )
        
        assert request.llm_detection_result is not None
        assert request.llm_detection_result.is_llm_generated is True
        assert request.context_window == 4096
        assert request.metadata == {"key": "value"}

    def test_to_dict(self):
        """Test converting request to dictionary."""
        request = InferenceRequest(
            pr_id="123",
            repo="test/repo",
            diff_text="diff content",
            file_path="file.py",
            line_start=10,
            line_end=20,
            metadata={"test": True}
        )
        
        data = request.to_dict()
        
        assert data["pr_id"] == "123"
        assert data["repo"] == "test/repo"
        assert data["diff_text"] == "diff content"
        assert data["file_path"] == "file.py"
        assert data["line_start"] == 10
        assert data["line_end"] == 20
        assert data["metadata"] == {"test": True}

    def test_from_dict(self):
        """Test creating request from dictionary."""
        data = {
            "pr_id": "456",
            "repo": "another/repo",
            "diff_text": "another diff",
            "file_path": "another.py",
            "line_start": 5,
            "line_end": 15,
            "context_window": 2048,
            "metadata": {"source": "test"}
        }
        
        request = InferenceRequest.from_dict(data)
        
        assert request.pr_id == "456"
        assert request.repo == "another/repo"
        assert request.diff_text == "another diff"
        assert request.file_path == "another.py"
        assert request.line_start == 5
        assert request.line_end == 15
        assert request.context_window == 2048
        assert request.metadata == {"source": "test"}

    def test_json_roundtrip(self):
        """Test JSON serialization and deserialization roundtrip."""
        original = InferenceRequest(
            pr_id="789",
            repo="json/repo",
            diff_text="json diff",
            file_path="json.py",
            line_start=1,
            line_end=100,
            metadata={"roundtrip": True}
        )
        
        json_str = json.dumps(original.to_dict())
        loaded_data = json.loads(json_str)
        restored = InferenceRequest.from_dict(loaded_data)
        
        assert original.pr_id == restored.pr_id
        assert original.repo == restored.repo
        assert original.diff_text == restored.diff_text
        assert original.file_path == restored.file_path
        assert original.line_start == restored.line_start
        assert original.line_end == restored.line_end
        assert original.metadata == restored.metadata


class TestInferenceResponse:
    """Tests for the InferenceResponse dataclass."""

    def test_create_success_response(self):
        """Test creating a successful inference response."""
        response = InferenceResponse(
            pr_id="123",
            status=InferenceStatus.SUCCESS,
            latency_seconds=1.5,
            model_id="starcoder2-3b"
        )
        
        assert response.pr_id == "123"
        assert response.status == InferenceStatus.SUCCESS
        assert response.latency_seconds == 1.5
        assert response.model_id == "starcoder2-3b"
        assert response.detected_bugs == []
        assert response.error_message is None

    def test_create_failed_response(self):
        """Test creating a failed inference response."""
        response = InferenceResponse(
            pr_id="123",
            status=InferenceStatus.FAILED,
            error_message="Model timeout",
            latency_seconds=30.0
        )
        
        assert response.status == InferenceStatus.FAILED
        assert response.error_message == "Model timeout"

    def test_add_bug_detection(self):
        """Test adding a bug detection to response."""
        response = InferenceResponse(
            pr_id="123",
            status=InferenceStatus.SUCCESS
        )
        
        response.add_bug_detection(
            file_path="buggy.py",
            line_start=10,
            line_end=15,
            severity=Severity.MAJOR,
            description="Potential null pointer"
        )
        
        assert len(response.detected_bugs) == 1
        bug = response.detected_bugs[0]
        assert bug["file_path"] == "buggy.py"
        assert bug["line_start"] == 10
        assert bug["line_end"] == 15
        assert bug["severity"] == Severity.MAJOR.value
        assert bug["description"] == "Potential null pointer"

    def test_to_dict(self):
        """Test converting response to dictionary."""
        response = InferenceResponse(
            pr_id="123",
            status=InferenceStatus.SUCCESS,
            latency_seconds=2.0,
            tokens_used=150,
            metadata={"model_version": "v1"}
        )
        
        response.add_bug_detection(
            "test.py", 5, 10, Severity.MINOR, "Minor issue"
        )
        
        data = response.to_dict()
        
        assert data["pr_id"] == "123"
        assert data["status"] == "success"
        assert data["latency_seconds"] == 2.0
        assert data["tokens_used"] == 150
        assert len(data["detected_bugs"]) == 1
        assert data["metadata"] == {"model_version": "v1"}

    def test_from_dict_with_string_status(self):
        """Test creating response from dictionary with string status."""
        data = {
            "pr_id": "456",
            "status": "timeout",
            "error_message": "Execution timed out",
            "latency_seconds": 60.0
        }
        
        response = InferenceResponse.from_dict(data)
        
        assert response.status == InferenceStatus.TIMEOUT
        assert response.error_message == "Execution timed out"

    def test_from_dict_with_invalid_status(self):
        """Test creating response with invalid status defaults to ERROR."""
        data = {
            "pr_id": "789",
            "status": "unknown_status",
            "latency_seconds": 0.1
        }
        
        response = InferenceResponse.from_dict(data)
        
        assert response.status == InferenceStatus.ERROR

    def test_json_roundtrip(self):
        """Test JSON serialization and deserialization roundtrip."""
        original = InferenceResponse(
            pr_id="123",
            status=InferenceStatus.SUCCESS,
            latency_seconds=1.23,
            model_id="test-model"
        )
        original.add_bug_detection(
            "file.py", 10, 20, Severity.CRITICAL, "Critical bug"
        )
        
        json_str = json.dumps(original.to_dict())
        loaded_data = json.loads(json_str)
        restored = InferenceResponse.from_dict(loaded_data)
        
        assert original.pr_id == restored.pr_id
        assert original.status == restored.status
        assert original.latency_seconds == restored.latency_seconds
        assert original.model_id == restored.model_id
        assert len(original.detected_bugs) == len(restored.detected_bugs)
        assert original.detected_bugs[0] == restored.detected_bugs[0]