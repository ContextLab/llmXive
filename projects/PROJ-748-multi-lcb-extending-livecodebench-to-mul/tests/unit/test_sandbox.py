"""
Unit tests for the Docker sandbox infrastructure.

Tests:
- Error classification logic
- Sandbox configuration
- Result serialization
"""
import pytest
from unittest.mock import MagicMock, patch

from code.execution.sandbox import (
    ExecutionStatus,
    ErrorClassifier,
    ExecutionResult,
    SandboxConfig,
    LanguageSandbox,
    SandboxManager
)


class TestErrorClassifier:
    """Tests for error classification logic."""

    def test_pass_status(self):
        """Test that successful execution returns PASS."""
        status = ErrorClassifier.classify(0, "", "Hello, World!")
        assert status == ExecutionStatus.PASS

    def test_pass_status_empty_output(self):
        """Test that empty output with exit code 0 returns PASS."""
        status = ErrorClassifier.classify(0, "", "")
        assert status == ExecutionStatus.PASS

    def test_compilation_error_cpp(self):
        """Test C++ compilation error detection."""
        stderr = "error: expected ';' before 'return'"
        status = ErrorClassifier.classify(1, stderr, "")
        assert status == ExecutionStatus.COMPILATION_ERROR

    def test_compilation_error_java(self):
        """Test Java compilation error detection."""
        stderr = "error: cannot find symbol"
        status = ErrorClassifier.classify(1, stderr, "")
        assert status == ExecutionStatus.COMPILATION_ERROR

    def test_syntax_error_python(self):
        """Test Python syntax error detection."""
        stderr = "SyntaxError: invalid syntax"
        status = ErrorClassifier.classify(1, stderr, "")
        assert status == ExecutionStatus.SYNTAX_ERROR

    def test_runtime_error_exception(self):
        """Test runtime error detection via exception."""
        stderr = "Traceback (most recent call last): ValueError: invalid value"
        status = ErrorClassifier.classify(1, stderr, "")
        assert status == ExecutionStatus.RUNTIME_ERROR

    def test_runtime_error_segmentation_fault(self):
        """Test segmentation fault detection."""
        stderr = "Segmentation fault (core dumped)"
        status = ErrorClassifier.classify(139, stderr, "")
        assert status == ExecutionStatus.RUNTIME_ERROR

    def test_timeout_status(self):
        """Test timeout status detection."""
        status = ErrorClassifier.classify(124, "", "")
        assert status == ExecutionStatus.TIMEOUT

    def test_timeout_status_signal_9(self):
        """Test timeout status via signal 9."""
        status = ErrorClassifier.classify(-9, "", "")
        assert status == ExecutionStatus.TIMEOUT

    def test_system_error_out_of_memory(self):
        """Test out of memory detection."""
        stderr = "Out of memory: Kill process"
        status = ErrorClassifier.classify(137, stderr, "")
        assert status == ExecutionStatus.SYSTEM_ERROR

    def test_generic_failure(self):
        """Test generic failure status."""
        status = ErrorClassifier.classify(1, "Unknown error", "")
        assert status == ExecutionStatus.FAIL


class TestExecutionResult:
    """Tests for ExecutionResult dataclass."""

    def test_to_dict(self):
        """Test dictionary conversion."""
        result = ExecutionResult(
            task_id="test_001",
            language="python",
            status=ExecutionStatus.PASS,
            exit_code=0,
            stdout="Hello",
            stderr="",
            duration_ms=100.5
        )

        data = result.to_dict()
        assert data["task_id"] == "test_001"
        assert data["language"] == "python"
        assert data["status"] == "pass"
        assert data["exit_code"] == 0
        assert data["stdout"] == "Hello"
        assert data["stderr"] == ""
        assert data["duration_ms"] == 100.5

    def test_to_dict_with_error(self):
        """Test dictionary conversion with error message."""
        result = ExecutionResult(
            task_id="test_002",
            language="cpp",
            status=ExecutionStatus.COMPILATION_ERROR,
            exit_code=1,
            stdout="",
            stderr="error: expected ';' before 'return'",
            duration_ms=50.0,
            error_message="Compilation failed"
        )

        data = result.to_dict()
        assert data["error_message"] == "Compilation failed"
        assert data["status"] == "compilation_error"


class TestSandboxConfig:
    """Tests for SandboxConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = SandboxConfig()
        assert config.timeout_seconds == 10.0
        assert config.memory_limit_mb == 512
        assert config.cpu_limit == 1.0
        assert config.network_disabled is True
        assert config.read_only is True
        assert config.working_dir == "/workspace"

    def test_custom_values(self):
        """Test custom configuration values."""
        config = SandboxConfig(
            timeout_seconds=30.0,
            memory_limit_mb=1024,
            cpu_limit=2.0,
            network_disabled=False,
            read_only=False,
            working_dir="/app"
        )
        assert config.timeout_seconds == 30.0
        assert config.memory_limit_mb == 1024
        assert config.cpu_limit == 2.0
        assert config.network_disabled is False
        assert config.read_only is False
        assert config.working_dir == "/app"


class TestLanguageSandbox:
    """Tests for LanguageSandbox class."""

    def test_supported_languages(self):
        """Test that supported languages are recognized."""
        supported = ["python", "cpp", "java", "rust", "javascript"]
        for lang in supported:
            # Should not raise
            sandbox = LanguageSandbox.__new__(LanguageSandbox)
            sandbox.language = lang
            assert sandbox.language == lang

    def test_unsupported_language(self):
        """Test that unsupported language raises error."""
        with pytest.raises(ValueError, match="Unsupported language"):
            LanguageSandbox("unknown_lang")


class TestSandboxManager:
    """Tests for SandboxManager class."""

    @patch('code.execution.sandbox.LanguageSandbox')
    def test_get_sandbox_creates_new(self, mock_sandbox_class):
        """Test that get_sandbox creates a new sandbox if not exists."""
        manager = SandboxManager.__new__(SandboxManager)
        manager.sandboxes = {}
        manager.logger = MagicMock()

        mock_instance = MagicMock()
        mock_sandbox_class.return_value = mock_instance

        result = manager.get_sandbox("python")

        assert "python" in manager.sandboxes
        mock_sandbox_class.assert_called_once()

    @patch('code.execution.sandbox.LanguageSandbox')
    def test_get_sandbox_returns_cached(self, mock_sandbox_class):
        """Test that get_sandbox returns cached sandbox if exists."""
        manager = SandboxManager.__new__(SandboxManager)
        manager.sandboxes = {}
        manager.logger = MagicMock()

        mock_instance = MagicMock()
        manager.sandboxes["python"] = mock_instance

        result = manager.get_sandbox("python")

        assert result == mock_instance
        mock_sandbox_class.assert_not_called()

    def test_execute_batch(self):
        """Test batch execution."""
        manager = SandboxManager.__new__(SandboxManager)
        manager.sandboxes = {}
        manager.logger = MagicMock()

        # Mock the execute method
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {"status": "pass"}

        def mock_execute(lang, task_id, source_code, test_case):
            return mock_result

        manager.execute = mock_execute

        tasks = [
            {"language": "python", "task_id": "t1", "source_code": "print(1)", "test_case": {}},
            {"language": "cpp", "task_id": "t2", "source_code": "int main(){}", "test_case": {}}
        ]

        results = manager.execute_batch(tasks)

        assert len(results) == 2
        assert all(r.to_dict() == {"status": "pass"} for r in results)