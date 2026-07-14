import os
import sys
import subprocess
import time
import json
from pathlib import Path
from datetime import datetime

# Ensure we can import from the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import get_data_dir, get_results_dir, ensure_directories

def check_file_exists(path_str: str, description: str) -> bool:
    """Check if a required file exists."""
    p = Path(path_str)
    if not p.exists():
        print(f"❌ MISSING: {description} at {p}")
        return False
    print(f"✅ FOUND: {description} at {p}")
    return True

def run_script(script_rel_path: str, args: list = None, timeout: int = 300) -> bool:
    """Run a script and return True if it exits with code 0."""
    script_path = Path(PROJECT_ROOT) / script_rel_path
    if not script_path.exists():
        print(f"❌ SCRIPT NOT FOUND: {script_path}")
        return False

    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)

    print(f"🚀 Running: {' '.join(cmd)}")
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT)}
        )
        elapsed = time.time() - start_time

        if result.returncode == 0:
            print(f"✅ SUCCESS: {script_rel_path} (took {elapsed:.2f}s)")
            if result.stdout:
                # Log last few lines of output for context
                lines = result.stdout.strip().split('\n')
                for line in lines[-5:]:
                    print(f"   | {line}")
            return True
        else:
            print(f"❌ FAILED: {script_rel_path} (exit code {result.returncode})")
            print(f"   STDOUT: {result.stdout}")
            print(f"   STDERR: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"❌ TIMEOUT: {script_rel_path} exceeded {timeout}s")
        return False
    except Exception as e:
        print(f"❌ ERROR running {script_rel_path}: {e}")
        return False

def main():
    print("=" * 60)
    print("QUICKSTART VALIDATION: End-to-End Reproducibility Check")
    print("Target Environment: CPU-Only")
    print("=" * 60)

    start_total = time.time()
    results = {
        "timestamp": datetime.now().isoformat(),
        "environment": "CPU-Only Validation",
        "checks": [],
        "scripts": [],
        "final_status": "PASS"
    }

    # 1. Check Directory Structure
    print("\n--- Checking Directory Structure ---")
    ensure_directories()
    dirs_to_check = [
        (get_data_dir(), "Data Root"),
        (get_results_dir(), "Results Root"),
        (PROJECT_ROOT / "data" / "raw", "Raw Data"),
        (PROJECT_ROOT / "data" / "stratified", "Stratified Data"),
        (PROJECT_ROOT / "data" / "features", "Features"),
        (PROJECT_ROOT / "data" / "processed", "Processed Data"),
    ]
    for d, name in dirs_to_check:
        if not check_file_exists(str(d), name):
            results["checks"].append({"name": name, "status": "FAIL"})
            results["final_status"] = "FAIL"
        else:
            results["checks"].append({"name": name, "status": "PASS"})

    # 2. Check Documentation
    print("\n--- Checking Documentation ---")
    docs = [
        ("README.md", "Project README"),
        ("quickstart.md", "Quickstart Guide"),
    ]
    for doc, name in docs:
        if not check_file_exists(str(PROJECT_ROOT / doc), name):
            results["checks"].append({"name": name, "status": "FAIL"})
            results["final_status"] = "FAIL"
        else:
            results["checks"].append({"name": name, "status": "PASS"})

    # 3. Execute Pipeline Scripts in Order
    print("\n--- Executing Pipeline Scripts ---")
    
    # Step A: Setup/Download (T007) - Only if raw data missing
    # Note: We assume T007 has run or data is present. If not, we try to run it.
    # For validation, we run the main orchestrator which should handle dependencies.
    # However, to be thorough, we run the specific steps if they are expected to be idempotent.
    
    # We will run the main orchestrator (T020) which is the definitive end-to-end test.
    # If the orchestrator fails, the pipeline is broken.
    
    scripts_to_run = [
        ("code/main.py", ["--validate-only"], "Main Orchestrator (Validation Mode)"),
    ]
    
    # If main.py doesn't support --validate-only, we run it normally but expect it to be fast
    # if data is already processed.
    
    for script, args, desc in scripts_to_run:
        success = run_script(script, args)
        results["scripts"].append({"script": script, "args": args, "status": "PASS" if success else "FAIL"})
        if not success:
            results["final_status"] = "FAIL"
            break

    # 4. Verify Final Outputs
    print("\n--- Verifying Final Outputs ---")
    output_files = [
        ("data/results/metrics.json", "Metrics JSON"),
        ("data/results/hypothesis_verification.md", "Hypothesis Verification Report"),
    ]
    
    for f, name in output_files:
        full_path = PROJECT_ROOT / f
        if not check_file_exists(str(full_path), name):
            results["checks"].append({"name": name, "status": "FAIL"})
            results["final_status"] = "FAIL"
        else:
            results["checks"].append({"name": name, "status": "PASS"})
            # Attempt to load JSON to ensure validity
            if f.endswith(".json"):
                try:
                    with open(full_path, 'r') as fh:
                        data = json.load(fh)
                    print(f"   ✅ JSON Valid: {name}")
                except json.JSONDecodeError:
                    print(f"   ❌ JSON Invalid: {name}")
                    results["final_status"] = "FAIL"

    total_time = time.time() - start_total
    print("\n" + "=" * 60)
    print(f"VALIDATION COMPLETE: {results['final_status']}")
    print(f"Total Time: {total_time:.2f}s")
    print("=" * 60)

    # Save validation log
    log_path = PROJECT_ROOT / "data" / "results" / "quickstart_validation_log.json"
    ensure_directories()
    with open(log_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"📝 Validation log saved to: {log_path}")

    if results["final_status"] == "FAIL":
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
