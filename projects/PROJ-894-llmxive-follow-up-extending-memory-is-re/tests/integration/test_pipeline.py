"""
Integration test for the baseline execution pipeline with timeout handling.
"""
import pytest
import os
import sys
import time
import json
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from runner import TimeoutError, TimeoutHandler, run_task
from strategies.full import FullTraversal
import networkx as nx

def test_timeout_handler_context_manager():
    """Test that the TimeoutHandler context manager works correctly."""
    def slow_function():
        time.sleep(2)
        return "done"

    with TimeoutHandler(timeout=0.5):
        try:
            result = slow_function()
            # Should not reach here
            assert False, "Timeout should have been raised"
        except TimeoutError:
            # Expected
            pass

def test_timeout_handler_normal_completion():
    """Test that TimeoutHandler allows normal completion."""
    def fast_function():
        time.sleep(0.1)
        return "done"

    with TimeoutHandler(timeout=2.0):
        result = fast_function()
        assert result == "done"

def test_run_task_with_timeout():
    """Test run_task function with a task that exceeds timeout."""
    def task_that_fails():
        time.sleep(3)
        return {"success": True}

    result = run_task(task_that_fails, timeout=0.5)
    
    assert result["status"] == "timeout"
    assert "error" in result

def test_run_task_success():
    """Test run_task function with a successful task."""
    def task_that_succeeds():
        time.sleep(0.1)
        return {"success": True, "data": "result"}

    result = run_task(task_that_succeeds, timeout=2.0)
    
    assert result["status"] == "success"
    assert result["data"]["success"] is True

def test_full_traversal_integration():
    """Integration test: Run FullTraversal on a generated graph and verify stats."""
    # Create a test graph
    G = nx.DiGraph()
    for i in range(10):
        G.add_edge(i, i+1)
        G.nodes[i]["valid"] = True
    G.nodes[10]["valid"] = True

    def traversal_task():
        strategy = FullTraversal()
        success, path, stats = strategy.traverse(G, 0)
        return {
            "success": success,
            "nodes_visited": stats["nodes_visited"],
            "path_length": len(path)
        }

    result = run_task(traversal_task, timeout=5.0)
    
    assert result["status"] == "success"
    assert result["data"]["success"] is True
    assert result["data"]["nodes_visited"] == 11
    assert result["data"]["path_length"] == 11
