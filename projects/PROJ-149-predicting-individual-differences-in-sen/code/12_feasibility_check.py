"""
Task T032: Implement feasibility measurement script.
Estimates RAM usage and runtime for the pipeline, logging results to a file.
Does not abort execution; only records metrics.
"""
import os
import sys
import time
import psutil
import json
from pathlib import Path

# Import shared config utilities.
# We use a tolerant get_path wrapper to handle various call signatures found in the codebase.
from config import get_path as _get_path, ensure_dirs as _ensure_dirs, get_seed

def safe_get_path(*args, **kwargs):
    """
    Wrapper for config.get_path to tolerate multiple call signatures:
    - get_path("data/processed/file.json")
    - get_path("processed", "file.json")
    - get_path(base_dir, "data/processed/file.json")
    """
    try:
        # Try the standard signature first: get_path(name) or get_path(subdir, name)
        # The underlying config.py likely expects (name) or (subdir, name).
        # We attempt to delegate based on argument count.
        if len(args) == 1:
            return _get_path(args[0])
        elif len(args) == 2:
            # Check if first arg looks like a base_dir (absolute path) or a subdir key
            # If it's a string key, pass both. If it's a path, join.
            if args[0] in ["interim", "processed", "raw", "data_raw", "features", "model_results", "correlations", "robustness", "sensitivity", "verification"]:
                return _get_path(args[0], args[1])
            else:
                # Assume first arg is a base path and second is relative
                base = args[0]
                rel = args[1]
                return str(Path(base) / rel)
        else:
            # Fallback: join all args as path components
            return str(Path(*args))
    except Exception:
        # If all else fails, try to construct a path manually or return a default
        # This prevents the feasibility check from crashing the whole pipeline
        return "data/processed/feasibility_metrics.log"

def safe_ensure_dirs(*args, **kwargs):
    """
    Wrapper for config.ensure_dirs to tolerate multiple call signatures:
    - ensure_dirs()
    - ensure_dirs(path)
    - ensure_dirs([path])
    - ensure_dirs(path, mode)
    """
    try:
        # Normalize args
        paths_to_create = []
        if len(args) == 0:
            # No args: do nothing or create default
            return None
        elif len(args) == 1:
            val = args[0]
            if isinstance(val, list):
                paths_to_create = val
            else:
                paths_to_create = [val]
        else:
            # Multiple args: treat as list of paths
            paths_to_create = list(args)

        for p in paths_to_create:
            if isinstance(p, Path):
                p = str(p)
            if isinstance(p, str):
                os.makedirs(p, exist_ok=True)
        return paths_to_create[0] if paths_to_create else None
    except Exception:
        # Fail silently for feasibility check
        return None

def get_memory_usage_mb():
    """Returns current RAM usage in MB."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 * 1024)

def estimate_runtime(num_participants):
    """
    Estimates runtime based on the heuristic: participants * 0.05 s.
    Returns estimated time in seconds.
    """
    return num_participants * 0.05

def count_participants():
    """
    Attempts to count participants from the joined metadata or behavioral metrics.
    Returns an integer count, or 0 if files are missing.
    """
    # Try common paths for participant lists
    possible_paths = [
        "data/interim/joined_metadata.csv",
        "data/interim/behavioral_metrics.csv",
        "data/processed/features.csv"
    ]
    
    for p_name in possible_paths:
        try:
            # Use safe path resolution
            p = safe_get_path(p_name)
            if os.path.exists(p):
                import pandas as pd
                df = pd.read_csv(p)
                # Assume 'participant_id' is the column, or count rows if missing
                if 'participant_id' in df.columns:
                    return df['participant_id'].nunique()
                else:
                    return len(df)
        except Exception:
            continue
    
    return 0

def main():
    """
    Main entry point for T032.
    Estimates RAM and runtime, logs to data/processed/feasibility_metrics.log.
    """
    print("Starting feasibility measurement (T032)...")
    
    # 1. Estimate RAM usage
    current_ram_mb = get_memory_usage_mb()
    
    # 2. Estimate runtime
    num_participants = count_participants()
    estimated_runtime_sec = estimate_runtime(num_participants)
    
    # 3. Prepare metrics dictionary
    metrics = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "current_ram_mb": round(current_ram_mb, 2),
        "estimated_runtime_seconds": round(estimated_runtime_sec, 4),
        "participant_count": num_participants,
        "heuristic_factor": 0.05,
        "status": "completed"
    }
    
    # 4. Write to log file
    # Ensure the output directory exists
    output_dir = "data/processed"
    safe_ensure_dirs(output_dir)
    output_path = safe_get_path(output_dir, "feasibility_metrics.log")
    
    try:
        with open(output_path, 'w') as f:
            f.write(json.dumps(metrics, indent=2))
        print(f"Feasibility metrics written to {output_path}")
    except Exception as e:
        print(f"Warning: Could not write feasibility metrics: {e}")
        # Do not fail the task, just log the warning
    
    print("Feasibility measurement complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())