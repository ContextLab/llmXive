"""
Python entry point for the full suite if shell script is not preferred.
Orchestrates the end-to-end pipeline execution.
"""
import subprocess
import sys
import os
import json

def main():
    print("=== llmXive Full Suite End-to-End Regression Test ===")
    print(f"Starting at: {subprocess.check_output(['date']).decode().strip()}")

    # Clean state
    print("[1/6] Cleaning data/processed/...")
    import shutil
    if os.path.exists("data/processed"):
        shutil.rmtree("data/processed")
    os.makedirs("data/processed", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    # Run Full Sweep
    print("[2/6] Running full N-sweep (T033b)...")
    result = subprocess.run([sys.executable, "src/main.py", "--run-full-sweep"], check=True)
    if not os.path.exists("data/processed/full_sweep_results.json"):
        raise RuntimeError("full_sweep_results.json missing")
    print("  Generated: data/processed/full_sweep_results.json")

    # Heavy Tailed
    print("[3/6] Running heavy-tailed validation (T034d)...")
    result = subprocess.run([sys.executable, "scripts/run_heavy_tailed_validation.py"], check=True)
    if not os.path.exists("data/processed/heavy_tailed_results.json"):
        raise RuntimeError("heavy_tailed_results.json missing")
    print("  Generated: data/processed/heavy_tailed_results.json")

    # Derivation Audit
    print("[4/6] Running final derivation audit (T066)...")
    result = subprocess.run([sys.executable, "scripts/run_final_derivation_audit.py"], check=True)
    if not os.path.exists("docs/peer_review_checklist.md"):
        raise RuntimeError("peer_review_checklist.md missing")
    print("  Updated: docs/peer_review_checklist.md")

    # Sample Size Check
    print("[5/6] Verifying sample size enforcement (T064)...")
    result = subprocess.run([sys.executable, "scripts/verify_sample_size_enforcement.py"], check=True)
    print("  Verification passed.")

    # Final Report
    print("[6/6] Generating final statistical report (T044)...")
    result = subprocess.run([sys.executable, "src/analysis/stats.py", "--generate-report"], check=True)
    if not os.path.exists("data/processed/statistical_report.json"):
        raise RuntimeError("statistical_report.json missing")
    print("  Generated: data/processed/statistical_report.json")

    print("=== Suite Completed Successfully ===")
    print(f"Finished at: {subprocess.check_output(['date']).decode().strip()}")

if __name__ == "__main__":
    main()
