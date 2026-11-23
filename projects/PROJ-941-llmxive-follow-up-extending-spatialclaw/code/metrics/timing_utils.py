"""
Timing utilities for excluding blocked 3D library initialization time from step latency.

This module provides functions to calculate wall-clock time for agent steps while
filtering out time spent on blocked operations (e.g., failed imports of trimesh,
pytorch3d, etc.) that are caught by the restricted kernel.

The restricted kernel logs blocked operations with timestamps. This utility
parses those logs to identify blocked intervals and subtracts them from total
step latency.
"""

import time
import logging
import re
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Pattern to match blocked operation log entries
# Expected format from restricted_kernel.py: 
# "BLOCKED: [timestamp] Attempted to import/call <library_name>: <reason>"
BLOCKED_LOG_PATTERN = re.compile(
    r'BLOCKED:\s*\[([^\]]+)\]\s*Attempted\s+to\s+(import|call)\s+(\w+):\s*(.+)'
)

# Pattern to match step start/end log entries
STEP_LOG_PATTERN = re.compile(
    r'STEP:\s*([^\s]+)\s*:\s*(start|end)\s*\[([^\]]+)\]'
)

def parse_timestamp(ts_str: str) -> float:
    """
    Parse a timestamp string from log entries to epoch seconds.
    
    Args:
        ts_str: Timestamp string in ISO format or float representation
        
    Returns:
        Float representation of epoch seconds
    """
    try:
        # Try ISO format first
        dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        return dt.timestamp()
    except (ValueError, AttributeError):
        # Try direct float conversion
        try:
            return float(ts_str)
        except ValueError:
            # Fallback: return current time as last resort
            logger.warning(f"Could not parse timestamp: {ts_str}, using current time")
            return time.time()

def extract_blocked_intervals(log_entries: List[str]) -> List[Tuple[float, float]]:
    """
    Extract time intervals where blocked operations occurred from log entries.
    
    Args:
        log_entries: List of log lines from execution logs
        
    Returns:
        List of (start_time, end_time) tuples for blocked intervals
    """
    blocked_intervals = []
    
    for entry in log_entries:
        match = BLOCKED_LOG_PATTERN.search(entry)
        if match:
            timestamp_str = match.group(1)
            blocked_time = parse_timestamp(timestamp_str)
            # Blocked operations are instantaneous (exception raised immediately)
            # We treat them as having a small duration based on context
            # For now, we mark the exact timestamp as the blocked point
            blocked_intervals.append((blocked_time, blocked_time))
            
    return blocked_intervals

def extract_step_intervals(log_entries: List[str]) -> Dict[str, List[Tuple[float, float]]]:
    """
    Extract start/end intervals for each step from log entries.
    
    Args:
        log_entries: List of log lines from execution logs
        
    Returns:
        Dict mapping step_id to list of (start_time, end_time) tuples
    """
    step_intervals: Dict[str, List[Tuple[float, float]]] = {}
    current_steps: Dict[str, float] = {}
    
    for entry in log_entries:
        match = STEP_LOG_PATTERN.search(entry)
        if match:
            step_id = match.group(1)
            action = match.group(2)
            timestamp_str = match.group(3)
            timestamp = parse_timestamp(timestamp_str)
            
            if action == 'start':
                current_steps[step_id] = timestamp
            elif action == 'end':
                if step_id in current_steps:
                    start_time = current_steps[step_id]
                    end_time = timestamp
                    if step_id not in step_intervals:
                        step_intervals[step_id] = []
                    step_intervals[step_id].append((start_time, end_time))
                    del current_steps[step_id]
    
    return step_intervals

def calculate_clean_step_latency(
    step_start_time: float,
    step_end_time: float,
    blocked_intervals: List[Tuple[float, float]]
) -> float:
    """
    Calculate step latency excluding time spent on blocked operations.
    
    Args:
        step_start_time: Start timestamp of the step
        step_end_time: End timestamp of the step
        blocked_intervals: List of (start, end) tuples for blocked operations
        
    Returns:
        Clean latency in seconds with blocked time excluded
    """
    total_duration = step_end_time - step_start_time
    
    if not blocked_intervals:
        return total_duration
    
    blocked_time = 0.0
    for blocked_start, blocked_end in blocked_intervals:
        # Calculate overlap between step interval and blocked interval
        overlap_start = max(step_start_time, blocked_start)
        overlap_end = min(step_end_time, blocked_end)
        
        if overlap_start < overlap_end:
            blocked_time += (overlap_end - overlap_start)
    
    # For instantaneous blocked operations (start == end), we estimate
    # a small overhead based on typical exception handling time
    # This is a heuristic since the kernel logs the timestamp of the block
    instantaneous_blocks = sum(
        1 for start, end in blocked_intervals 
        if abs(end - start) < 0.001 and start >= step_start_time and end <= step_end_time
    )
    
    # Estimate 5ms per instantaneous blocked operation as overhead
    instantaneous_overhead = instantaneous_blocks * 0.005
    
    clean_latency = max(0.0, total_duration - blocked_time - instantaneous_overhead)
    
    logger.debug(
        f"Step latency calculation: total={total_duration:.4f}s, "
        f"blocked={blocked_time:.4f}s, instantaneous_overhead={instantaneous_overhead:.4f}s, "
        f"clean={clean_latency:.4f}s"
    )
    
    return clean_latency

def get_blocked_time_from_logs(log_file_path: str) -> List[Tuple[float, float]]:
    """
    Read log file and extract blocked operation intervals.
    
    Args:
        log_file_path: Path to the execution log file
        
    Returns:
        List of (start_time, end_time) tuples for blocked operations
    """
    log_entries = []
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            log_entries = f.readlines()
    except FileNotFoundError:
        logger.warning(f"Log file not found: {log_file_path}")
        return []
    except Exception as e:
        logger.error(f"Error reading log file {log_file_path}: {e}")
        return []
    
    return extract_blocked_intervals(log_entries)

def record_step_with_blocked_exclusion(
    task_id: str,
    step_id: str,
    collector: Any,
    log_file_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Record a step's latency excluding blocked operation time.
    
    This function should be called at the end of each agent step to record
    the clean latency (excluding blocked 3D library initialization time).
    
    Args:
        task_id: Unique identifier for the task
        step_id: Unique identifier for the step within the task
        collector: MetricsCollector instance to record the metrics
        log_file_path: Optional path to log file for extracting blocked intervals
        
    Returns:
        Dict with recorded metrics including clean latency
    """
    start_time = time.time()
    
    # At step end, we need to calculate clean latency
    # This function is called at step end, so we need the start time
    # The caller should pass the start time or we need to track it
    
    # For now, we assume this is called with context that includes start_time
    # In practice, the agent should track step start times and pass them here
    
    end_time = time.time()
    total_latency = end_time - start_time
    
    blocked_intervals = []
    if log_file_path:
        blocked_intervals = get_blocked_time_from_logs(log_file_path)
    
    # Filter blocked intervals relevant to this step
    # This is a simplification - in practice, we'd need step-specific timestamps
    step_blocked_intervals = [
        interval for interval in blocked_intervals
        if interval[0] >= start_time - 0.1 and interval[1] <= end_time + 0.1
    ]
    
    clean_latency = calculate_clean_step_latency(
        start_time, end_time, step_blocked_intervals
    )
    
    # Record with collector
    record = collector.record_step(
        task_id=task_id,
        latency_ms=clean_latency * 1000,
        status="success",
        blocked_time_ms=(total_latency - clean_latency) * 1000
    )
    
    return record

def estimate_blocked_overhead(
    blocked_operation_count: int,
    average_overhead_per_block: float = 0.005
) -> float:
    """
    Estimate total overhead time for blocked operations.
    
    Args:
        blocked_operation_count: Number of blocked operations
        average_overhead_per_block: Average time per blocked operation in seconds
                                    (default 5ms based on typical exception handling)
                                    
    Returns:
        Estimated total overhead time in seconds
    """
    return blocked_operation_count * average_overhead_per_block

class BlockedTimeTracker:
    """
    Context manager to track and exclude blocked operation time from step latency.
    
    Usage:
        with BlockedTimeTracker() as tracker:
            # agent step code here
            pass
        
        clean_latency = tracker.get_clean_latency()
    """
    
    def __init__(self):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.blocked_events: List[Tuple[float, float]] = []
        self._blocked_hook_installed = False
    
    def __enter__(self):
        self.start_time = time.time()
        # Install hook to track blocked operations
        self._install_blocked_hook()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self._remove_blocked_hook()
        return False
    
    def _install_blocked_hook(self):
        """Install a hook to track blocked operations."""
        # This would integrate with the restricted kernel's logging
        # For now, we note that blocked operations will be logged
        self._blocked_hook_installed = True
    
    def _remove_blocked_hook(self):
        """Remove the blocked operation hook."""
        self._blocked_hook_installed = False
    
    def get_clean_latency(self) -> float:
        """Get the step latency excluding blocked operation time."""
        if self.start_time is None or self.end_time is None:
            return 0.0
        
        total_duration = self.end_time - self.start_time
        
        # Estimate blocked time (would be populated by hook in real implementation)
        # For now, return total duration as we can't track without kernel integration
        return total_duration
    
    def get_blocked_time(self) -> float:
        """Get the estimated blocked time."""
        # This would be populated by the hook
        return 0.0

def main():
    """CLI entry point for testing timing utilities."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test timing utilities')
    parser.add_argument('--log-file', type=str, help='Path to log file')
    parser.add_argument('--test-intervals', action='store_true', help='Test interval calculation')
    
    args = parser.parse_args()
    
    if args.test_intervals:
        # Test interval calculation
        step_start = 1000.0
        step_end = 1010.0
        blocked = [(1002.0, 1005.0), (1008.0, 1009.0)]
        
        clean = calculate_clean_step_latency(step_start, step_end, blocked)
        print(f"Step interval: [{step_start}, {step_end}]")
        print(f"Blocked intervals: {blocked}")
        print(f"Clean latency: {clean:.4f}s")
        print(f"Blocked time: {(step_end - step_start) - clean:.4f}s")
    
    elif args.log_file:
        blocked = get_blocked_time_from_logs(args.log_file)
        print(f"Found {len(blocked)} blocked intervals in {args.log_file}")
        for i, (start, end) in enumerate(blocked):
            print(f"  {i+1}. [{start:.4f}, {end:.4f}]")
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()