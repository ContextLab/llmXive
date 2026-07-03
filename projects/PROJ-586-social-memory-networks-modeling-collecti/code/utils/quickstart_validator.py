"""Quickstart validation runner.

Executes all commands listed in quickstart.md and verifies that each exits
with code 0. Produces a validation report in the project's results directory.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple

import yaml

# Import logging utilities from the project's established logger
from utils.logging import get_logger

logger = get_logger(__name__)


def parse_quickstart_commands(quickstart_path: Path) -> List[str]:
    """Parse commands from quickstart.md.

    Extracts shell commands from code blocks in the markdown file.
    Looks for lines starting with '$ ' or 'python ' or 'pip ' inside
    code blocks.
    """
    if not quickstart_path.exists():
        raise FileNotFoundError(f"quickstart.md not found at {quickstart_path}")

    content = quickstart_path.read_text(encoding="utf-8")
    commands = []

    # Simple parser: extract commands from markdown code blocks
    # We look for lines that look like shell commands
    in_code_block = False
    for line in content.splitlines():
        stripped = line.strip()

        # Detect code block start/end
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue

        if not in_code_block:
            continue

        # Extract command lines (skip prompts like '$' or '>', and empty lines)
        if stripped.startswith("$ "):
            cmd = stripped[2:].strip()
            if cmd:
                commands.append(cmd)
        elif stripped.startswith("python ") or stripped.startswith("pip "):
            commands.append(stripped)
        elif stripped.startswith("#") or stripped.startswith("//"):
            # Skip comments
            continue
        elif stripped and not stripped.startswith("#"):
            # Check if it looks like a command (contains spaces, starts with common cmd)
            parts = stripped.split()
            if parts and parts[0] in ("python", "pip", "pytest", "black", "flake8", "python3"):
                commands.append(stripped)

    return commands


def run_command(cmd: str, cwd: Path, timeout: int = 300) -> Tuple[int, str, str]:
    """Run a single command and return (exit_code, stdout, stderr)."""
    logger.log("run_command", command=cmd, cwd=str(cwd))
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        logger.log("command_timeout", command=cmd, timeout=timeout)
        return -1, "", f"Command timed out after {timeout}s"
    except Exception as e:
        logger.log("command_error", command=cmd, error=str(e))
        return -1, "", str(e)


def validate_quickstart(
    project_root: Path, quickstart_path: Path | None = None
) -> Dict[str, Any]:
    """Run all commands from quickstart.md and validate exit codes.

    Args:
        project_root: Root directory of the project
        quickstart_path: Optional path to quickstart.md (defaults to project_root/quickstart.md)

    Returns:
        Dictionary with validation results
    """
    if quickstart_path is None:
        quickstart_path = project_root / "quickstart.md"

    if not quickstart_path.exists():
        # Try common locations
        possible_paths = [
            project_root / "quickstart.md",
            project_root / "docs" / "quickstart.md",
            project_root / "projects" / project_root.name / "quickstart.md",
        ]
        for p in possible_paths:
            if p.exists():
                quickstart_path = p
                break
        else:
            raise FileNotFoundError(
                "quickstart.md not found in any expected location"
            )

    # Determine working directory (code/ subdirectory if it exists)
    working_dir = project_root / "code"
    if not working_dir.exists():
        working_dir = project_root

    logger.log("validation_start", quickstart=str(quickstart_path), working_dir=str(working_dir))

    commands = parse_quickstart_commands(quickstart_path)

    if not commands:
        logger.log("validation_warning", message="No commands found in quickstart.md")
        return {
            "status": "warning",
            "message": "No commands found in quickstart.md",
            "commands_tested": 0,
            "passed": 0,
            "failed": 0,
            "results": [],
        }

    results = []
    passed = 0
    failed = 0

    for i, cmd in enumerate(commands, 1):
        logger.log("executing_command", index=i, command=cmd)
        exit_code, stdout, stderr = run_command(cmd, working_dir)

        success = exit_code == 0
        if success:
            passed += 1
            status = "passed"
        else:
            failed += 1
            status = "failed"

        result = {
            "index": i,
            "command": cmd,
            "exit_code": exit_code,
            "status": status,
            "stdout": stdout[:1000] if stdout else "",  # Truncate for readability
            "stderr": stderr[:1000] if stderr else "",
        }
        results.append(result)

        if success:
            logger.log("command_passed", index=i, command=cmd[:50])
        else:
            logger.log("command_failed", index=i, command=cmd[:50], exit_code=exit_code)

    overall_status = "passed" if failed == 0 else "failed"

    return {
        "status": overall_status,
        "quickstart_path": str(quickstart_path),
        "working_dir": str(working_dir),
        "timestamp": datetime.utcnow().isoformat(),
        "commands_tested": len(commands),
        "passed": passed,
        "failed": failed,
        "results": results,
    }


def write_report(report: Dict[str, Any], output_path: Path) -> None:
    """Write validation report to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    logger.log("report_written", path=str(output_path))


def build_parser() -> argparse.ArgumentParser:
    """Build command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Validate quickstart.md by executing all commands"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Path to project root (default: current directory)",
    )
    parser.add_argument(
        "--quickstart",
        type=Path,
        default=None,
        help="Path to quickstart.md (default: project_root/quickstart.md)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path for validation report (default: project_root/results/quickstart_validation.json)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    return parser


def main() -> int:
    """Main entry point for quickstart validation."""
    parser = build_parser()
    args = parser.parse_args()

    # Set up logging if verbose
    if args.verbose:
        logger.log("verbose_mode", enabled=True)

    try:
        report = validate_quickstart(args.project_root, args.quickstart)

        # Determine output path
        if args.output:
            output_path = args.output
        else:
            results_dir = args.project_root / "results"
            output_path = results_dir / "quickstart_validation.json"

        write_report(report, output_path)

        # Print summary
        status_symbol = "✅" if report["status"] == "passed" else "❌"
        print(f"\n{status_symbol} Quickstart Validation: {report['status'].upper()}")
        print(f"  Commands tested: {report['commands_tested']}")
        print(f"  Passed: {report['passed']}")
        print(f"  Failed: {report['failed']}")
        print(f"  Report saved to: {output_path}")

        if report["results"]:
            print("\n  Detailed Results:")
            for r in report["results"]:
                symbol = "✅" if r["status"] == "passed" else "❌"
                cmd_short = r["command"][:60] + "..." if len(r["command"]) > 60 else r["command"]
                print(f"    {symbol} [{r['index']}] {cmd_short}")

        return 0 if report["status"] == "passed" else 1

    except Exception as e:
        logger.log("validation_error", error=str(e))
        print(f"❌ Validation failed with error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
