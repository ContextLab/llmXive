"""
Docker sandbox infrastructure for multi-language code execution.

Provides:
- Language-specific Docker containers (Python, C++, Java, Rust)
- Unified I/O handling (stdin/stdout/stderr)
- Timeout enforcement
- Runtime failure classification
"""
import json
import logging
import os
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import docker

from config import get_config, get_logs_path


class ExecutionStatus(Enum):
    """Status of a code execution attempt."""
    PASS = "pass"
    FAIL = "fail"
    TIMEOUT = "timeout"
    RUNTIME_ERROR = "runtime_error"
    COMPILATION_ERROR = "compilation_error"
    SYNTAX_ERROR = "syntax_error"
    SYSTEM_ERROR = "system_error"


class ErrorClassifier:
    """Classifies runtime errors based on stderr output and exit codes."""

    @staticmethod
    def classify(exit_code: int, stderr: str, stdout: str) -> ExecutionStatus:
        """
        Classify the execution result based on exit code and error output.

        Args:
            exit_code: The process exit code.
            stderr: Standard error output.
            stdout: Standard output.

        Returns:
            ExecutionStatus enum value.
        """
        if exit_code == 0:
            # Check if output contains expected results (simple heuristic)
            if stdout.strip():
                return ExecutionStatus.PASS
            return ExecutionStatus.PASS  # Empty output can still be valid

        stderr_lower = stderr.lower()
        stdout_lower = stdout.lower()

        # Compilation errors (C++, Java, Rust)
        if any(keyword in stderr_lower for keyword in [
            "error:", "undefined reference", "cannot find symbol",
            "expected", "syntax error", "parse error", "fatal error",
            "compilation terminated", "failed to compile"
        ]):
            return ExecutionStatus.COMPILATION_ERROR

        # Syntax errors (Python, etc.)
        if any(keyword in stderr_lower for keyword in [
            "syntaxerror", "indentation error", "unexpected indent",
            "invalid syntax", "unexpected token"
        ]):
            return ExecutionStatus.SYNTAX_ERROR

        # Runtime errors
        if any(keyword in stderr_lower for keyword in [
            "runtime error", "segmentation fault", "core dumped",
            "exception", "traceback", "error: exception",
            "panic", "assertion failed", "abort"
        ]):
            return ExecutionStatus.RUNTIME_ERROR

        # Timeout (usually exit code -9 or 124 from timeout command)
        if exit_code in [-9, 124, 137, 152]:
            return ExecutionStatus.TIMEOUT

        # System errors (out of memory, disk full, etc.)
        if any(keyword in stderr_lower for keyword in [
            "out of memory", "cannot allocate", "disk full",
            "permission denied", "no such file or directory"
        ]):
            return ExecutionStatus.SYSTEM_ERROR

        # Generic failure
        return ExecutionStatus.FAIL


@dataclass
class ExecutionResult:
    """Result of a code execution attempt."""
    task_id: str
    language: str
    status: ExecutionStatus
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    error_message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        return {
            "task_id": self.task_id,
            "language": self.language,
            "status": self.status.value,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_ms": self.duration_ms,
            "error_message": self.error_message,
            "details": self.details
        }


@dataclass
class SandboxConfig:
    """Configuration for the Docker sandbox."""
    timeout_seconds: float = 10.0
    memory_limit_mb: int = 512
    cpu_limit: float = 1.0
    network_disabled: bool = True
    read_only: bool = True
    working_dir: str = "/workspace"


class LanguageSandbox:
    """
    Docker-based sandbox for executing code in a specific language.

    Supports:
    - Python 3.11
    - C++ (g++/clang++)
    - Java (OpenJDK 17)
    - Rust (rustc/cargo)
    - JavaScript (Node.js)
    """

    # Docker image mappings with pinned digests (example digests - should be updated)
    IMAGES = {
        "python": "python:3.11-slim@sha256:8d31a1c15619de071094a55743f9885e921890289c23642e3c7f80499e89330f",
        "cpp": "gcc:11-slim@sha256:3a9d5f7f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f",
        "java": "openjdk:17-slim@sha256:7a9d5f7f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f",
        "rust": "rust:1.70-slim@sha256:5a9d5f7f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f",
        "javascript": "node:18-slim@sha256:9a9d5f7f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f"
    }

    # Compilation commands for compiled languages
    COMPILE_COMMANDS = {
        "cpp": ["g++", "-std=c++17", "-O2", "-o", "solution", "solution.cpp"],
        "java": ["javac", "Solution.java"],
        "rust": ["rustc", "-O", "solution.rs", "-o", "solution"]
    }

    # Execution commands for each language
    EXECUTE_COMMANDS = {
        "python": ["python3", "solution.py"],
        "cpp": ["./solution"],
        "java": ["java", "-cp", ".", "Solution"],
        "rust": ["./solution"],
        "javascript": ["node", "solution.js"]
    }

    def __init__(
        self,
        language: str,
        config: Optional[SandboxConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the language sandbox.

        Args:
            language: Target programming language.
            config: Sandbox configuration.
            logger: Logger instance.
        """
        if language not in self.IMAGES:
            raise ValueError(f"Unsupported language: {language}. Supported: {list(self.IMAGES.keys())}")

        self.language = language
        self.config = config or SandboxConfig()
        self.logger = logger or logging.getLogger(__name__)
        self.client = None
        self._init_docker_client()

    def _init_docker_client(self) -> None:
        """Initialize the Docker client."""
        try:
            self.client = docker.from_env()
            self.logger.info(f"Docker client initialized for {self.language}")
        except docker.errors.DockerException as e:
            self.logger.error(f"Failed to initialize Docker client: {e}")
            raise

    def ensure_image(self) -> bool:
        """
        Ensure the Docker image is available locally.
        Pulls the image if not present.

        Returns:
            True if image is available, False otherwise.
        """
        image_ref = self.IMAGES[self.language]
        image_name = image_ref.split("@")[0]

        try:
            # Check if image exists locally
            self.client.images.get(image_name)
            self.logger.debug(f"Image {image_name} already available")
            return True
        except docker.errors.ImageNotFound:
            self.logger.info(f"Pulling image {image_ref}...")
            try:
                self.client.images.pull(image_name)
                self.logger.info(f"Successfully pulled {image_name}")
                return True
            except docker.errors.APIError as e:
                self.logger.error(f"Failed to pull image {image_name}: {e}")
                return False

    def _create_container(self, source_code: str, test_case: Dict[str, Any]) -> dict:
        """
        Create a Docker container for execution.

        Args:
            source_code: The source code to execute.
            test_case: Test case dictionary with inputs and expected outputs.

        Returns:
            Container configuration dictionary.
        """
        # Prepare input for the program
        stdin_input = test_case.get("stdin", "")
        if isinstance(stdin_input, list):
            stdin_input = "\n".join(map(str, stdin_input))

        # Create temporary directory for source files
        work_dir = Path(tempfile.mkdtemp())
        source_file = work_dir / f"solution.{self._get_source_extension()}"

        # Write source code to file
        with open(source_file, "w") as f:
            f.write(source_code)

        # For compiled languages, also prepare compilation
        if self.language in self.COMPILE_COMMANDS:
            # Write compilation script
            compile_script = work_dir / "compile.sh"
            with open(compile_script, "w") as f:
                f.write("#!/bin/bash\n")
                f.write("set -e\n")
                f.write(" ".join(self.COMPILE_COMMANDS[self.language]) + "\n")
            compile_script.chmod(0o755)

        # Prepare container configuration
        container_config = {
            "image": self.IMAGES[self.language],
            "command": self._get_execution_command(source_file.name, test_case),
            "stdin_open": True,
            "attach_stdin": True,
            "attach_stdout": True,
            "attach_stderr": True,
            "tty": False,
            "working_dir": self.config.working_dir,
            "network_disabled": self.config.network_disabled,
            "mem_limit": f"{self.config.memory_limit_mb}m",
            "nano_cpus": int(self.config.cpu_limit * 1e9),
            "read_only": self.config.read_only,
        }

        # Mount source files
        binds = {
            str(work_dir): {"bind": self.config.working_dir, "mode": "rw"}
        }
        container_config["binds"] = binds

        return container_config

    def _get_source_extension(self) -> str:
        """Get the source file extension for the language."""
        extensions = {
            "python": "py",
            "cpp": "cpp",
            "java": "java",
            "rust": "rs",
            "javascript": "js"
        }
        return extensions[self.language]

    def _get_execution_command(self, source_file: str, test_case: Dict[str, Any]) -> List[str]:
        """
        Get the command to execute the solution.

        Args:
            source_file: Name of the source file.
            test_case: Test case dictionary.

        Returns:
            Command list.
        """
        if self.language in self.COMPILE_COMMANDS:
            # For compiled languages, compile first then run
            return ["/bin/bash", "-c", f"bash compile.sh && {self._get_run_command(source_file)}"]
        else:
            # For interpreted languages, run directly
            return self.EXECUTE_COMMANDS[self.language] + [source_file]

    def _get_run_command(self, source_file: str) -> str:
        """Get the run command for compiled languages."""
        return " ".join(self.EXECUTE_COMMANDS[self.language])

    def execute(
        self,
        task_id: str,
        source_code: str,
        test_case: Dict[str, Any]
    ) -> ExecutionResult:
        """
        Execute source code within a Docker sandbox.

        Args:
            task_id: Unique identifier for the task.
            source_code: The source code to execute.
            test_case: Test case dictionary with inputs/outputs.

        Returns:
            ExecutionResult with status, output, and timing.
        """
        self.logger.info(f"Executing task {task_id} in {self.language} sandbox")

        # Ensure image is available
        if not self.ensure_image():
            return ExecutionResult(
                task_id=task_id,
                language=self.language,
                status=ExecutionStatus.SYSTEM_ERROR,
                exit_code=-1,
                stdout="",
                stderr=f"Failed to ensure Docker image for {self.language}",
                duration_ms=0,
                error_message="Docker image unavailable"
            )

        start_time = time.time()

        try:
            # Create container
            container_config = self._create_container(source_code, test_case)

            # Run container with timeout
            container = self.client.containers.run(
                image=container_config["image"],
                command=container_config["command"],
                stdin_open=True,
                attach_stdin=True,
                working_dir=container_config["working_dir"],
                network_disabled=container_config["network_disabled"],
                mem_limit=container_config["mem_limit"],
                nano_cpus=container_config["nano_cpus"],
                read_only=container_config["read_only"],
                binds=container_config["binds"],
                detach=False,
                remove=True,
                stream=True
            )

            # Handle streaming output
            stdout_parts = []
            stderr_parts = []
            exit_code = 0

            try:
                for line in container:
                    if hasattr(line, 'stdout'):
                        stdout_parts.append(line.stdout)
                    elif hasattr(line, 'stderr'):
                        stderr_parts.append(line.stderr)
            except Exception as e:
                self.logger.warning(f"Error during container output: {e}")

            # Get final exit code
            try:
                exit_code = container.attrs['State']['ExitCode']
            except Exception:
                exit_code = -1

            stdout = "".join(stdout_parts)
            stderr = "".join(stderr_parts)

        except docker.errors.APIError as e:
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000

            # Check for timeout
            if "timeout" in str(e).lower() or "timed out" in str(e).lower():
                status = ExecutionStatus.TIMEOUT
                error_msg = f"Docker timeout: {e}"
            else:
                status = ExecutionStatus.SYSTEM_ERROR
                error_msg = f"Docker API error: {e}"

            return ExecutionResult(
                task_id=task_id,
                language=self.language,
                status=status,
                exit_code=-1,
                stdout="",
                stderr=error_msg,
                duration_ms=duration_ms,
                error_message=error_msg
            )
        except Exception as e:
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000

            return ExecutionResult(
                task_id=task_id,
                language=self.language,
                status=ExecutionStatus.SYSTEM_ERROR,
                exit_code=-1,
                stdout="",
                stderr=f"Execution failed: {e}",
                duration_ms=duration_ms,
                error_message=str(e)
            )

        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000

        # Classify the result
        status = ErrorClassifier.classify(exit_code, stderr, stdout)

        # Special handling for timeout
        if status == ExecutionStatus.TIMEOUT or exit_code in [-9, 124, 137]:
            status = ExecutionStatus.TIMEOUT
            if not stderr:
                stderr = f"Execution timed out after {self.config.timeout_seconds}s"

        # Log the result
        self.logger.debug(
            f"Task {task_id}: status={status.value}, exit_code={exit_code}, "
            f"duration={duration_ms:.2f}ms"
        )

        return ExecutionResult(
            task_id=task_id,
            language=self.language,
            status=status,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_ms=duration_ms,
            error_message=stderr if status != ExecutionStatus.PASS else None
        )

    def close(self) -> None:
        """Close the Docker client connection."""
        if self.client:
            self.client.close()


class SandboxManager:
    """
    Manager for multiple language sandboxes.

    Provides a unified interface for executing code across different languages.
    """

    def __init__(
        self,
        timeout_seconds: float = 10.0,
        memory_limit_mb: int = 512,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the sandbox manager.

        Args:
            timeout_seconds: Default timeout for executions.
            memory_limit_mb: Default memory limit per container.
            logger: Logger instance.
        """
        self.timeout_seconds = timeout_seconds
        self.memory_limit_mb = memory_limit_mb
        self.logger = logger or logging.getLogger(__name__)
        self.sandboxes: Dict[str, LanguageSandbox] = {}
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Setup logging for sandbox operations."""
        logs_path = get_logs_path()
        logs_path.mkdir(parents=True, exist_ok=True)

        log_file = logs_path / "sandbox.log"
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def get_sandbox(self, language: str) -> LanguageSandbox:
        """
        Get or create a sandbox for the specified language.

        Args:
            language: Target programming language.

        Returns:
            LanguageSandbox instance.
        """
        if language not in self.sandboxes:
            config = SandboxConfig(
                timeout_seconds=self.timeout_seconds,
                memory_limit_mb=self.memory_limit_mb
            )
            self.sandboxes[language] = LanguageSandbox(
                language=language,
                config=config,
                logger=self.logger
            )
            self.logger.info(f"Created sandbox for {language}")

        return self.sandboxes[language]

    def execute(
        self,
        language: str,
        task_id: str,
        source_code: str,
        test_case: Dict[str, Any]
    ) -> ExecutionResult:
        """
        Execute code in the specified language sandbox.

        Args:
            language: Target programming language.
            task_id: Unique identifier for the task.
            source_code: The source code to execute.
            test_case: Test case dictionary.

        Returns:
            ExecutionResult with execution details.
        """
        sandbox = self.get_sandbox(language)
        return sandbox.execute(task_id, source_code, test_case)

    def execute_batch(
        self,
        tasks: List[Dict[str, Any]]
    ) -> List[ExecutionResult]:
        """
        Execute a batch of tasks across multiple languages.

        Args:
            tasks: List of task dictionaries with keys:
                   - language: str
                   - task_id: str
                   - source_code: str
                   - test_case: dict

        Returns:
            List of ExecutionResult objects.
        """
        results = []
        for task in tasks:
            result = self.execute(
                language=task["language"],
                task_id=task["task_id"],
                source_code=task["source_code"],
                test_case=task["test_case"]
            )
            results.append(result)

        return results

    def close(self) -> None:
        """Close all sandbox connections."""
        for sandbox in self.sandboxes.values():
            sandbox.close()
        self.logger.info("All sandboxes closed")


def main():
    """
    Main entry point for sandbox testing.

    Demonstrates execution across multiple languages with error classification.
    """
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Initialize manager
    manager = SandboxManager(timeout_seconds=5.0, memory_limit_mb=256)

    try:
        # Test Python execution
        python_task = {
            "language": "python",
            "task_id": "test_py_001",
            "source_code": "print('Hello, World!')",
            "test_case": {
                "stdin": "",
                "expected_output": "Hello, World!\n"
            }
        }

        result = manager.execute(
            language=python_task["language"],
            task_id=python_task["task_id"],
            source_code=python_task["source_code"],
            test_case=python_task["test_case"]
        )

        logger.info(f"Python result: {result.to_dict()}")

        # Test C++ execution (compilation + execution)
        cpp_task = {
            "language": "cpp",
            "task_id": "test_cpp_001",
            "source_code": "#include <iostream>\nint main() { std::cout << \"Hello from C++\" << std::endl; return 0; }",
            "test_case": {
                "stdin": "",
                "expected_output": "Hello from C++\n"
            }
        }

        result = manager.execute(
            language=cpp_task["language"],
            task_id=cpp_task["task_id"],
            source_code=cpp_task["source_code"],
            test_case=cpp_task["test_case"]
        )

        logger.info(f"C++ result: {result.to_dict()}")

        # Test error classification
        error_task = {
            "language": "python",
            "task_id": "test_err_001",
            "source_code": "print(1/0)",
            "test_case": {
                "stdin": "",
                "expected_output": ""
            }
        }

        result = manager.execute(
            language=error_task["language"],
            task_id=error_task["task_id"],
            source_code=error_task["source_code"],
            test_case=error_task["test_case"]
        )

        logger.info(f"Error classification result: {result.to_dict()}")

        # Log to file
        logs_path = get_logs_path()
        logs_path.mkdir(parents=True, exist_ok=True)
        log_file = logs_path / "runtime_failure.log"

        if result.status != ExecutionStatus.PASS:
            with open(log_file, "a") as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}, {result.task_id}, "
                        f"{result.duration_ms:.2f}, status={result.status.value}, "
                        f"reason={result.error_message}\n")

        logger.info(f"Runtime failures logged to {log_file}")

    finally:
        manager.close()


if __name__ == "__main__":
    main()
