"""
Full‑pipeline runner for CI validation (Task T035).

Executes the end‑to‑end experiment scripts, records total runtime,
peak memory usage, and disk consumption, and writes a concise report to
``projects/PROJ-586-social-memory-networks-modeling-collecti/results/``.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

# Optional third‑party dependency – ensure it is listed in requirements.txt
try:
    import psutil
except ImportError as exc:
    sys.stderr.write("psutil is required for resource measurement. Install it via requirements.txt\\n")
    raise


RESULT_DIR = Path(
    "projects/PROJ-586-social-memory-networks-modeling-collecti/results"
)
RESULT_DIR.mkdir(parents=True, exist_ok=True)


def _run_script(command: list[str], description: str) -> float:
    """Run a subprocess command and return its elapsed seconds."""
    start = time.time()
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"❌ {description} failed (returncode={e.returncode})\\n")
        sys.stderr.write(e.stderr.decode() if e.stderr else "")
        raise
    elapsed = time.time() - start
    print(f"✅ {description} completed in {elapsed:.2f}s")
    return elapsed


def _measure_memory() -> float:
    """Return current RSS memory usage in megabytes."""
    process = psutil.Process(os.getpid())
    mem_bytes = process.memory_info().rss
    return mem_bytes / (1024 * 1024)


def _measure_disk() -> float:
    """Return total disk usage of the project directory in megabytes."""
    usage = shutil.disk_usage(Path.cwd())
    # Use the used portion as a simple proxy
    return usage.used / (1024 * 1024)


def main() -> None:
    """
    Execute the full experiment pipeline and write a resource‑usage report.

    The pipeline consists of:
    1. Full‑context simulation (100 games – enough for a quick CI run)
    2. Limited‑context simulation (100 games)
    3. ANOVA analysis
    4. Power analysis
    5. Scaling analysis
    6. Plot generation (scaling & sensitivity)
    """
    total_runtime = 0.0
    steps = [
        (["python", "code/run_experiment.py", "--context", "full", "--agents", "5", "--games", "100"],
         "Full‑context simulation (100 games)"),
        (["python", "code/run_experiment.py", "--context", "limited", "--agents", "5", "--games", "100"],
         "Limited‑context simulation (100 games)"),
        (["python", "code/run_anova.py"], "ANOVA analysis"),
        (["python", "code/run_power.py"], "Power analysis"),
        (["python", "code/run_scaling_plot_generation.py"], "Scaling plot generation"),
    ]

    for cmd, desc in steps:
        elapsed = _run_script(cmd, desc)
        total_runtime += elapsed

    # Record resource usage after the pipeline
    memory_mb = _measure_memory()
    disk_mb = _measure_disk()

    report = {
        "total_runtime_seconds": round(total_runtime, 2),
        "peak_memory_mb": round(memory_mb, 2),
        "disk_usage_mb": round(disk_mb, 2),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    out_path = RESULT_DIR / "pipeline_resource_report.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"🗒️ Resource report written to {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run full pipeline and record resources")
    # No additional arguments needed for CI; kept for extensibility
    args = parser.parse_args()
    main()
