import os
import json
import time
import logging
import gc
from pathlib import Path
from typing import Dict, Any, List, Optional
import psutil

# Configure logging
logger = logging.getLogger(__name__)

def get_memory_usage_mb(process_id: Optional[int] = None) -> float:
    """Get current memory usage in MB for the current process or specified process."""
    try:
        if process_id is None:
            process = psutil.Process()
        else:
            process = psutil.Process(process_id)
        return process.memory_info().rss / (1024 * 1024)
    except Exception as e:
        logger.warning(f"Could not get memory usage: {e}")
        return 0.0

def get_peak_memory_mb() -> float:
    """Get peak memory usage in MB for the current process."""
    try:
        process = psutil.Process()
        # Note: psutil doesn't track peak RSS directly, using maxrss from resource module as fallback
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # Convert KB to MB
    except Exception as e:
        logger.warning(f"Could not get peak memory usage: {e}")
        return get_memory_usage_mb()

def generate_memory_log_entry(phase: str, memory_mb: float, peak_memory_mb: float, 
                             timestamp: Optional[float] = None) -> Dict[str, Any]:
    """Generate a structured log entry for memory usage."""
    return {
        "phase": phase,
        "memory_mb": round(memory_mb, 2),
        "peak_memory_mb": round(peak_memory_mb, 2),
        "timestamp": timestamp or time.time(),
        "timestamp_formatted": time.strftime("%Y-%m-%d %H:%M:%S")
    }

def save_memory_log(log_entries: List[Dict[str, Any]], output_path: str) -> None:
    """Save memory log entries to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(log_entries, f, indent=2)
    logger.info(f"Memory log saved to: {output_path}")

def log_memory_usage(phase: str, output_path: str = "data/processed/memory_log.json") -> Dict[str, Any]:
    """
    Log memory usage for a specific phase and append to the memory log file.
    
    Args:
        phase: Name of the current phase
        output_path: Path to the memory log JSON file
        
    Returns:
        The memory log entry created
    """
    # Force garbage collection to get accurate memory usage
    gc.collect()
    
    current_memory = get_memory_usage_mb()
    peak_memory = get_peak_memory_mb()
    
    entry = generate_memory_log_entry(phase, current_memory, peak_memory)
    
    # Load existing log or create new one
    log_entries = []
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r') as f:
                log_entries = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load existing memory log: {e}")
            log_entries = []
    
    # Append new entry
    log_entries.append(entry)
    
    # Save updated log
    save_memory_log(log_entries, output_path)
    
    logger.info(f"Memory logged for {phase}: {current_memory:.2f} MB (peak: {peak_memory:.2f} MB)")
    return entry