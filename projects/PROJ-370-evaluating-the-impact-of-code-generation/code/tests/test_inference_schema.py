import pytest
import json
from code.src.inference.schema import InferenceRequest, InferenceResponse, InferenceStatus

class TestInferenceRequest:
    def test_inference_request_creation(self):
        """Test creating a valid InferenceRequest."""
        req = InferenceRequest(
            pr_id="123",
            file_path="test.py",
            line_start=10,
            line_end=20,
            diff_content="def foo(): pass",
            llm_code_flag=True
        )
        assert req.pr_id == "123"
        assert req.file_path == "test.py"
        assert req.line_start == 10
        assert req.line_end == 20
        assert req.llm_code_flag is True
        assert req.temperature == 0.0

    def test_inference_request_json_roundtrip(self):
        """Test serializing and deserializing InferenceRequest."""
        original = InferenceRequest(
            pr_id="456",
            file_path="main.py",
            line_start=1,
            line_end=5,
            diff_content="x = 1",
            llm_code_flag=False,
            request_id="req-001"
        )
        data = original.to_dict()
        reconstructed = InferenceRequest.from_dict(data)

        assert reconstructed.pr_id == original.pr_id
        assert reconstructed.file_path == original.file_path
        assert reconstructed.line_start == original.line_start
        assert reconstructed.line_end == original.line_end
        assert reconstructed.diff_content == original.diff_content
        assert reconstructed.llm_code_flag == original.llm_code_flag
        assert reconstructed.request_id == original.request_id

    def test_inference_request_to_dict(self):
        """Test conversion to dictionary."""
        req = InferenceRequest(
            pr_id="789",
            file_path="utils.py",
            line_start=50,
            line_end=60,
            diff_content="return True",
            llm_code_flag=True,
            temperature=0.7
        )
        data = req.to_dict()
        assert isinstance(data, dict)
        assert data["temperature"] == 0.7
        assert data["context_window_limit"] == 4096  # default

    def test_inference_request_from_dict_invalid(self):
        """Test that missing required fields raise KeyError."""
        data = {"pr_id": "123"}  # Missing other required fields
        with pytest.raises(KeyError):
            InferenceRequest.from_dict(data)

class TestInferenceResponse:
    def test_inference_response_creation_success(self):
        """Test creating a successful InferenceResponse."""
        resp = InferenceResponse(
            request_id="req-123",
            pr_id="123",
            file_path="test.py",
            line_start=10,
            line_end=20,
            status=InferenceStatus.SUCCESS,
            latency_seconds=1.5
        )
        assert resp.status == InferenceStatus.SUCCESS
        assert resp.latency_seconds == 1.5
        assert resp.detected_bugs == []

    def test_inference_response_creation_error(self):
        """Test creating an error InferenceResponse."""
        resp = InferenceResponse(
            request_id="req-456",
            pr_id="456",
            file_path="main.py",
            line_start=1,
            line_end=5,
            status=InferenceStatus.ERROR,
            error_message="Model timeout"
        )
        assert resp.status == InferenceStatus.ERROR
        assert resp.error_message == "Model timeout"

    def test_inference_response_json_roundtrip(self):
        """Test serializing and deserializing InferenceResponse."""
        original = InferenceResponse(
            request_id="req-789",
            pr_id="789",
            file_path="utils.py",
            line_start=50,
            line_end=60,
            status=InferenceStatus.SUCCESS,
            detected_bugs=[{"line": 52, "severity": "major"}],
            latency_seconds=2.0
        )
        data = original.to_dict()
        reconstructed = InferenceResponse.from_dict(data)

        assert reconstructed.request_id == original.request_id
        assert reconstructed.status == original.status
        assert reconstructed.detected_bugs == original.detected_bugs
        assert reconstructed.latency_seconds == original.latency_seconds

    def test_inference_response_to_json(self):
        """Test JSON serialization string output."""
        resp = InferenceResponse(
            request_id="req-json",
            pr_id="999",
            file_path="json.py",
            line_start=1,
            line_end=1,
            status=InferenceStatus.TIMEOUT
        )
        json_str = resp.to_json()
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["status"] == "timeout"

    def test_inference_response_from_json(self):
        """Test JSON deserialization."""
        json_data = {
            "request_id": "req-json-in",
            "pr_id": "888",
            "file_path": "input.py",
            "line_start": 1,
            "line_end": 10,
            "status": "success",
            "detected_bugs": [],
            "model_name": "test-model"
        }
        resp = InferenceResponse.from_json(json.dumps(json_data))
        assert resp.pr_id == "888"
        assert resp.model_name == "test-model"
        assert resp.status == InferenceStatus.SUCCESS

    def test_inference_response_invalid_status(self):
        """Test that invalid status string raises ValueError."""
        data = {
            "request_id": "req-bad",
            "pr_id": "111",
            "file_path": "bad.py",
            "line_start": 1,
            "line_end": 1,
            "status": "invalid_status"
        }
        with pytest.raises(ValueError):
            InferenceResponse.from_dict(data)