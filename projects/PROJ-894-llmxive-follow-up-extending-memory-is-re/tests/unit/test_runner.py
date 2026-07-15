"""
Unit tests for the runner module (timeout and execution logic).
"""
import pytest
import time
from runner import run_task, TimeoutError

def test_run_task_success():
    """Test a task that completes successfully."""
    def quick_task(task_id, context):
        return {"result": "success", "task_id": task_id}
    
    result = run_task(
        task={"id": "t1", "context": {}},
        executor=quick_task,
        timeout_seconds=5
    )
    
    assert result["status"] == "success"
    assert result["data"]["result"] == "success"

def test_run_task_timeout():
    """Test a task that exceeds the timeout."""
    def slow_task(task_id, context):
        time.sleep(10)
        return {"result": "done"}
    
    with pytest.raises(TimeoutError):
        run_task(
            task={"id": "t2", "context": {}},
            executor=slow_task,
            timeout_seconds=1
        )
