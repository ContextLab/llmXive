"""
Timeout Guard Module for Autonomous Agent Execution.

Enforces hard timeouts per agent run and writes detailed traces to
results/timeout_traces.log for auditability (T042).
"""
import signal
import os
import time
import json
from pathlib import Path
from typing import Optional, Callable, Any, Dict
from datetime import datetime, timezone

# Ensure results directory exists
RESULTS_DIR = Path(__file__).parent.parent.parent / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
TIMEOUT_TRACES_LOG = RESULTS_DIR / "timeout_traces.log"

class TimeoutGuardError(Exception):
    """Custom exception for timeout events."""
    pass

def _timeout_handler(signum, frame):
    """Signal handler for timeout events."""
    raise TimeoutGuardError("Execution exceeded the time limit.")

def run_with_timeout(
    func: Callable,
    args: tuple = (),
    kwargs: dict = None,
    timeout_seconds: int = 3600,
    agent_id: str = "unknown",
    task_id: str = "unknown",
    step_description: str = "unknown_step"
) -> Any:
    """
    Execute a function with a hard timeout and detailed trace logging.
    
    Args:
        func: The function to execute.
        args: Positional arguments for the function.
        kwargs: Keyword arguments for the function.
        timeout_seconds: Maximum allowed execution time in seconds.
        agent_id: Identifier for the agent being executed.
        task_id: Identifier for the task being executed.
        step_description: Description of the current step (e.g., "prompt_generation", "api_call").
        
    Returns:
        The return value of the function if successful.
        
    Raises:
        TimeoutGuardError: If the execution exceeds the timeout.
    """
    if kwargs is None:
        kwargs = {}

    # Set up signal handler (Unix only for signal.alarm)
    # For cross-platform, we would use multiprocessing, but signal is requested for Unix
    original_handler = signal.signal(signal.SIGALRM, _timeout_handler)
    
    try:
        # Set the alarm
        signal.alarm(timeout_seconds)
        
        # Execute the function
        result = func(*args, **kwargs)
        
        # Cancel the alarm if successful
        signal.alarm(0)
        return result
        
    except TimeoutGuardError as e:
        # Log the detailed trace BEFORE raising
        _log_timeout_trace(
            agent_id=agent_id,
            task_id=task_id,
            step=step_description,
            timeout_seconds=timeout_seconds,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        raise e
    finally:
        # Restore original handler
        signal.signal(signal.SIGALRM, original_handler)

def _log_timeout_trace(
    agent_id: str,
    task_id: str,
    step: str,
    timeout_seconds: int,
    timestamp: str
) -> None:
    """
    Write a detailed timeout trace to results/timeout_traces.log.
    
    Format: JSON line per event for easy parsing.
    """
    trace_entry = {
        "timestamp": timestamp,
        "event_type": "TIMEOUT_EXCEEDED",
        "agent_id": agent_id,
        "task_id": task_id,
        "step_reached": step,
        "timeout_limit_seconds": timeout_seconds,
        "message": f"Agent '{agent_id}' timed out at step '{step}' for task '{task_id}' after {timeout_seconds}s."
    }
    
    try:
        with open(TIMEOUT_TRACES_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(trace_entry) + "\n")
    except IOError as e:
        # Fail loudly if we cannot log the trace
        raise RuntimeError(f"Failed to write timeout trace to {TIMEOUT_TRACES_LOG}: {e}") from e

def enforce_timeout(
    func: Callable,
    timeout_seconds: int,
    agent_id: str,
    task_id: str,
    step: str
) -> Callable:
    """
    Decorator factory to enforce timeout on a function call.
    
    Usage:
        @enforce_timeout(timeout_seconds=3600, agent_id="alpha", task_id="123", step="run")
        def my_agent_step():
            ...
    """
    def wrapper(*args, **kwargs):
        return run_with_timeout(
            func=func,
            args=args,
            kwargs=kwargs,
            timeout_seconds=timeout_seconds,
            agent_id=agent_id,
            task_id=task_id,
            step_description=step
        )
    return wrapper