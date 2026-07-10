"""
Quickstart validation script for PROJ-058.
Executes the pipeline end-to-end and verifies output artifacts exist.
"""
import os
import sys
import subprocess
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

def run_command(cmd: list, timeout: int = 3600) -> tuple:
    """Run a shell command and return (success, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def check_file_exists(path: Path, description: str) -> bool:
    """Check if a file exists and is non-empty."""
    if not path.exists():
        print(f"❌ MISSING: {description} at {path}")
        return False
    if path.stat().st_size == 0:
        print(f"❌ EMPTY: {description} at {path}")
        return False
    print(f"✅ FOUND: {description} at {path}")
    return True

def main():
    print("=" * 60)
    print("Running Quickstart Validation for PROJ-058")
    print("=" * 60)

    all_passed = True

    # 1. Verify directory structure
    required_dirs = [
        "data", "data/raw", "data/processed",
        "code", "code/discovery", "code/preprocess", "code/analysis", "code/viz",
        "output", "output/figures", "tests", "logs"
    ]
    print("\n[1/4] Checking directory structure...")
    for d in required_dirs:
        if not (PROJECT_ROOT / d).exists():
            print(f"❌ Missing directory: {d}")
            all_passed = False
    if all_passed:
        print("✅ All directories present")

    # 2. Run the main pipeline
    print("\n[2/4] Executing main pipeline (code/main.py)...")
    success, stdout, stderr = run_command([
        sys.executable, str(PROJECT_ROOT / "code" / "main.py")
    ], timeout=21600)  # 6 hours

    if success:
        print("✅ Pipeline execution completed successfully")
    else:
        print("❌ Pipeline execution failed")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        all_passed = False

    # 3. Verify output artifacts
    print("\n[3/4] Verifying output artifacts...")
    required_outputs = [
        ("output/discovery_status.json", "Discovery status"),
        ("data/processed/variance_matrix.csv", "Unified variance matrix"),
        ("output/correlation_results.json", "Correlation results"),
        ("output/timescale_alignment.json", "Timescale alignment data"),
        ("output/final_report.json", "Final report"),
        ("logs/pipeline.log", "Pipeline log")
    ]

    for rel_path, desc in required_outputs:
        full_path = PROJECT_ROOT / rel_path
        if not check_file_exists(full_path, desc):
            all_passed = False

    # 4. Validate final report structure
    print("\n[4/4] Validating final report structure...")
    final_report_path = PROJECT_ROOT / "output" / "final_report.json"
    if final_report_path.exists():
        try:
            with open(final_report_path, "r") as f:
                report = json.load(f)
            
            required_keys = ["discovery_status", "correlation", "timescale_alignment", "sensitivity"]
            missing_keys = [k for k in required_keys if k not in report]
            
            if missing_keys:
                print(f"❌ Missing keys in final report: {missing_keys}")
                all_passed = False
            else:
                print("✅ Final report structure valid")
        except json.JSONDecodeError:
            print("❌ Final report is not valid JSON")
            all_passed = False
    else:
        print("❌ Cannot validate: final_report.json missing")
        all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ VALIDATION PASSED: Quickstart check successful")
        return 0
    else:
        print("❌ VALIDATION FAILED: See errors above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
