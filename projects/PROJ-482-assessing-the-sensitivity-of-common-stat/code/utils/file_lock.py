import os
import fcntl
import logging
import time
from contextlib import contextmanager
from typing import Optional, List, Dict, Any

def file_lock(filepath: str) -> None:
    """Locks a file using fcntl."""
    try:
        file_handle = open(filepath, 'a')
        fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX)
    except Exception as e:
        logging.error(f"Error locking file {filepath}: {e}")
        raise

def write_pvalue_batch(filepath: str, data: List[List[Any]]) -> None:
    """Writes a batch of p-values to a CSV file with file locking."""
    with file_lock(filepath):
        try:
            with open(filepath, 'a', newline='') as csvfile:
                import csv
                writer = csv.writer(csvfile)
                writer.writerows(data)
        except Exception as e:
            logging.error(f"Error writing to file {filepath}: {e}")
            raise