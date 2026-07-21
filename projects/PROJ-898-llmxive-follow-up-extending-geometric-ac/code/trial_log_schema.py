"""
Schema definition and utilities for trial logging in the symbolic planner experiment.

This module defines the structure of the trial_log.csv file used to record
the execution of individual trials in the inference pipeline.

Schema Columns:
- trial_id: Unique identifier for the experimental trial (integer or string)
- step: Step number within the trial (integer, 0-indexed)
- success: Boolean flag indicating if the step succeeded (0 or 1)
- infeasible: Boolean flag indicating if constraints were unsatisfiable (0 or 1)
- timeout: Boolean flag indicating if the step exceeded time limits (0 or 1)
- latency_ms: Execution time in milliseconds (float)
"""
import csv
import os
from typing import Dict, List, Optional, Any, TextIO
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

# Schema definition as a constant list of column names in order
TRIAL_LOG_COLUMNS = [
    "trial_id",
    "step",
    "success",
    "infeasible",
    "timeout",
    "latency_ms"
]

@dataclass
class TrialLogEntry:
    """Data class representing a single row in the trial log."""
    trial_id: Any
    step: int
    success: bool
    infeasible: bool
    timeout: bool
    latency_ms: float

    def to_row(self) -> Dict[str, Any]:
        """Convert the entry to a dictionary matching the CSV schema."""
        return {
            "trial_id": self.trial_id,
            "step": self.step,
            "success": 1 if self.success else 0,
            "infeasible": 1 if self.infeasible else 0,
            "timeout": 1 if self.timeout else 0,
            "latency_ms": self.latency_ms
        }

class TrialLogger:
    """Context manager and utility for writing trial logs to CSV."""
    
    def __init__(self, output_path: str):
        """
        Initialize the logger.
        
        Args:
            output_path: Path to the CSV file to write.
        """
        self.output_path = output_path
        self.file_handle: Optional[TextIO] = None
        self.writer: Optional[csv.DictWriter] = None
        self._is_context_manager = False

    def __enter__(self):
        """Open the file for writing if not already open."""
        self._is_context_manager = True
        if self.file_handle is None:
            self.file_handle = open(self.output_path, mode='w', newline='')
            self.writer = csv.DictWriter(
                self.file_handle, 
                fieldnames=TRIAL_LOG_COLUMNS
            )
            self.writer.writeheader()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close the file if opened by this context manager."""
        if self._is_context_manager and self.file_handle:
            self.file_handle.close()
            self.file_handle = None
            self.writer = None
        self._is_context_manager = False
        return False  # Do not suppress exceptions

    def write_entry(self, entry: TrialLogEntry) -> None:
        """
        Write a single trial log entry to the CSV.
        
        Args:
            entry: The TrialLogEntry to write.
        """
        if self.writer is None:
            raise RuntimeError("Logger not initialized. Use as context manager or call open().")
        
        row = entry.to_row()
        self.writer.writerow(row)
        self.file_handle.flush()

    def write_entries(self, entries: List[TrialLogEntry]) -> None:
        """
        Write multiple trial log entries to the CSV.
        
        Args:
            entries: List of TrialLogEntry objects.
        """
        for entry in entries:
            self.write_entry(entry)

    def open(self) -> None:
        """Open the file for writing."""
        if self.file_handle is None:
            self.file_handle = open(self.output_path, mode='w', newline='')
            self.writer = csv.DictWriter(
                self.file_handle, 
                fieldnames=TRIAL_LOG_COLUMNS
            )
            self.writer.writeheader()

    def close(self) -> None:
        """Close the file."""
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None
            self.writer = None

def get_schema_description() -> Dict[str, str]:
    """
    Returns a description of each column in the trial log schema.
    
    Returns:
        Dictionary mapping column names to their descriptions.
    """
    return {
        "trial_id": "Unique identifier for the experimental trial (int or str)",
        "step": "Step number within the trial (int, 0-indexed)",
        "success": "Boolean flag (0/1) indicating if the step succeeded",
        "infeasible": "Boolean flag (0/1) indicating if constraints were unsatisfiable",
        "timeout": "Boolean flag (0/1) indicating if the step exceeded time limits",
        "latency_ms": "Execution time in milliseconds (float)"
    }

def verify_schema(path: str) -> bool:
    """
    Verify that a CSV file matches the expected trial log schema.
    
    Args:
        path: Path to the CSV file.
        
    Returns:
        True if the schema matches, False otherwise.
    """
    if not os.path.exists(path):
        logger.error(f"File not found: {path}")
        return False
    
    try:
        with open(path, 'r', newline='') as f:
            reader = csv.reader(f)
            header = next(reader)
            
            if header != TRIAL_LOG_COLUMNS:
                logger.error(f"Header mismatch. Expected {TRIAL_LOG_COLUMNS}, got {header}")
                return False
            
            # Check at least one data row exists
            try:
                next(reader)
            except StopIteration:
                logger.warning(f"File {path} has header but no data rows.")
                
        return True
    except Exception as e:
        logger.error(f"Error verifying schema in {path}: {e}")
        return False

def main():
    """
    CLI entry point to demonstrate schema usage and verification.
    """
    import sys
    import tempfile
    
    logging.basicConfig(level=logging.INFO)
    
    # Create a temporary file for demonstration
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
        temp_path = tmp.name

    try:
        logger.info(f"Creating trial log at: {temp_path}")
        
        with TrialLogger(temp_path) as logger_obj:
            # Create sample entries
            entries = [
                TrialLogEntry(trial_id=1, step=0, success=True, infeasible=False, timeout=False, latency_ms=12.5),
                TrialLogEntry(trial_id=1, step=1, success=False, infeasible=True, timeout=False, latency_ms=0.0),
                TrialLogEntry(trial_id=1, step=2, success=False, infeasible=False, timeout=True, latency_ms=5000.0),
                TrialLogEntry(trial_id=2, step=0, success=True, infeasible=False, timeout=False, latency_ms=14.2),
            ]
            logger_obj.write_entries(entries)
        
        # Verify schema
        if verify_schema(temp_path):
            logger.info("Schema verification passed.")
        else:
            logger.error("Schema verification failed.")
            sys.exit(1)
            
        # Print contents
        logger.info("File contents:")
        with open(temp_path, 'r') as f:
            print(f.read())
            
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == "__main__":
    main()
