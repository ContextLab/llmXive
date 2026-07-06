"""
Integration tests for the sandbox module.

Tests resource constraints (timeout and memory limits) and basic execution.
"""
import sys
import time
import pytest
from src.evaluation.sandbox import (
    run_code_with_sandbox,
    SandboxTimeoutError,
    SandboxMemoryError,
    TIMEOUT_SECONDS
)


class TestSandboxExecution:
    """Test basic sandbox execution functionality."""
    
    def test_successful_execution(self):
        """Test that simple code executes successfully."""
        code = """
print("Hello, World!")
x = 1 + 1
"""
        result = run_code_with_sandbox(code)
        
        assert result['success'] is True
        assert "Hello, World!" in result['stdout']
        assert result['execution_time'] >= 0
        assert result['timeout'] is False
        assert result['memory_exceeded'] is False
        
    def test_syntax_error(self):
        """Test that syntax errors are captured."""
        code = """
print("Unclosed string
"""
        result = run_code_with_sandbox(code)
        
        assert result['success'] is False
        assert result['error_type'] is not None
        
    def test_runtime_error(self):
        """Test that runtime errors are captured."""
        code = """
x = 1 / 0
"""
        result = run_code_with_sandbox(code)
        
        assert result['success'] is False
        assert "ZeroDivisionError" in result['stderr']


class TestSandboxTimeout:
    """Test sandbox timeout functionality."""
    
    @pytest.mark.skipif(sys.platform == 'win32', reason="Timeout test requires Unix-like system for resource limits")
    def test_timeout_detection(self):
        """Test that infinite loops are detected and timed out."""
        code = """
while True:
    pass
"""
        # Use a short timeout for testing
        result = run_code_with_sandbox(code, timeout=2)
        
        assert result['timeout'] is True
        assert result['success'] is False
        assert result['error_type'] == 'timeout'
        
    def test_quick_computation(self):
        """Test that quick computations complete without timeout."""
        code = """
import time
time.sleep(0.1)
print("Done")
"""
        result = run_code_with_sandbox(code, timeout=5)
        
        assert result['success'] is True
        assert "Done" in result['stdout']
        assert result['timeout'] is False


class TestSandboxMemory:
    """Test sandbox memory limit functionality."""
    
    @pytest.mark.skipif(sys.platform == 'win32', reason="Memory limit test requires Unix-like system for resource limits")
    def test_memory_limit_enforcement(self):
        """Test that excessive memory allocation is blocked."""
        code = """
# Attempt to allocate more than 512MB
large_list = [0] * (1024 * 1024 * 1024)  # 1GB of integers
"""
        result = run_code_with_sandbox(code, timeout=5)
        
        # Should fail due to memory limit
        assert result['success'] is False
        assert result['memory_exceeded'] is True or result['error_type'] in ['memory_limit', 'execution_error']
        
    def test_normal_memory_usage(self):
        """Test that normal memory usage works fine."""
        code = """
# Normal memory usage
data = [i for i in range(10000)]
print(f"Created list with {len(data)} elements")
"""
        result = run_code_with_sandbox(code, timeout=5)
        
        assert result['success'] is True
        assert "Created list" in result['stdout']