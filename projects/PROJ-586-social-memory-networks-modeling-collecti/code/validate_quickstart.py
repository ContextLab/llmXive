"""
T031: Validate quickstart.md execution.

This script parses quickstart.md, extracts shell commands, executes them
in the project root, and verifies that each returns exit code 0.
It writes a validation report to results/quickstart_validation.json.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Project root relative to this script
PROJECT_ROOT = Path(__file__).parent.parent
QUICKSTART_PATH = PROJECT_ROOT / "quickstart.md"
RESULTS_DIR = PROJECT_ROOT / "results"
VALIDATION_REPORT_PATH = RESULTS_DIR / "quickstart_validation.json"

# Regex to extract code blocks from markdown
CODE_BLOCK_PATTERN = re.compile(r'```(?:bash|sh|shell)?\n(.*?)```', re.DOTALL)


def extract_commands_from_markdown(md_path: Path) -> List[str]:
    """Extract all shell commands from markdown code blocks."""
    if not md_path.exists():
        raise FileNotFoundError(f"quickstart.md not found at {md_path}")
    
    content = md_path.read_text(encoding='utf-8')
    blocks = CODE_BLOCK_PATTERN.findall(content)
    
    commands = []
    for block in blocks:
        # Split by newlines and filter empty lines and comments
        lines = [line.strip() for line in block.split('\n') if line.strip() and not line.strip().startswith('#')]
        if lines:
            # Join non-empty lines as a single command (handles multi-line commands)
            cmd = ' '.join(lines)
            commands.append(cmd)
    
    return commands


def execute_command(cmd: str, cwd: Path, timeout_seconds: int = 300) -> Dict[str, Any]:
    """Execute a single command and capture results."""
    result = {
        "command": cmd,
        "cwd": str(cwd),
        "exit_code": None,
        "stdout": "",
        "stderr": "",
        "success": False,
        "error": None
    }
    
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )
        result["exit_code"] = proc.returncode
        result["stdout"] = proc.stdout
        result["stderr"] = proc.stderr
        result["success"] = (proc.returncode == 0)
        if not result["success"]:
            result["error"] = f"Command failed with exit code {proc.returncode}"
    except subprocess.TimeoutExpired:
        result["error"] = f"Command timed out after {timeout_seconds} seconds"
        result["exit_code"] = -1
    except Exception as e:
        result["error"] = str(e)
        result["exit_code"] = -1
    
    return result


def run_validation(quickstart_path: Optional[Path] = None, output_path: Optional[Path] = None) -> Dict[str, Any]:
    """Run the full validation process."""
    start_time = datetime.utcnow()
    
    if quickstart_path is None:
        quickstart_path = QUICKSTART_PATH
    if output_path is None:
        output_path = VALIDATION_REPORT_PATH
    
    # Ensure results directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        "timestamp": start_time.isoformat(),
        "quickstart_path": str(quickstart_path),
        "validation_directory": str(PROJECT_ROOT),
        "total_commands": 0,
        "successful_commands": 0,
        "failed_commands": 0,
        "all_passed": False,
        "results": []
    }
    
    try:
        commands = extract_commands_from_markdown(quickstart_path)
        report["total_commands"] = len(commands)
        
        if len(commands) == 0:
            report["error"] = "No commands found in quickstart.md"
            return report
        
        for i, cmd in enumerate(commands, 1):
            print(f"[{i}/{len(commands)}] Executing: {cmd[:80]}...")
            result = execute_command(cmd, PROJECT_ROOT)
            report["results"].append(result)
            
            if result["success"]:
                report["successful_commands"] += 1
                print(f"  -> SUCCESS (exit code: {result['exit_code']})")
            else:
                report["failed_commands"] += 1
                print(f"  -> FAILED (exit code: {result['exit_code']})")
                print(f"     Error: {result['error']}")
                if result['stderr']:
                    print(f"     Stderr: {result['stderr'][:200]}")
        
        report["all_passed"] = (report["failed_commands"] == 0)
        
    except Exception as e:
        report["error"] = f"Validation failed: {str(e)}"
        report["all_passed"] = False
    
    end_time = datetime.utcnow()
    report["duration_seconds"] = (end_time - start_time).total_seconds()
    
    # Write report
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    
    return report


def main():
    parser = argparse.ArgumentParser(description="Validate quickstart.md execution")
    parser.add_argument("--quickstart", type=Path, help="Path to quickstart.md")
    parser.add_argument("--output", type=Path, help="Path to output report")
    args = parser.parse_args()
    
    report = run_validation(args.quickstart, args.output)
    
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    print(f"Total commands: {report['total_commands']}")
    print(f"Successful: {report['successful_commands']}")
    print(f"Failed: {report['failed_commands']}")
    print(f"All passed: {report['all_passed']}")
    print(f"Duration: {report['duration_seconds']:.2f}s")
    print(f"Report saved to: {VALIDATION_REPORT_PATH}")
    
    if not report['all_passed']:
        print("\nFAILED COMMANDS:")
        for r in report['results']:
            if not r['success']:
                print(f"  - {r['command']}")
                print(f"    Error: {r['error']}")
        sys.exit(1)
    else:
        print("\n✓ All commands in quickstart.md executed successfully.")
        sys.exit(0)


if __name__ == "__main__":
    main()
