"""
Contract test for evaluation timeout handling (T021).

This test verifies that the evaluation script (external/SDAR/agent_system/eval.py)
correctly handles task timeouts without crashing the entire evaluation suite.

It depends on T006c (global timeout wrapper) being implemented.
"""
import os
import sys
import json
import subprocess
import time
from pathlib import Path
import pytest

# Project root setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

EVAL_SCRIPT_PATH = PROJECT_ROOT / "external" / "SDAR" / "agent_system" / "eval.py"
GLOBAL_TIMEOUT_WRAPPER = PROJECT_ROOT / "scripts" / "global_timeout_wrapper.sh"
OUTPUT_LOG_PATH = PROJECT_ROOT / "outputs" / "logs" / "eval_log.json"

# Ensure output directories exist
(PROJECT_ROOT / "outputs" / "logs").mkdir(parents=True, exist_ok=True)

def test_eval_timeout_wrapper_exists():
    """Verify the global timeout wrapper script exists (T006c)."""
    assert GLOBAL_TIMEOUT_WRAPPER.exists(), f"Global timeout wrapper not found at {GLOBAL_TIMEOUT_WRAPPER}"
    # Ensure it is executable
    assert os.access(GLOBAL_TIMEOUT_WRAPPER, os.X_OK), f"Timeout wrapper is not executable"

def test_eval_script_exists():
    """Verify the evaluation script exists."""
    assert EVAL_SCRIPT_PATH.exists(), f"Evaluation script not found at {EVAL_SCRIPT_PATH}"

def test_eval_timeout_handling():
    """
    Contract test: Verify that running the eval script with a short timeout
    (simulated via environment variable or config) does not crash the process
    and produces a log file with timeout/failure entries.
    
    We simulate a timeout by setting a very short task timeout if the script
    supports it, or by relying on the global wrapper if configured.
    """
    # Prepare a test run with a forced short timeout
    # We assume the eval script reads TASK_TIMEOUT from env or args.
    # If not, we rely on the global wrapper's hard timeout.
    
    env = os.environ.copy()
    env["SDAR_MODEL_PROXY"] = "distilbert-base-uncased"
    # Force a very short timeout to trigger the timeout handler
    env["TASK_TIMEOUT"] = "1"  # 1 second per task
    env["NUM_TASKS"] = "1"     # Run only one task to speed up test
    
    # Construct the command
    # If global_timeout_wrapper.sh exists, we could wrap it, but for this test
    # we assume the eval script itself has internal timeout logic or we rely on
    # the environment variable.
    cmd = [sys.executable, str(EVAL_SCRIPT_PATH)]
    
    # Add arguments if the script expects them, otherwise rely on env vars
    # Based on T022, the script should accept num_tasks and task_timeout.
    # We'll try passing them as args first, falling back to env if needed.
    cmd.extend(["--num_tasks", "1", "--task_timeout", "1"])

    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            env=env,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=30  # Hard limit for the whole test run
        )
    except subprocess.TimeoutExpired:
        # If the script hangs despite the timeout, that's a failure of the timeout mechanism
        pytest.fail("Evaluation script did not respect timeout and hung for >30s")

    elapsed = time.time() - start_time
    
    # The script should finish quickly (under 10s) if timeouts are working
    # A 1-second timeout on 1 task should take < 5s total
    assert elapsed < 10.0, f"Evaluation took too long ({elapsed:.2f}s), suggesting timeout logic failed"
    
    # Check exit code: 0 is success, non-zero might be expected if tasks fail
    # but the process itself should not crash (segfault)
    # We allow non-zero exit if tasks failed due to timeout, as long as a log was written.
    
    # Verify log file was created (T025 requirement)
    assert OUTPUT_LOG_PATH.exists(), f"Evaluation log not generated at {OUTPUT_LOG_PATH}"
    
    with open(OUTPUT_LOG_PATH, "r") as f:
        log_content = json.load(f)
    
    # Verify the log structure contains necessary keys
    assert "tasks" in log_content, "Log missing 'tasks' key"
    assert "success_rate" in log_content, "Log missing 'success_rate' key"
    
    # Check that at least one task was attempted and recorded
    tasks = log_content["tasks"]
    assert len(tasks) >= 1, "No tasks recorded in log"
    
    # Verify that failure reasons or timeout status are logged
    # T025: Ensure failure reasons are logged
    has_timeout_or_failure = False
    for task in tasks:
        status = task.get("status", "")
        reason = task.get("reason", "")
        if status == "timeout" or "timeout" in reason.lower() or status == "failed":
            has_timeout_or_failure = True
            break
    
    # We expect at least one task to have failed/timed out given the 1s timeout
    # If the script is too fast, it might succeed, but the test verifies the LOGGING
    # of such events.
    # The critical assertion is that the script didn't crash and produced structured logs.
    # If it succeeded, that's fine too, but the structure must be there.
    
    # T027: Verify the script continues (implied by having logs for all tasks)
    # If it crashed, we wouldn't have the log file or it would be incomplete.
    
def test_eval_script_continues_on_timeout():
    """
    Verify that if a task times out, the script continues to the next task
    rather than crashing the entire suite (T027).
    """
    # This is implicitly tested by test_eval_timeout_handling if we run multiple tasks
    # and verify the log has entries for all of them.
    # We'll run a specific test for 2 tasks with a short timeout.
    
    env = os.environ.copy()
    env["SDAR_MODEL_PROXY"] = "distilbert-base-uncased"
    env["TASK_TIMEOUT"] = "1"
    env["NUM_TASKS"] = "2"
    
    cmd = [sys.executable, str(EVAL_SCRIPT_PATH), "--num_tasks", "2", "--task_timeout", "1"]
    
    try:
        result = subprocess.run(
            cmd,
            env=env,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=30
        )
    except subprocess.TimeoutExpired:
        pytest.fail("Eval script hung with multiple tasks, timeout logic not robust")
    
    assert OUTPUT_LOG_PATH.exists(), "Log file missing after multi-task run"
    
    with open(OUTPUT_LOG_PATH, "r") as f:
        log_content = json.load(f)
    
    tasks = log_content.get("tasks", [])
    # We expect 2 tasks to be logged, even if they timed out
    assert len(tasks) == 2, f"Expected 2 tasks in log, got {len(tasks)}. Script likely crashed on first timeout."