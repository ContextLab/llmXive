"""
Physical Cleanup Script for T111.
Executes shell commands to remove nested 'raw/' directories and PEMS files.
Logs verification output to data/data_provenance_report.md.
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], description: str) -> tuple[bool, str]:
    """Run a shell command and return success status and output."""
    print(f"Executing: {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            cwd=Path(__file__).parent.parent.parent.parent  # Project root
        )
        output = result.stdout + result.stderr
        success = result.returncode == 0
        print(f"Return Code: {result.returncode}")
        if output.strip():
            print(f"Output:\n{output}")
        return success, output
    except Exception as e:
        return False, str(e)

def main():
    project_root = Path(__file__).parent.parent.parent.parent
    data_raw_dir = project_root / "data" / "raw"
    report_path = project_root / "data" / "data_provenance_report.md"

    # Ensure report file exists or append to it
    report_content = []
    report_content.append(f"# Data Provenance Report: T111 Physical Cleanup 2")
    report_content.append(f"Generated: {Path.cwd()}")
    report_content.append(f"")

    # Step 1: Remove nested 'raw/' directories
    print("\n--- Step 1: Removing nested 'raw/' directories ---")
    cmd_raw = [
        "find", str(data_raw_dir), "-type", "d", "-name", "raw", "-exec", "rm", "-rf", "{}", "+"
    ]
    success_raw, output_raw = run_command(cmd_raw, "Remove nested raw directories")
    
    report_content.append("## Step 1: Remove nested 'raw/' directories")
    report_content.append(f"**Command**: `find data/raw/ -type d -name raw -exec rm -rf {{}} +`")
    report_content.append(f"**Status**: {'SUCCESS' if success_raw else 'FAILED'}")
    report_content.append(f"**Output**:\n```")
    report_content.append(output_raw if output_raw else "(No output)")
    report_content.append("```\n")

    # Verification for Step 1
    cmd_verify_raw = ["find", str(data_raw_dir), "-type", "d", "-name", "raw"]
    _, verify_output_raw = run_command(cmd_verify_raw, "Verify no nested raw dirs")
    if verify_output_raw.strip():
        report_content.append(f"**Verification Failed**: Nested directories still exist:\n{verify_output_raw}")
        success_raw = False
    else:
        report_content.append("**Verification**: No nested 'raw/' directories found.")

    # Step 2: Remove PEMS files
    print("\n--- Step 2: Removing PEMS files ---")
    cmd_pems = [
        "find", str(data_raw_dir), "-name", "*pems*", "-delete"
    ]
    success_pems, output_pems = run_command(cmd_pems, "Remove PEMS files")

    report_content.append("## Step 2: Remove PEMS files")
    report_content.append(f"**Command**: `find data/raw/ -name \"*pems*\" -delete`")
    report_content.append(f"**Status**: {'SUCCESS' if success_pems else 'FAILED'}")
    report_content.append(f"**Output**:\n```")
    report_content.append(output_pems if output_pems else "(No output)")
    report_content.append("```\n")

    # Verification for Step 2
    cmd_verify_pems = ["ls", "-la", str(data_raw_dir)]
    _, verify_output_pems = run_command(cmd_verify_pems, "List data/raw/ contents")
    
    report_content.append("## Verification")
    report_content.append("### Final State of data/raw/")
    report_content.append("```bash")
    report_content.append(verify_output_pems)
    report_content.append("```")

    # Check for remaining pems files
    if "pems" in verify_output_pems.lower():
        report_content.append("\n**CRITICAL**: PEMS files still detected in data/raw/")
        success_pems = False
    else:
        report_content.append("\n**Verification**: No PEMS files detected in data/raw/")

    # Final Summary
    report_content.append("\n## Summary")
    if success_raw and success_pems:
        report_content.append("✅ **T111 Physical Cleanup 2: SUCCESS**")
        report_content.append("- Nested 'raw/' directories removed.")
        report_content.append("- PEMS files removed.")
    else:
        report_content.append("❌ **T111 Physical Cleanup 2: FAILED**")
        if not success_raw:
            report_content.append("- Failed to remove nested 'raw/' directories or verification failed.")
        if not success_pems:
            report_content.append("- Failed to remove PEMS files or verification failed.")

    # Write report
    report_content_str = "\n".join(report_content)
    with open(report_path, "w") as f:
        f.write(report_content_str)
    
    print(f"\nReport saved to: {report_path}")
    
    # Exit with error if cleanup failed
    if not (success_raw and success_pems):
        sys.exit(1)

if __name__ == "__main__":
    main()
