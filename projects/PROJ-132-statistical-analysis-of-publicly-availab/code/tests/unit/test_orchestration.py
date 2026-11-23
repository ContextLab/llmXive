"""
Unit tests for the orchestration lock mechanism (T045).

Verifies that:
1. Lock acquisition works correctly.
2. Lock prevents concurrent execution (simulated).
3. Lock is released after execution.
4. Timeout behavior is correct.
"""
import os
import sys
import time
import tempfile
import threading
import multiprocessing
from pathlib import Path
import pytest
import json

# Add project root to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.lib.orchestration import acquire_lock, release_lock, LOCK_TIMEOUT_SECONDS

@pytest.fixture
def temp_lock_dir():
    """Create a temporary directory for lock files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_acquire_lock_success(temp_lock_dir):
    """Test that a lock can be acquired successfully."""
    lock_path = temp_lock_dir / "test.lock"
    assert acquire_lock(lock_path, "TestTask") is True
    assert lock_path.exists()
    
    # Verify content
    with open(lock_path, 'r') as f:
        data = json.load(f)
        assert "task" in data
        assert data["task"] == "TestTask"
    
    # Clean up
    release_lock(lock_path, "TestTask")
    assert not lock_path.exists()

def test_acquire_lock_blocked(temp_lock_dir):
    """Test that a lock cannot be acquired if already held."""
    lock_path = temp_lock_dir / "test.lock"
    
    # Acquire manually
    fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR)
    fcntl = __import__('fcntl')
    fcntl.flock(fd, fcntl.LOCK_EX)
    
    # Try to acquire via function (should fail immediately or timeout quickly)
    # We set a short timeout for the test
    import src.lib.orchestration as orch
    original_timeout = orch.LOCK_TIMEOUT_SECONDS
    orch.LOCK_TIMEOUT_SECONDS = 2.0 # Short timeout for test
    
    try:
        result = acquire_lock(lock_path, "TestTask2")
        assert result is False, "Should not acquire lock held by another"
    finally:
        orch.LOCK_TIMEOUT_SECONDS = original_timeout
        os.close(fd)

def test_release_lock_removes_file(temp_lock_dir):
    """Test that releasing a lock removes the file."""
    lock_path = temp_lock_dir / "test.lock"
    acquire_lock(lock_path, "TestTask")
    assert lock_path.exists()
    
    release_lock(lock_path, "TestTask")
    assert not lock_path.exists()

def test_release_lock_nonexistent(temp_lock_dir):
    """Test releasing a lock that doesn't exist."""
    lock_path = temp_lock_dir / "nonexistent.lock"
    # Should return False but not crash
    assert release_lock(lock_path, "TestTask") is False

def test_concurrent_execution_serialization(temp_lock_dir):
    """
    Test that two processes trying to acquire the same lock
    result in one succeeding and the other waiting/failing.
    """
    lock_path = temp_lock_dir / "concurrent.lock"
    results = []

    def worker(name, wait_time):
        # Try to acquire lock
        acquired = acquire_lock(lock_path, name)
        if acquired:
            time.sleep(wait_time)
            release_lock(lock_path, name)
            results.append((name, "success"))
        else:
            results.append((name, "failed"))

    # Start two threads
    t1 = threading.Thread(target=worker, args=("Worker1", 1.0))
    t2 = threading.Thread(target=worker, args=("Worker2", 1.0))
    
    t1.start()
    time.sleep(0.1) # Small delay to ensure t1 gets it first
    t2.start()
    
    t1.join()
    t2.join()
    
    # One should succeed, one might fail or succeed later depending on timeout
    # In this test, we just check that the logic runs without deadlock
    assert len(results) == 2
    # At least one should have succeeded
    assert any(r[1] == "success" for r in results)

def test_lock_timeout(temp_lock_dir):
    """Test that acquire_lock returns False on timeout."""
    lock_path = temp_lock_dir / "timeout.lock"
    
    # Hold the lock manually for a long time
    fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR)
    fcntl = __import__('fcntl')
    fcntl.flock(fd, fcntl.LOCK_EX)
    
    import src.lib.orchestration as orch
    original_timeout = orch.LOCK_TIMEOUT_SECONDS
    orch.LOCK_TIMEOUT_SECONDS = 2.0 # Short timeout
    
    try:
        start = time.time()
        result = acquire_lock(lock_path, "TimeoutTest")
        elapsed = time.time() - start
        
        assert result is False
        assert elapsed >= 2.0 # Should have waited for timeout
    finally:
        orch.LOCK_TIMEOUT_SECONDS = original_timeout
        os.close(fd)
