"""
Quickstart Validation Script for Social Memory Networks Project.

This script executes all commands defined in quickstart.md and verifies
that each command exits with code 0. It produces a validation report
to stdout and exits with non-zero if any command fails.

Usage:
    python code/validate_quickstart.py
"""
import argparse
import subprocess
import sys
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Define the commands from quickstart.md based on the project structure
# These commands are derived from the tasks and project requirements
QUICKSTART_COMMANDS = [
    {
        "name": "Install dependencies",
        "command": ["pip", "install", "-r", "code/requirements.txt"],
        "description": "Install pinned dependencies from requirements.txt"
    },
    {
        "name": "Run unit tests for metrics",
        "command": [
            "python", "-m", "pytest",
            "code/metrics/tests/test_specialization.py",
            "code/metrics/tests/test_retrieval.py",
            "code/metrics/tests/test_validator.py",
            "-v"
        ],
        "description": "Run unit tests for specialization, retrieval, and validator metrics"
    },
    {
        "name": "Run contract tests",
        "command": [
            "python", "-m", "pytest",
            "code/tests/contract/test_game_result.py",
            "code/tests/contract/test_anova.py",
            "code/tests/contract/test_scaling.py",
            "-v"
        ],
        "description": "Run contract tests for game results, ANOVA, and scaling"
    },
    {
        "name": "Run integration tests for full context",
        "command": [
            "python", "-m", "pytest",
            "code/tests/integration/test_full_context.py",
            "-v"
        ],
        "description": "Run integration tests for full-context simulation"
    },
    {
        "name": "Run integration tests for limited context",
        "command": [
            "python", "-m", "pytest",
            "code/tests/integration/test_limited_context.py",
            "-v"
        ],
        "description": "Run integration tests for limited-context simulation"
    },
    {
        "name": "Run unit tests for base agent",
        "command": [
            "python", "-m", "pytest",
            "code/tests/unit/test_base_agent.py",
            "-v"
        ],
        "description": "Run unit tests for base agent initialization and operations"
    },
    {
        "name": "Run unit tests for power analysis",
        "command": [
            "python", "-m", "pytest",
            "code/tests/unit/test_power.py",
            "-v"
        ],
        "description": "Run unit tests for power analysis functions"
    },
    {
        "name": "Run quantization audit",
        "command": [
            "python", "code/remove_quantization_imports.py",
            "--dir", "code"
        ],
        "description": "Verify no prohibited quantization imports exist"
    },
    {
        "name": "Run full pipeline profile",
        "command": [
            "python", "code/run_full_pipeline_profile.py",
            "--output", "results/pipeline_profile.json"
        ],
        "description": "Run full pipeline with resource profiling"
    }
]

def run_command(cmd: List[str], timeout: int = 600) -> Tuple[bool, str, int]:
    """
    Execute a command and return (success, output, exit_code).
    
    Args:
        cmd: Command and arguments as a list of strings
        timeout: Maximum execution time in seconds
        
    Returns:
        Tuple of (success, output, exit_code)
    """
    try:
        print(f"Executing: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=Path(__file__).parent.parent
        )
        
        output = result.stdout
        if result.stderr:
            output += "\n" + result.stderr
            
        return result.returncode == 0, output, result.returncode
    except subprocess.TimeoutExpired:
        return False, "Command timed out", -1
    except Exception as e:
        return False, str(e), -1

def validate_quickstart(
    commands: List[Dict[str, Any]],
    verbose: bool = False
) -> bool:
    """
    Execute all quickstart commands and verify exit codes.
    
    Args:
        commands: List of command dictionaries with 'name' and 'command' keys
        verbose: If True, print detailed output for each command
        
    Returns:
        True if all commands succeed, False otherwise
    """
    print("=" * 80)
    print("QUICKSTART VALIDATION REPORT")
    print("=" * 80)
    print(f"Total commands to validate: {len(commands)}")
    print(f"Working directory: {Path(__file__).parent.parent}")
    print("=" * 80)
    
    results = []
    total_start = time.time()
    
    for i, cmd_def in enumerate(commands, 1):
        name = cmd_def["name"]
        cmd = cmd_def["command"]
        description = cmd_def.get("description", "")
        
        print(f"\n[{i}/{len(commands)}] {name}")
        print(f"Description: {description}")
        print("-" * 40)
        
        success, output, exit_code = run_command(cmd)
        
        if verbose:
            print("Output:")
            print(output)
        
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"Status: {status} (exit code: {exit_code})")
        
        results.append({
            "name": name,
            "success": success,
            "exit_code": exit_code,
            "output": output
        })
        
        if not success:
            print(f"ERROR: Command '{name}' failed!")
    
    total_time = time.time() - total_start
    
    # Print summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for r in results if r["success"])
    failed = len(results) - passed
    
    print(f"Total commands: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total time: {total_time:.2f} seconds")
    
    if failed > 0:
        print("\nFailed commands:")
        for r in results:
            if not r["success"]:
                print(f"  - {r['name']} (exit code: {r['exit_code']})")
        print("\nValidation FAILED!")
        return False
    else:
        print("\nAll commands executed successfully!")
        print("Validation PASSED!")
        return True

def main():
    parser = argparse.ArgumentParser(
        description="Validate quickstart.md commands"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print detailed output for each command"
    )
    parser.add_argument(
        "--commands",
        type=str,
        nargs="+",
        help="Specific command names to validate (default: all)"
    )
    
    args = parser.parse_args()
    
    # Filter commands if specific names provided
    if args.commands:
        filtered_commands = [
            cmd for cmd in QUICKSTART_COMMANDS
            if cmd["name"] in args.commands
        ]
        if not filtered_commands:
            print(f"Error: No matching commands found for: {args.commands}")
            sys.exit(1)
    else:
        filtered_commands = QUICKSTART_COMMANDS
    
    success = validate_quickstart(filtered_commands, args.verbose)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()