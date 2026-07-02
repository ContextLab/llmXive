"""CI‑friendly wrapper that runs the full experiment pipeline and records resources."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _disk_usage_mb(path: Path) -> float:
    """Return used disk space under *path* in megabytes."""
    total, used, free = shutil.disk_usage(str(path))
    return used / (1024 * 1024)

def _memory_usage_mb() -> float:
    """Return the current resident set size of the Python process (MB)."""
    try:
        import psutil
    except ImportError:
        raise RuntimeError("psutil is required for memory measurement; add it to requirements.txt")
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

# ----------------------------------------------------------------------
# Main pipeline orchestration
# ----------------------------------------------------------------------
def main() -> None:
    """Execute the full pipeline (full + limited contexts, scaling, ANOVA, power).

    The function runs a *scaled‑down* version of the experiments so that it
    finishes quickly on CI.  Results are written to the project's ``results``
    directory and a JSON summary of runtime, memory and disk usage is saved as
    ``pipeline_profile.json``.
    """
    # Directories
    project_root = Path(__file__).resolve().parents[2]  # projects/.../code/..
    results_dir = project_root / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    # Record start metrics
    start_time = time.time()
    start_mem = _memory_usage_mb()
    start_disk = _disk_usage_mb(project_root)

    # ------------------------------------------------------------------
    # 1. Run full‑context experiment (small toy run for CI)
    # ------------------------------------------------------------------
    subprocess.run(
        [sys.executable, "code/run_experiment.py",
         "--context", "full",
         "--agents", "5",
         "--games", "10"],  # tiny run to keep CI fast
        check=True,
    )

    # ------------------------------------------------------------------
    # 2. Run limited‑context experiment (toy run)
    # ------------------------------------------------------------------
    subprocess.run(
        [sys.executable, "code/run_experiment.py",
         "--context", "limited",
         "--agents", "5",
         "--games", "10"],
        check=True,
    )

    # ------------------------------------------------------------------
    # 3. Run scaling experiment (agents 3,5,7)
    # ------------------------------------------------------------------
    subprocess.run(
        [sys.executable, "code/run_scaling_experiment.py",
         "--agents", "3,5,7",
         "--games", "5"],  # very small for CI
        check=True,
    )

    # ------------------------------------------------------------------
    # 4. Run ANOVA analysis
    # ------------------------------------------------------------------
    subprocess.run(
        [sys.executable, "code/analysis/anova.py"],
        check=True,
    )

    # ------------------------------------------------------------------
    # 5. Run power analysis
    # ------------------------------------------------------------------
    subprocess.run(
        [sys.executable, "code/analysis/power.py"],
        check=True,
    )

    # Record end metrics
    end_time = time.time()
    end_mem = _memory_usage_mb()
    end_disk = _disk_usage_mb(project_root)

    profile: Dict[str, Any] = {
        "runtime_seconds": round(end_time - start_time, 2),
        "memory_mb_used": round(end_mem - start_mem, 2),
        "disk_mb_used": round(end_disk - start_disk, 2),
    }

    # Write JSON profile
    profile_path = results_dir / "pipeline_profile.json"
    with profile_path.open("w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)

    print(f"Pipeline profile written to {profile_path}")

if __name__ == "__main__":
    main()
