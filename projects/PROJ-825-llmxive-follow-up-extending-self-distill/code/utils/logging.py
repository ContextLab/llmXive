"""
Logging infrastructure for llmXive research pipeline.
Supports JSON/CSV output for TrainingRun and GatingSignal artifacts.
"""
import json
import csv
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

# Import config to ensure we use the project's defined paths
from config import get_config, LoggingConfig


class Logger:
    """
    Unified logger for research artifacts.
    Handles both JSONL (for streaming logs) and CSV (for aggregated tables) outputs.
    """

    def __init__(self, config: Optional[LoggingConfig] = None):
        self.config = config or get_config().logging
        self.output_dir = Path(self.config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Track open file handles for streaming
        self._jsonl_handles: Dict[str, Any] = {}
        self._csv_handles: Dict[str, Any] = {}
        self._csv_writers: Dict[str, Any] = {}

    def _get_jsonl_handle(self, filename: str):
        """Get or create a file handle for JSONL writing."""
        if filename not in self._jsonl_handles:
            filepath = self.output_dir / filename
            handle = open(filepath, 'a', encoding='utf-8')
            self._jsonl_handles[filename] = handle
        return self._jsonl_handles[filename]

    def _get_csv_writer(self, filename: str, fieldnames: Optional[List[str]] = None):
        """Get or create a CSV writer for a file."""
        if filename not in self._csv_writers:
            filepath = self.output_dir / filename
            file_exists = os.path.exists(filepath) and os.path.getsize(filepath) > 0

            mode = 'a' if file_exists else 'w'
            handle = open(filepath, mode, newline='', encoding='utf-8')

            if not file_exists and fieldnames:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
            else:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)

            self._csv_handles[filename] = handle
            self._csv_writers[filename] = writer
        return self._csv_writers[filename]

    def log_training_run(self, data: Dict[str, Any], mode: str = 'jsonl'):
        """
        Log a TrainingRun artifact.

        Args:
            data: Dictionary containing training run metrics.
                  Expected keys: run_id, timestamp, variant, episode, step, reward,
                                 success, steps_to_threshold, total_steps, cost_cpu, cost_memory
            mode: 'jsonl' for streaming logs, 'csv' for aggregated tables.
        """
        # Ensure required fields
        if 'timestamp' not in data:
            data['timestamp'] = datetime.utcnow().isoformat()

        if mode == 'jsonl':
            handle = self._get_jsonl_handle(self.config.training_log_jsonl)
            handle.write(json.dumps(data) + '\n')
            handle.flush()
        elif mode == 'csv':
            # For CSV, we define standard fields for training runs
            fieldnames = [
                'run_id', 'timestamp', 'variant', 'episode', 'step', 'reward',
                'success', 'steps_to_threshold', 'total_steps', 'cost_cpu', 'cost_memory'
            ]
            writer = self._get_csv_writer(self.config.training_log_csv, fieldnames)
            writer.writerow(data)

    def log_gating_signal(self, data: Dict[str, Any], mode: str = 'jsonl'):
        """
        Log a GatingSignal artifact.

        Args:
            data: Dictionary containing gating signal metrics.
                  Expected keys: run_id, episode, step, token_entropy, context_stability,
                                 gating_score, teacher_invoked, paired_trajectory_id
            mode: 'jsonl' for streaming logs, 'csv' for aggregated tables.
        """
        # Ensure required fields
        if 'timestamp' not in data:
            data['timestamp'] = datetime.utcnow().isoformat()

        if mode == 'jsonl':
            handle = self._get_jsonl_handle(self.config.gating_signal_log_jsonl)
            handle.write(json.dumps(data) + '\n')
            handle.flush()
        elif mode == 'csv':
            fieldnames = [
                'run_id', 'episode', 'step', 'token_entropy', 'context_stability',
                'gating_score', 'teacher_invoked', 'paired_trajectory_id', 'timestamp'
            ]
            writer = self._get_csv_writer(self.config.gating_signal_log_csv, fieldnames)
            writer.writerow(data)

    def close(self):
        """Close all open file handles."""
        for handle in self._jsonl_handles.values():
            handle.close()
        self._jsonl_handles.clear()

        for handle in self._csv_handles.values():
            handle.close()
        self._csv_handles.clear()
        self._csv_writers.clear()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Convenience functions for quick access without instantiating Logger
_global_logger: Optional[Logger] = None

def get_logger() -> Logger:
    """Get or create the global logger instance."""
    global _global_logger
    if _global_logger is None:
        _global_logger = Logger()
    return _global_logger

def log_training_run(data: Dict[str, Any], mode: str = 'jsonl'):
    """Log training run using the global logger."""
    get_logger().log_training_run(data, mode)

def log_gating_signal(data: Dict[str, Any], mode: str = 'jsonl'):
    """Log gating signal using the global logger."""
    get_logger().log_gating_signal(data, mode)

def close_logger():
    """Close the global logger."""
    global _global_logger
    if _global_logger:
        _global_logger.close()
        _global_logger = None