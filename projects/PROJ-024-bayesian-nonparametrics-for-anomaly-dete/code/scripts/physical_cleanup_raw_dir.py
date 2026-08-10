"""
Task T105: Physical Cleanup of nested data/raw/raw/ directory.

Executes: rm -rf data/raw/raw/
Verification: find data/raw/ -type d -name raw
Output: Appends verification results to data/data_provenance_report.md
"""
import os
import subprocess
import sys
from pathlib import Path

def main():
    project_root = Path(__file__).resolve().parents[2]
    raw_dir = project_root / "data" / "raw"
    nested_raw_dir = raw_dir / "raw"
    report_path = project_root / "data" / "data_provenance_report.md"

    print(f"Target Directory: {nested_raw_dir}")
    print(f"Project Root: {project_root}")

    # Check if the nested directory exists
    if not nested_raw_dir.exists():
        print("INFO: Nested 'raw/' directory does not exist. No cleanup needed.")
        verification_output = "No nested 'raw/' directory found."
    else:
        print(f"INFO: Removing nested directory: {nested_raw_dir}")
        try:
            # Execute the removal command
            subprocess.run(
                ["rm", "-rf", str(nested_raw_dir)],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"SUCCESS: Removed {nested_raw_dir}")
            verification_output = f"Successfully removed {nested_raw_dir}"
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to remove directory: {e}")
            print(f"STDOUT: {e.stdout}")
            print(f"STDERR: {e.stderr}")
            sys.exit(1)

    # Verification step
    print("Running verification command: find data/raw/ -type d -name raw")
    try:
        result = subprocess.run(
            ["find", str(raw_dir), "-type", "d", "-name", "raw"],
            capture_output=True,
            text=True,
            check=False  # find returns non-zero if nothing found, which is expected
        )
        verification_cmd_output = result.stdout.strip()
        if result.returncode != 0 and not verification_cmd_output:
            # find returns non-zero if nothing found, which is the success case here
            verification_cmd_output = "" 
        
        if verification_cmd_output:
            print(f"WARNING: Verification failed. Found remaining directories:\n{verification_cmd_output}")
            status = "FAILED"
        else:
            print("SUCCESS: Verification passed. No nested 'raw/' directories remain.")
            status = "SUCCESS"
    except Exception as e:
        print(f"ERROR during verification: {e}")
        verification_cmd_output = str(e)
        status = "ERROR"

    # Append to report
    report_entry = f"""
## Task: T105
Physical Cleanup of nested data/raw/raw/ directory

## Execution
- **Action**: Removed {nested_raw_dir}
- **Status**: {status}

## Verification Command Output
```bash
find {raw_dir} -type d -name raw
```
**Result**: {verification_cmd_output if verification_cmd_output else "(empty - no nested directories found)"}

## Assert
- **Constraint**: Command must return empty output.
- **Result**: {'PASS' if status == 'SUCCESS' else 'FAIL'}
"""

    with open(report_path, "a") as f:
        f.write(report_entry)

    print(f"Verification report appended to {report_path}")

    if status != "SUCCESS":
        sys.exit(1)

if __name__ == "__main__":
    main()