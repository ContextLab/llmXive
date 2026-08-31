"""
Graceful Termination Handler for Simulation Runs.

This module implements the logic for mid-simulation shutdown, partial state saving,
and clean exit with specific 'Out of Bounds' reasons (e.g., Memory Explosion).
It is designed to be called by the simulation loop (eco_director) or the CLI
wrapper when resource limits are exceeded.
"""
import os
import sys
import json
import signal
import time
import traceback
from datetime import datetime
from typing import Optional, Dict, Any

from src.data_models import SimulationRun, MetricRecord


class TerminationReason:
    """Constants for termination reasons."""
    MEMORY_EXHAUSTED = "Memory Explosion"
    TIME_LIMIT_EXCEEDED = "Time Limit Exceeded"
    STATE_EXPLOSION = "State Explosion"
    PHYSICS_VIOLATION = "Physics Constraint Violation"
    USER_INTERRUPT = "User Interrupt"
    ERROR = "Error"


class GracefulTerminator:
    """
    Handles graceful shutdown of a simulation run.
    
    Responsibilities:
    - Saves partial state to disk (parquet/json) if applicable.
    - Logs the specific 'Out of Bounds' reason.
    - Exits cleanly without crashing the CI job (exit code 0 or specific code).
    """

    def __init__(self, run_id: str, output_dir: str = "data/raw"):
        self.run_id = run_id
        self.output_dir = output_dir
        self.start_time = datetime.now()
        self.partial_state_path: Optional[str] = None
        self.status_log_path = os.path.join(output_dir, f"{run_id}_status.json")
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

    def _save_partial_state(self, state: Dict[str, Any], reason: str) -> str:
        """
        Saves the current simulation state to a partial file.
        Returns the path to the saved file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.run_id}_partial_{timestamp}.parquet"
        filepath = os.path.join(self.output_dir, filename)
        
        # Note: In a real implementation, 'state' would be a pandas DataFrame
        # or a dict of arrays convertible to parquet. Here we serialize the
        # metadata and a snapshot of the state dict to JSON for safety
        # if pandas is not immediately available or for the termination log.
        # However, the task requires saving 'partial state'. 
        # We will assume the state passed is serializable or convertable.
        
        try:
            import pandas as pd
            if isinstance(state, dict):
                # Try to convert to DataFrame if possible
                # If it's a dict of lists, pd.DataFrame(state) works
                # If it's complex objects, we might need to serialize manually
                # For this implementation, we attempt a direct conversion
                df = pd.DataFrame(state)
                df.to_parquet(filepath, index=False)
            elif isinstance(state, pd.DataFrame):
                state.to_parquet(filepath, index=False)
            else:
                # Fallback to JSON for complex objects
                json_path = filepath.replace(".parquet", ".json")
                with open(json_path, 'w') as f:
                    json.dump(state, f, default=str)
                filepath = json_path
        except Exception as e:
            # If saving fails, log to error but don't crash the termination
            sys.stderr.write(f"Warning: Failed to save partial state: {e}\n")
            filepath = None

        return filepath

    def _write_status_log(self, reason: str, details: Optional[str] = None, 
                          step_count: Optional[int] = None, 
                          metrics: Optional[Dict[str, float]] = None):
        """
        Writes a structured JSON status log to the output directory.
        """
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        status = {
            "run_id": self.run_id,
            "termination_reason": reason,
            "timestamp": datetime.now().isoformat(),
            "elapsed_seconds": elapsed,
            "details": details,
            "partial_state_saved": self.partial_state_path is not None,
            "partial_state_path": self.partial_state_path,
            "exit_code": 0,  # Clean exit for CI
            "step_count": step_count,
            "metrics_snapshot": metrics or {}
        }

        with open(self.status_log_path, 'w') as f:
            json.dump(status, f, indent=2)

    def terminate(self, reason: str, state: Optional[Dict[str, Any]] = None, 
                  details: Optional[str] = None, 
                  step_count: Optional[int] = None,
                  metrics: Optional[Dict[str, float]] = None):
        """
        Executes the graceful termination sequence.
        
        Args:
            reason: The specific reason (e.g., "Memory Explosion").
            state: The current simulation state to save.
            details: Additional context for the log.
            step_count: Number of steps completed.
            metrics: Current metrics snapshot.
        """
        # 1. Save partial state
        if state is not None:
            self.partial_state_path = self._save_partial_state(state, reason)
            if self.partial_state_path:
                sys.stderr.write(f"Partial state saved to: {self.partial_state_path}\n")
            else:
                sys.stderr.write("Failed to save partial state.\n")
        
        # 2. Log the specific reason
        sys.stderr.write(f"TERMINATION: {reason}\n")
        if details:
            sys.stderr.write(f"DETAILS: {details}\n")
        
        # 3. Write status log
        self._write_status_log(reason, details, step_count, metrics)
        sys.stderr.write(f"Status log written to: {self.status_log_path}\n")

        # 4. Exit cleanly (return code 0 to avoid CI crash, or specific code if needed)
        # We use 0 to indicate "handled gracefully" as per requirement "exits cleanly without crashing"
        sys.exit(0)

    def handle_memory_limit(self, current_mb: float, limit_mb: float, 
                            state: Dict[str, Any], step_count: int, 
                            metrics: Dict[str, float]):
        """Convenience method for memory limit termination."""
        details = f"Current memory usage: {current_mb:.2f} MB (Limit: {limit_mb:.2f} MB)"
        self.terminate(
            reason=TerminationReason.MEMORY_EXHAUSTED,
            state=state,
            details=details,
            step_count=step_count,
            metrics=metrics
        )

    def handle_time_limit(self, elapsed_seconds: float, limit_seconds: float,
                          state: Dict[str, Any], step_count: int,
                          metrics: Dict[str, float]):
        """Convenience method for time limit termination."""
        details = f"Elapsed time: {elapsed_seconds:.2f}s (Limit: {limit_seconds:.2f}s)"
        self.terminate(
            reason=TerminationReason.TIME_LIMIT_EXCEEDED,
            state=state,
            details=details,
            step_count=step_count,
            metrics=metrics
        )


def get_memory_usage_mb() -> float:
    """
    Returns the current memory usage of the process in MB.
    Uses /proc/self/status on Linux, falls back to resource on Unix, 
    or returns 0.0 if not available (to avoid crashing on Windows).
    """
    try:
        # Linux specific
        with open('/proc/self/status', 'r') as f:
            for line in f:
                if line.startswith('VmRSS:'):
                    # VmRSS is in kB
                    value = int(line.split()[1])
                    return value / 1024.0
    except (FileNotFoundError, IndexError, ValueError):
        pass

    try:
        # Unix fallback
        import resource
        rusage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in kB on Linux, bytes on macOS? 
        # On macOS it's bytes, on Linux kB. We'll assume kB for Linux and try to detect.
        # For simplicity in this cross-platform snippet, we rely on the /proc method above mostly.
        # If we get here, we might be on macOS where resource.ru_maxrss is bytes.
        # Let's assume kB for now as it's the most common in CI (Linux).
        return rusage.ru_maxrss / 1024.0
    except ImportError:
        pass

    return 0.0


def check_memory_and_log(current_mb: float, limit_mb: float, 
                         run_id: str, state: Dict[str, Any], 
                         step_count: int, metrics: Dict[str, float]):
    """
    Checks if memory usage exceeds limit and triggers termination if so.
    """
    if current_mb > limit_mb:
        terminator = GracefulTerminator(run_id)
        terminator.handle_memory_limit(current_mb, limit_mb, state, step_count, metrics)


def main():
    """
    Standalone test/usage example for the termination handler.
    """
    print("Testing GracefulTerminator...")
    terminator = GracefulTerminator("test-run-123")
    
    # Simulate a state
    sample_state = {
        "step": 100,
        "energy": 50.5,
        "population": 1000
    }
    
    # Trigger a memory limit termination
    terminator.handle_memory_limit(
        current_mb=2048.0, 
        limit_mb=1024.0, 
        state=sample_state, 
        step_count=100,
        metrics={"coherence": 0.9}
    )
    # The script will exit here, so this line won't be reached in a real run
    print("This should not print if termination works.")


if __name__ == "__main__":
    main()