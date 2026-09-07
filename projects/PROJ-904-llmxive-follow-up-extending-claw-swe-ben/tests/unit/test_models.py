"""
Unit tests for data model classes.
"""
import pytest
from datetime import datetime
from models.task_instance import TaskInstance, TaskStatus
from models.context_config import ContextConfiguration, StrategyType
from models.execution_result import ExecutionResult, ExecutionStatus, FailureCategory
from utils.logger import setup_logger

logger = setup_logger(__name__)


class TestTaskInstance:
    def test_task_instance_init(self):
        """Test basic initialization of TaskInstance."""
        instance = TaskInstance(
            instance_id="test-001",
            issue_description="Fix bug in parser",
            target_file="parser.py",
            repository="test/repo",
            version="1.0.0"
        )
        assert instance.instance_id == "test-001"
        assert instance.status == TaskStatus.PENDING
        assert instance.created_at is not None

    def test_task_instance_to_dict(self):
        """Test serialization of TaskInstance."""
        instance = TaskInstance(
            instance_id="test-002",
            issue_description="Another issue",
            target_file="main.py",
            repository="test/repo2"
        )
        data = instance.to_dict()
        assert data["instance_id"] == "test-002"
        assert data["status"] == "pending"

    def test_task_instance_from_dict(self):
        """Test deserialization of TaskInstance."""
        data = {
            "instance_id": "test-003",
            "issue_description": "Deserialized issue",
            "target_file": "utils.py",
            "repository": "test/repo3",
            "version": "2.0.0",
            "status": "completed"
        }
        instance = TaskInstance.from_dict(data)
        assert instance.instance_id == "test-003"
        assert instance.status == TaskStatus.COMPLETED


class TestContextConfiguration:
    def test_context_config_init(self):
        """Test basic initialization of ContextConfiguration."""
        config = ContextConfiguration(
            strategy=StrategyType.BASELINE,
            max_tokens=4096,
            context_files=["file1.py", "file2.py"]
        )
        assert config.strategy == StrategyType.BASELINE
        assert config.max_tokens == 4096
        assert len(config.context_files) == 2

    def test_context_config_to_dict(self):
        """Test serialization of ContextConfiguration."""
        config = ContextConfiguration(
            strategy=StrategyType.TFIDF,
            max_tokens=2048,
            context_files=["code.py"]
        )
        data = config.to_dict()
        assert data["strategy"] == "tfidf"
        assert data["max_tokens"] == 2048

    def test_context_config_from_dict(self):
        """Test deserialization of ContextConfiguration."""
        data = {
            "strategy": "diff_aware",
            "max_tokens": 8192,
            "context_files": ["a.py", "b.py", "c.py"],
            "metadata": {"source": "test"}
        }
        config = ContextConfiguration.from_dict(data)
        assert config.strategy == StrategyType.DIFF_AWARE
        assert config.max_tokens == 8192


class TestExecutionResult:
    def test_execution_result_init(self):
        """Test basic initialization of ExecutionResult."""
        result = ExecutionResult(
            instance_id="inst-001",
            model_id="llama-3-1b",
            strategy=StrategyType.BASELINE,
            status=ExecutionStatus.SUCCESS,
            pass_label=True
        )
        assert result.instance_id == "inst-001"
        assert result.model_id == "llama-3-1b"
        assert result.strategy == StrategyType.BASELINE
        assert result.status == ExecutionStatus.SUCCESS
        assert result.pass_label is True
        assert result.created_at is not None

    def test_execution_result_to_dict(self):
        """Test serialization of ExecutionResult."""
        result = ExecutionResult(
            instance_id="inst-002",
            model_id="llama-3-7b",
            strategy=StrategyType.TFIDF,
            status=ExecutionStatus.SUCCESS,
            pass_label=True,
            generated_text="def fix(): pass",
            execution_time_ms=123.45
        )
        data = result.to_dict()
        assert data["instance_id"] == "inst-002"
        assert data["model_id"] == "llama-3-7b"
        assert data["strategy"] == "tfidf"
        assert data["status"] == "success"
        assert data["pass_label"] is True
        assert data["generated_text"] == "def fix(): pass"
        assert data["execution_time_ms"] == 123.45

    def test_execution_result_from_dict(self):
        """Test deserialization of ExecutionResult."""
        data = {
            "instance_id": "inst-003",
            "model_id": "llama-3-1b",
            "strategy": "diff_aware",
            "status": "error",
            "pass_label": False,
            "error_message": "Timeout occurred",
            "execution_time_ms": 5000.0,
            "failure_category": "timeout"
        }
        result = ExecutionResult.from_dict(data)
        assert result.instance_id == "inst-003"
        assert result.model_id == "llama-3-1b"
        assert result.strategy == StrategyType.DIFF_AWARE
        assert result.status == ExecutionStatus.ERROR
        assert result.pass_label is False
        assert result.error_message == "Timeout occurred"
        assert result.failure_category == FailureCategory.TIMEOUT

    def test_execution_result_to_json(self):
        """Test JSON serialization of ExecutionResult."""
        result = ExecutionResult(
            instance_id="inst-004",
            model_id="test-model",
            strategy=StrategyType.BASELINE,
            status=ExecutionStatus.SUCCESS,
            pass_label=True
        )
        json_str = result.to_json()
        assert "inst-004" in json_str
        assert "baseline" in json_str
        assert "success" in json_str

    def test_execution_result_checksum(self):
        """Test checksum calculation for integrity verification."""
        result1 = ExecutionResult(
            instance_id="inst-005",
            model_id="m1",
            strategy=StrategyType.BASELINE,
            status=ExecutionStatus.SUCCESS,
            pass_label=True
        )
        result2 = ExecutionResult(
            instance_id="inst-005",
            model_id="m1",
            strategy=StrategyType.BASELINE,
            status=ExecutionStatus.SUCCESS,
            pass_label=True
        )
        # Same core data should produce same checksum
        assert result1.calculate_checksum() == result2.calculate_checksum()

        # Different core data should produce different checksum
        result3 = ExecutionResult(
            instance_id="inst-006",
            model_id="m1",
            strategy=StrategyType.BASELINE,
            status=ExecutionStatus.SUCCESS,
            pass_label=True
        )
        assert result1.calculate_checksum() != result3.calculate_checksum()

    def test_execution_result_with_metadata(self):
        """Test ExecutionResult with custom metadata."""
        result = ExecutionResult(
            instance_id="inst-007",
            model_id="m1",
            strategy=StrategyType.SEMANTIC,
            status=ExecutionStatus.SUCCESS,
            pass_label=True,
            metadata={"tokens_used": 1500, "temperature": 0.7}
        )
        assert result.metadata["tokens_used"] == 1500
        assert result.metadata["temperature"] == 0.7

    def test_execution_result_partial_status(self):
        """Test ExecutionResult with PARTIAL status."""
        result = ExecutionResult(
            instance_id="inst-008",
            model_id="m1",
            strategy=StrategyType.BASELINE,
            status=ExecutionStatus.PARTIAL,
            pass_label=None,
            error_message="Incomplete generation"
        )
        assert result.status == ExecutionStatus.PARTIAL
        assert result.pass_label is None