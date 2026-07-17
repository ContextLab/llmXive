import os
import sys
import json
import time
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

def run_pipeline_step(step_name, command):
    """Run a single step and return status."""
    print(f"Running {step_name}...")
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=3600
        )
        if result.returncode != 0:
            return False, result.stderr
        return True, result.stdout
    except subprocess.TimeoutExpired:
        return False, "Timeout exceeded"
    except Exception as e:
        return False, str(e)

def main():
    """Validate the full pipeline runtime."""
    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pipeline_steps": [],
        "total_time_seconds": 0,
        "passed": True
    }

    start_time = time.time()

    # Simplified pipeline steps for CI validation
    # In a real scenario, these would call the specific scripts
    steps = [
        ("Verify", "python code/data/verify.py"),
        ("Download", "python code/data/download.py"),
        ("Preprocess", "python code/data/preprocess.py"),
        ("Split", "python code/data/split.py"),
        ("Diagnostics", "python code/models/diagnostics.py"),
        ("Fit Logistic", "python code/models/fit_logistic.py"),
        ("Fit Bayesian", "python code/models/fit_bayesian.py"),
        ("Evaluate", "python code/evaluation/metrics.py"),
        ("Report", "python code/evaluation/report.py")
    ]

    for name, cmd in steps:
        success, output = run_pipeline_step(name, cmd)
        report["pipeline_steps"].append({"step": name, "success": success})
        if not success:
            report["passed"] = False
            break

    end_time = time.time()
    report["total_time_seconds"] = end_time - start_time

    output_path = project_root / "data" / "ci_validation_report.json"
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"CI Validation Report: {output_path}")
    return 0 if report["passed"] else 1

if __name__ == "__main__":
    sys.exit(main())
