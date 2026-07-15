"""
Integration tests for the end-to-end execution pipeline.
"""
import pytest
import time
from runner import run_task, TimeoutHandler, TimeoutError
from strategies.full import FullTraversal
from graph_utils import build_memory_graph

def dummy_task_func(context):
    """A dummy task that simulates work."""
    time.sleep(0.1)
    return {"status": "success", "result": 42}

def test_run_task_success():
    """Test that a successful task completes and returns result."""
    result = run_task("test_task", dummy_task_func, {"input": "data"})
    assert result["status"] == "success"
    assert result["result"] == 42

def test_run_task_timeout():
    """Test that a task exceeding timeout raises TimeoutError."""
    def slow_task(context):
        time.sleep(2)
        return {"status": "success"}

    with pytest.raises(TimeoutError):
        run_task("slow_task", slow_task, {}, timeout=0.5)

def test_timeout_handler_logging(tmp_path):
    """Test that the timeout handler logs events correctly."""
    log_file = tmp_path / "test.log"
    handler = TimeoutHandler(log_file=str(log_file))
    
    try:
        def very_slow_task(context):
            time.sleep(5)
        run_task("very_slow", very_slow_task, {}, timeout=0.1, timeout_handler=handler)
    except TimeoutError:
        pass

    assert log_file.exists()
    content = log_file.read_text()
    assert "Timeout" in content or "timeout" in content.lower()
