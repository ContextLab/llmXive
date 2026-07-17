import unittest
import time
import os
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile

# Import the module under test
# Adjust import path based on project structure relative to tests/
sys.path.insert(0, str(Path(__file__).parent.parent))
from code.error_handling import (
    InferenceTimeoutError,
    DatasetDownloadError,
    RetryExhaustedError,
    retry_with_backoff,
    timeout_context,
    enforce_inference_timeout,
    safe_download_with_retry,
    compute_sha256
)

class TestCustomExceptions(unittest.TestCase):
    def test_inference_timeout_error(self):
        with self.assertRaises(InferenceTimeoutError):
            raise InferenceTimeoutError("Inference timed out")

    def test_dataset_download_error(self):
        with self.assertRaises(DatasetDownloadError):
            raise DatasetDownloadError("Download failed")

    def test_retry_exhausted_error(self):
        with self.assertRaises(RetryExhaustedError):
            raise RetryExhaustedError("Retries exhausted")

class TestRetryWithBackoff(unittest.TestCase):
    @retry_with_backoff(max_retries=2, initial_delay=0.1, exceptions=(ValueError,))
    def failing_function(self):
        if not hasattr(self, 'call_count'):
            self.call_count = 0
        self.call_count += 1
        if self.call_count < 3:
            raise ValueError("Simulated failure")
        return "Success"

    def test_retry_success(self):
        result = self.failing_function()
        self.assertEqual(result, "Success")
        self.assertEqual(self.call_count, 3)

    @retry_with_backoff(max_retries=1, initial_delay=0.01, exceptions=(ValueError,))
    def permanently_failing_function(self):
        raise ValueError("Always fails")

    def test_retry_exhausted(self):
        with self.assertRaises(RetryExhaustedError):
            self.permanently_failing_function()

class TestTimeoutContext(unittest.TestCase):
    def test_timeout_on_slow_function(self):
        with self.assertRaises(InferenceTimeoutError):
            with timeout_context(0.5, "Test Op"):
                time.sleep(1.0)

    def test_no_timeout_on_fast_function(self):
        start = time.time()
        with timeout_context(2.0, "Test Op"):
            time.sleep(0.1)
        elapsed = time.time() - start
        self.assertLess(elapsed, 1.0)

class TestEnforceInferenceTimeout(unittest.TestCase):
    @enforce_inference_timeout(timeout_seconds=0.5)
    def slow_function(self):
        time.sleep(1.0)
        return "Done"

    def test_timeout_decorator(self):
        with self.assertRaises(InferenceTimeoutError):
            self.slow_function()

    @enforce_inference_timeout(timeout_seconds=2.0)
    def fast_function(self):
        time.sleep(0.1)
        return "Done"

    def test_no_timeout_decorator(self):
        result = self.fast_function()
        self.assertEqual(result, "Done")

class TestComputeSha256(unittest.TestCase):
    def test_compute_sha256(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test data")
            tmp_path = tmp.name
        
        try:
            hash_val = compute_sha256(tmp_path)
            self.assertEqual(len(hash_val), 64) # SHA256 hex length
        finally:
            os.unlink(tmp_path)

if __name__ == '__main__':
    unittest.main()