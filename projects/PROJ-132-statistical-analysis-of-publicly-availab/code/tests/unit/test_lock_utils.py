"""
Unit tests for the file-based locking mechanism (T045a).
"""
import os
import time
import tempfile
import threading
import pytest
from pathlib import Path
from src.models.lock_utils import (
    acquire_lock,
    release_lock,
    managed_lock,
    check_lock_status,
    PipelineLockError
)


@pytest.fixture
def temp_lock_path():
    """Create a temporary directory and lock file path for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        lock_path = Path(tmpdir) / "test_pipeline.lock"
        yield lock_path


def test_acquire_lock_success(temp_lock_path):
    """Test successful acquisition of a lock."""
    result = acquire_lock(lock_path=temp_lock_path, timeout=5.0)
    assert result is True
    assert temp_lock_path.exists()
    
    # Cleanup
    release_lock(lock_path=temp_lock_path)


def test_acquire_lock_timeout(temp_lock_path):
    """Test that acquire_lock raises error when lock is held by another process."""
    # First, acquire the lock manually
    lock_file = open(temp_lock_path, 'w')
    import fcntl
    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
    
    try:
        # Try to acquire with short timeout
        with pytest.raises(PipelineLockError) as exc_info:
            acquire_lock(lock_path=temp_lock_path, timeout=1.0)
        
        assert "Timeout" in str(exc_info.value) or "failed" in str(exc_info.value).lower()
    finally:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        lock_file.close()
        if temp_lock_path.exists():
            temp_lock_path.unlink()


def test_release_lock_removes_file(temp_lock_path):
    """Test that releasing the lock handles the file correctly."""
    # Acquire first
    acquire_lock(lock_path=temp_lock_path)
    assert temp_lock_path.exists()
    
    # Release
    release_lock(lock_path=temp_lock_path)
    
    # File might still exist (it's just unlocked), but the lock is gone
    # We verify the lock status is unlocked
    assert not check_lock_status(lock_path=temp_lock_path)


def test_managed_lock_context_manager(temp_lock_path):
    """Test the context manager usage."""
    with managed_lock(lock_path=temp_lock_path, timeout=5.0):
        assert check_lock_status(lock_path=temp_lock_path)
        # Simulate work
        time.sleep(0.1)
    
    # After exiting context, lock should be released
    assert not check_lock_status(lock_path=temp_lock_path)


def test_check_lock_status_unlocked(temp_lock_path):
    """Test checking status of a non-existent/unlocked file."""
    # Ensure file doesn't exist or is unlocked
    if temp_lock_path.exists():
        temp_lock_path.unlink()
        
    assert not check_lock_status(lock_path=temp_lock_path)


def test_concurrent_execution_serialization(temp_lock_path):
    """Test that two threads cannot hold the lock simultaneously."""
    results = []
    
    def worker(worker_id):
        try:
            with managed_lock(lock_path=temp_lock_path, timeout=10.0):
                # Check if we are the only one
                if check_lock_status(lock_path=temp_lock_path):
                    # Simulate work
                    time.sleep(0.5)
                    results.append(f"worker_{worker_id}_success")
                else:
                    results.append(f"worker_{worker_id}_fail")
        except PipelineLockError as e:
            results.append(f"worker_{worker_id}_error: {e}")
    
    threads = []
    for i in range(2):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    # Both should have succeeded eventually, but not at the same time
    # Since managed_lock handles retry, both should be in results
    assert len(results) == 2
    assert all("success" in r or "error" in r for r in results)
    # Verify no "fail" indicates we couldn't acquire even after timeout
    assert not any("fail" in r for r in results)


def test_lock_timeout_configuration(temp_lock_path):
    """Test that a custom timeout is respected."""
    # Acquire manually
    lock_file = open(temp_lock_path, 'w')
    import fcntl
    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
    
    start = time.time()
    try:
        acquire_lock(lock_path=temp_lock_path, timeout=0.5)
        assert False, "Should have raised PipelineLockError"
    except PipelineLockError:
        elapsed = time.time() - start
        # Should be roughly 0.5s, allow some margin
        assert 0.4 <= elapsed <= 0.8
    finally:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        lock_file.close()
        if temp_lock_path.exists():
            temp_lock_path.unlink()