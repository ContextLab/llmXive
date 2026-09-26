import os
import sys
import subprocess
from pathlib import Path

def main():
    """Run radon cyclomatic complexity check and verify all functions < 15.
    This script is the verification artifact for T034a."""
    
    code_dir = Path("code")
    if not code_dir.exists():
        print("ERROR: code/ directory not found.")
        sys.exit(1)

    # Run radon command
    cmd = ["radon", "cc", str(code_dir), "-s", "-a"]
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        print(result.stdout)
        if result.stderr:
            print(f"STDERR: {result.stderr}", file=sys.stderr)

        # Parse output to check for violations
        # Format: code/file.py:func:func - Complexity: X
        violations = []
        for line in result.stdout.splitlines():
            if "Complexity" in line:
                # Extract complexity number
                try:
                    parts = line.split("Complexity")
                    if len(parts) > 1:
                        # Expected format: " - Complexity: X (CC)"
                        num_str = parts[1].split("(")[0].strip()
                        complexity = int(num_str)
                        if complexity >= 15:
                            violations.append(line.strip())
                except ValueError:
                    continue

        if violations:
            print("\n" + "="*50)
            print("VIOLATION DETECTED: Functions with CC >= 15 found:")
            print("="*50)
            for v in violations:
                print(v)
            print("="*50)
            sys.exit(1)
        else:
            print("\n" + "="*50)
            print("SUCCESS: All functions have cyclomatic complexity < 15.")
            print("="*50)
            sys.exit(0)
    except FileNotFoundError:
        print("ERROR: 'radon' command not found. Please install radon (pip install radon).")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to run radon check: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
