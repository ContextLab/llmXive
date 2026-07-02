"""Run the full experiment pipeline and record basic resource usage."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

def get_memory_mb() -> float | None:
    """Return the current process memory usage in megabytes, if possible."""
    try:
        import psutil
    except Exception:
        return None
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    results_dir = project_root / "projects" / "PROJ-586-social-memory-networks-modeling-collecti" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    start = time.time()
    # Run the main pipeline script; this will generate all CSV/plot artifacts.
    subprocess.run([sys.executable, "code/run_full_pipeline.py"], check=True, cwd=str(project_root))
    end = time.time()

    runtime_seconds = end - start
    memory_mb = get_memory_mb()
    total, used, free = shutil.disk_usage(str(project_root))
    disk_used_gb = used / (1024 ** 3)

    profile = {
        "runtime_seconds": runtime_seconds,
        "memory_mb": memory_mb,
        "disk_used_gb": disk_used_gb,
    }

    out_path = results_dir / "pipeline_profile.json"
    out_path.write_text(json.dumps(profile, indent=2))
    print(f"Pipeline profiling written to {out_path}")

if __name__ == "__main__":
    main()
