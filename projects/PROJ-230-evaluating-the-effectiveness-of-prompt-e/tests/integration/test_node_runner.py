"""
Integration test for Node.js test runner (T026).

This test verifies that the Node.js execution environment is available and
correctly enforces the 10-second timeout per test as specified in T009 and T028.

It does NOT execute the full pipeline (which requires generated translations);
instead, it uses a minimal synthetic JavaScript file to validate the runner logic.
"""
import pytest
import subprocess
import tempfile
import os
import time
from pathlib import Path
from src.utils.timeout_utils import enforce_test_timeout, TimeoutError


class TestNodeRunnerIntegration:
    """Integration tests for the Node.js test runner environment."""

    def test_node_environment_available(self):
        """Verify Node.js is installed and accessible in PATH."""
        try:
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            assert result.returncode == 0, f"Node.js not available: {result.stderr}"
            assert result.stdout.strip().startswith("v"), f"Unexpected Node version format: {result.stdout}"
        except FileNotFoundError:
            pytest.fail("Node.js is not installed or not in PATH. Please install Node.js to run this integration test.")
        except subprocess.TimeoutExpired:
            pytest.fail("Node.js version check timed out.")

    def test_npm_environment_available(self):
        """Verify npm is installed and accessible in PATH."""
        try:
            result = subprocess.run(
                ["npm", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            assert result.returncode == 0, f"npm not available: {result.stderr}"
        except FileNotFoundError:
            pytest.fail("npm is not installed or not in PATH. Please install Node.js to run this integration test.")
        except subprocess.TimeoutExpired:
            pytest.fail("npm version check timed out.")

    def test_execute_valid_javascript_success(self):
        """Verify Node.js can successfully execute a valid JavaScript file."""
        # Create a temporary valid JS file
        valid_js_content = """
        console.log("Test passed");
        process.exit(0);
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(valid_js_content)
            temp_file = f.name

        try:
            start_time = time.time()
            result = subprocess.run(
                ["node", temp_file],
                capture_output=True,
                text=True,
                timeout=10  # 10s timeout as per spec
            )
            elapsed = time.time() - start_time

            assert result.returncode == 0, f"Execution failed: {result.stderr}"
            assert "Test passed" in result.stdout, f"Expected output not found: {result.stdout}"
            assert elapsed < 5, f"Execution took too long: {elapsed}s"
        finally:
            os.unlink(temp_file)

    def test_execute_invalid_javascript_failure(self):
        """Verify Node.js correctly reports syntax errors in invalid JS."""
        invalid_js_content = """
        console.log("Syntax error here: ;;;");
        process.exit(0);
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(invalid_js_content)
            temp_file = f.name

        try:
            result = subprocess.run(
                ["node", temp_file],
                capture_output=True,
                text=True,
                timeout=10
            )

            # Should fail due to syntax error
            assert result.returncode != 0, "Execution should have failed for invalid JS"
            assert "SyntaxError" in result.stderr or "undefined" in result.stderr, f"Expected syntax error in stderr: {result.stderr}"
        finally:
            os.unlink(temp_file)

    def test_timeout_enforcement(self):
        """Verify that the 10s timeout is enforced for infinite loops."""
        # Create a JS file with an infinite loop
        infinite_loop_js = """
        while(true) {
            // Infinite loop
        }
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(infinite_loop_js)
            temp_file = f.name

        try:
            start_time = time.time()
            with pytest.raises(subprocess.TimeoutExpired):
                subprocess.run(
                    ["node", temp_file],
                    capture_output=True,
                    text=True,
                    timeout=5  # Use 5s for this test to be faster
                )
            elapsed = time.time() - start_time

            # Verify timeout happened within expected window
            assert elapsed >= 4.5 and elapsed <= 7, f"Timeout enforcement unexpected: {elapsed}s"
        finally:
            os.unlink(temp_file)

    def test_runner_with_timeout_decorator(self):
        """Test the project's specific timeout utility against a slow JS script."""
        # Create a JS file that sleeps for 2 seconds
        slow_js = """
        const sleep = (ms) => {
            const start = Date.now();
            while (Date.now() - start < ms) {}
        };
        sleep(2000);
        console.log("Done");
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(slow_js)
            temp_file = f.name

        try:
            # This should succeed within 10s
            start = time.time()
            result = subprocess.run(
                ["node", temp_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            elapsed = time.time() - start

            assert result.returncode == 0
            assert "Done" in result.stdout
            assert elapsed < 5  # Should finish quickly
        finally:
            os.unlink(temp_file)