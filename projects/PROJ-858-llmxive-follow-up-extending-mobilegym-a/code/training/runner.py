"""
Training runner with hard wall-clock time limit enforcement (watchdog).

This module orchestrates training runs and enforces the maximum time limit
defined in FR-004. It uses a watchdog mechanism to ensure that no single
rollout or batch exceeds the allocated time budget.
"""
import json
import os
import signal
import sys
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

# Import from project utilities
from utils.constants import get_coverage_vector_dimensions, get_semantic_proxies
from utils.logging import get_task_logger, log_error, log_task_start, log_task_complete, log_task_failed

logger = get_task_logger("training_runner")

# Configuration constants
MAX_WALL_CLOCK_SECONDS = 21600  # 6 hours as defined in constants.py
BATCH_TIMEOUT_SECONDS = 300     # 5 minutes per batch to prevent single batch deadlock
ROLLOUT_TIMEOUT_SECONDS = 60    # 1 minute per rollout

class TimeoutError(Exception):
    """Custom exception for timeout events."""
    pass

def timeout_handler(signum: int, frame: Any) -> None:
    """Signal handler for timeout events."""
    raise TimeoutError("Operation exceeded time limit")

def run_with_timeout(func: Callable, timeout_seconds: int, *args, **kwargs) -> Any:
    """
    Execute a function with a hard wall-clock timeout using signal alarms.
    
    Args:
        func: The function to execute
        timeout_seconds: Maximum allowed execution time in seconds
        *args: Positional arguments to pass to func
        **kwargs: Keyword arguments to pass to func
        
    Returns:
        The result of func(*args, **kwargs)
        
    Raises:
        TimeoutError: If the function exceeds the timeout
        Exception: Any exception raised by func
    """
    # Set the signal handler and alarm
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    
    try:
        result = func(*args, **kwargs)
        return result
    except TimeoutError:
        raise
    finally:
        # Cancel the alarm and restore the old handler
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

def initialize_training_session(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Initialize a training session with configuration and logging.
    
    Args:
        config: Training configuration dictionary
        
    Returns:
        Session state dictionary
    """
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    start_time = time.time()
    
    session = {
        "session_id": session_id,
        "start_time": start_time,
        "config": config,
        "rollouts_completed": 0,
        "total_steps": 0,
        "successes": 0,
        "failures": 0,
        "timeouts": 0,
        "coverage_vectors": [],
        "scheduler_trace": []
    }
    
    logger.info(f"Training session {session_id} initialized", extra={
        "session_id": session_id,
        "max_time": MAX_WALL_CLOCK_SECONDS
    })
    
    return session

def run_single_rollout(session: Dict[str, Any], task_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a single rollout with timeout enforcement.
    
    Args:
        session: Current training session state
        task_params: Parameters for the task to execute
        
    Returns:
        Rollout result dictionary
    """
    start_time = time.time()
    
    try:
        # Execute rollout with timeout
        result = run_with_timeout(
            execute_rollout_internal,
            ROLLOUT_TIMEOUT_SECONDS,
            task_params,
            session["session_id"]
        )
        
        elapsed = time.time() - start_time
        session["rollouts_completed"] += 1
        session["total_steps"] += result.get("steps", 0)
        
        if result.get("success", False):
            session["successes"] += 1
        else:
            session["failures"] += 1
            
        return {
            "success": True,
            "result": result,
            "elapsed_seconds": elapsed,
            "timed_out": False
        }
        
    except TimeoutError:
        elapsed = time.time() - start_time
        session["timeouts"] += 1
        logger.warning(f"Rollout timed out after {elapsed:.2f}s", extra={
            "task_params": task_params,
            "session_id": session["session_id"]
        })
        
        return {
            "success": False,
            "result": None,
            "elapsed_seconds": elapsed,
            "timed_out": True,
            "error": "Rollout exceeded timeout limit"
        }
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Rollout failed with exception: {str(e)}", extra={
            "task_params": task_params,
            "session_id": session["session_id"],
            "error_type": type(e).__name__
        })
        
        return {
            "success": False,
            "result": None,
            "elapsed_seconds": elapsed,
            "timed_out": False,
            "error": str(e)
        }

def execute_rollout_internal(task_params: Dict[str, Any], session_id: str) -> Dict[str, Any]:
    """
    Internal implementation of a rollout execution.
    
    This is a placeholder for the actual MobileGym rollout logic.
    In a real implementation, this would interface with the MobileGym environment.
    
    Args:
        task_params: Task parameters
        session_id: Current session ID
        
    Returns:
        Rollout result with success status and metrics
    """
    # Placeholder implementation - in real code this would:
    # 1. Initialize MobileGym environment
    # 2. Run the task with the given parameters
    # 3. Collect state coverage vectors
    # 4. Return success/failure and metrics
    
    # Simulating a successful rollout for demonstration
    # (Real implementation would call actual MobileGym API)
    return {
        "success": True,
        "steps": 10,
        "reward": 1.0,
        "state_coverage": [0] * get_coverage_vector_dimensions(),
        "task_id": task_params.get("task_id", "unknown")
    }

def run_training_batch(session: Dict[str, Any], task_batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Execute a batch of rollouts with timeout enforcement per rollout.
    
    Args:
        session: Current training session state
        task_batch: List of task parameters to execute
        
    Returns:
        List of rollout results
    """
    results = []
    batch_start = time.time()
    
    logger.info(f"Starting batch with {len(task_batch)} tasks", extra={
        "batch_size": len(task_batch),
        "session_id": session["session_id"]
    })
    
    for i, task_params in enumerate(task_batch):
        # Check overall session timeout
        elapsed_session = time.time() - session["start_time"]
        if elapsed_session >= MAX_WALL_CLOCK_SECONDS:
            logger.warning(f"Session timeout reached after {elapsed_session:.2f}s", extra={
                "session_id": session["session_id"],
                "elapsed": elapsed_session,
                "max": MAX_WALL_CLOCK_SECONDS
            })
            break
        
        result = run_single_rollout(session, task_params)
        results.append(result)
        
        # Check batch timeout
        elapsed_batch = time.time() - batch_start
        if elapsed_batch >= BATCH_TIMEOUT_SECONDS:
            logger.warning(f"Batch timeout reached after {elapsed_batch:.2f}s", extra={
                "session_id": session["session_id"],
                "elapsed": elapsed_batch,
                "max": BATCH_TIMEOUT_SECONDS,
                "tasks_completed": i + 1
            })
            break
    
    return results

def save_training_results(session: Dict[str, Any], output_path: str) -> None:
    """
    Save training session results to a JSON file.
    
    Args:
        session: Training session state
        output_path: Path to save results
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    results = {
        "session_id": session["session_id"],
        "start_time": datetime.fromtimestamp(session["start_time"]).isoformat(),
        "end_time": datetime.now().isoformat(),
        "duration_seconds": time.time() - session["start_time"],
        "config": session["config"],
        "metrics": {
            "rollouts_completed": session["rollouts_completed"],
            "total_steps": session["total_steps"],
            "successes": session["successes"],
            "failures": session["failures"],
            "timeouts": session["timeouts"],
            "success_rate": session["successes"] / max(session["rollouts_completed"], 1)
        },
        "coverage_vector_dimensions": get_coverage_vector_dimensions(),
        "semantic_proxies": get_semantic_proxies()
    }
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Training results saved to {output_path}", extra={
        "session_id": session["session_id"],
        "output_path": output_path
    })

def main() -> int:
    """
    Main entry point for the training runner.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Initialize training session
        config = {
            "max_wall_clock_seconds": MAX_WALL_CLOCK_SECONDS,
            "batch_timeout_seconds": BATCH_TIMEOUT_SECONDS,
            "rollout_timeout_seconds": ROLLOUT_TIMEOUT_SECONDS,
            "model": "Qwen3-VL-4B-Instruct",
            "quantization": "int8",  # CPU-optimized
            "context_window": 4096
        }
        
        session = initialize_training_session(config)
        
        # Example task batch - in real implementation this would come from scheduler
        task_batch = [
            {"task_id": "task_001", "difficulty": 0.5},
            {"task_id": "task_002", "difficulty": 0.7},
            {"task_id": "task_003", "difficulty": 0.3}
        ]
        
        # Run training batch
        results = run_training_batch(session, task_batch)
        
        # Save results
        output_path = "data/processed/training_results.json"
        save_training_results(session, output_path)
        
        # Log completion
        log_task_complete("training_runner", {
            "session_id": session["session_id"],
            "rollouts_completed": session["rollouts_completed"],
            "success_rate": session["successes"] / max(session["rollouts_completed"], 1)
        })
        
        return 0
        
    except Exception as e:
        log_error("training_runner", str(e), extra={"error_type": type(e).__name__})
        log_task_failed("training_runner", str(e))
        return 1

if __name__ == "__main__":
    sys.exit(main())