"""
Script to manually verify the sample size enforcement (T064).

This script attempts to run the runner with --num-runs=10 and expects
it to fail with exit code 1 and the "FR-006 Violation" message.

Usage:
    python scripts/verify_sample_size_enforcement.py
"""
import subprocess
import sys
import os

def main():
    print("=== T064: Verifying Sample Size Enforcement ===")
    print("Executing runner with --num-runs=10 (below FR-006 threshold of 30)...")
    
    cmd = [
        sys.executable,
        "src/environment/runner.py",
        "--num-runs=10",
        "--n-objectives=5",
        "--seed=42"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        print(f"Exit Code: {result.returncode}")
        print(f"Stdout:\n{result.stdout}")
        print(f"Stderr:\n{result.stderr}")
        
        # Verification logic
        if result.returncode == 1:
            combined_output = result.stdout + result.stderr
            if "FR-006 Violation" in combined_output:
                print("\n✅ SUCCESS: Run aborted correctly with FR-006 Violation.")
                return 0
            else:
                print("\n❌ FAILURE: Run exited with code 1, but missing 'FR-006 Violation' message.")
                return 1
        else:
            print(f"\n❌ FAILURE: Expected exit code 1, but got {result.returncode}.")
            return 1
            
    except Exception as e:
        print(f"\n❌ FAILURE: Exception occurred during execution: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())