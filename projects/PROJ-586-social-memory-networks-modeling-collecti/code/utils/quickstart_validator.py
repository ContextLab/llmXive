"""
Quickstart Validation Script

This script validates the quickstart.md file by:
1. Parsing all shell commands from the markdown file
2. Executing each command in the correct directory
3. Verifying exit codes are 0
4. Generating a validation report

Usage:
    python code/utils/quickstart_validator.py --quickstart path/to/quickstart.md
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def extract_commands_from_markdown(markdown_path: Path) -> List[Dict[str, Any]]:
    """
    Extract shell commands from a markdown file.

    Looks for code blocks marked with ```bash, ```sh, or ```shell
    Returns a list of dictionaries with command, line_number, and block_type.
    """
    commands = []
    current_block = None
    block_start_line = 0

    with open(markdown_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Check for code block start
        if stripped.startswith('```bash') or stripped.startswith('```sh') or stripped.startswith('```shell'):
            current_block = []
            block_start_line = i
            continue

        # Check for code block end
        if stripped == '```' and current_block is not None:
            command_text = '\n'.join(current_block)
            # Skip empty blocks or blocks with only comments
            if command_text.strip() and not command_text.strip().startswith('#'):
                commands.append({
                    'command': command_text,
                    'line_number': block_start_line,
                    'block_type': 'shell'
                })
            current_block = None
            continue

        # Add line to current block
        if current_block is not None:
            current_block.append(line.rstrip())

    return commands

def run_command(command: str, cwd: Path, timeout: int = 300) -> Tuple[int, str, str]:
    """
    Execute a shell command and return exit code, stdout, stderr.

    Args:
        command: The command string to execute
        cwd: Working directory for the command
        timeout: Maximum execution time in seconds

    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    try:
        # Split command into lines if it's multi-line
        lines = [line.strip() for line in command.split('\n') if line.strip() and not line.strip().startswith('#')]

        if not lines:
            return 0, "", ""

        # Join commands with && to execute sequentially
        full_command = ' && '.join(lines)

        result = subprocess.run(
            full_command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        return result.returncode, result.stdout, result.stderr

    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout} seconds"
    except Exception as e:
        return -1, "", str(e)

def validate_quickstart(quickstart_path: Path, project_dir: Path) -> Dict[str, Any]:
    """
    Validate all commands in the quickstart.md file.

    Args:
        quickstart_path: Path to the quickstart.md file
        project_dir: Project root directory to execute commands from

    Returns:
        Dictionary with validation results
    """
    if not quickstart_path.exists():
        return {
            'success': False,
            'error': f"Quickstart file not found: {quickstart_path}",
            'commands': []
        }

    if not project_dir.exists():
        return {
            'success': False,
            'error': f"Project directory not found: {project_dir}",
            'commands': []
        }

    commands = extract_commands_from_markdown(quickstart_path)

    if not commands:
        return {
            'success': False,
            'error': "No commands found in quickstart.md",
            'commands': []
        }

    results = []
    all_passed = True

    print(f"\n{Colors.BOLD}Validating quickstart.md...{Colors.RESET}\n")
    print(f"Project directory: {project_dir}")
    print(f"Quickstart file: {quickstart_path}")
    print(f"Found {len(commands)} command(s) to validate\n")

    for i, cmd_info in enumerate(commands, 1):
        command = cmd_info['command']
        line_num = cmd_info['line_number']

        # Truncate long commands for display
        display_cmd = command[:100] + "..." if len(command) > 100 else command

        print(f"{Colors.BLUE}[{i}/{len(commands)}] Line {line_num}:{Colors.RESET} {display_cmd}")

        exit_code, stdout, stderr = run_command(command, project_dir)

        if exit_code == 0:
            print(f"  {Colors.GREEN}✓ PASSED{Colors.RESET}")
            status = "passed"
        else:
            print(f"  {Colors.RED}✗ FAILED (exit code: {exit_code}){Colors.RESET}")
            if stderr:
                print(f"  Error: {stderr[:200]}")
            all_passed = False
            status = "failed"

        results.append({
            'command': command,
            'line_number': line_num,
            'exit_code': exit_code,
            'status': status,
            'stdout': stdout,
            'stderr': stderr
        })

        print()

    return {
        'success': all_passed,
        'total_commands': len(commands),
        'passed_commands': sum(1 for r in results if r['status'] == 'passed'),
        'failed_commands': sum(1 for r in results if r['status'] == 'failed'),
        'commands': results,
        'timestamp': datetime.now().isoformat()
    }

def generate_report(results: Dict[str, Any], output_path: Optional[Path] = None) -> str:
    """
    Generate a validation report and optionally save it to a file.

    Args:
        results: Validation results dictionary
        output_path: Optional path to save the report

    Returns:
        Report string
    """
    report_lines = [
        "=" * 80,
        "QUICKSTART VALIDATION REPORT",
        "=" * 80,
        f"Timestamp: {results['timestamp']}",
        f"Total Commands: {results['total_commands']}",
        f"Passed: {results['passed_commands']}",
        f"Failed: {results['failed_commands']}",
        f"Overall Status: {'PASSED' if results['success'] else 'FAILED'}",
        "=" * 80,
        ""
    ]

    for i, cmd_result in enumerate(results['commands'], 1):
        status_icon = "✓" if cmd_result['status'] == 'passed' else "✗"
        report_lines.append(f"[{i}] Line {cmd_result['line_number']}: {status_icon} {cmd_result['status'].upper()}")
        report_lines.append(f"    Command: {cmd_result['command'][:100]}...")
        if cmd_result['exit_code'] != 0:
            report_lines.append(f"    Exit Code: {cmd_result['exit_code']}")
            if cmd_result['stderr']:
                report_lines.append(f"    Error: {cmd_result['stderr'][:200]}")
        report_lines.append("")

    report = "\n".join(report_lines)

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)

    return report

def main():
    """Main entry point for the quickstart validator."""
    parser = argparse.ArgumentParser(
        description='Validate quickstart.md by executing all commands and checking exit codes.'
    )
    parser.add_argument(
        '--quickstart',
        type=str,
        default='quickstart.md',
        help='Path to the quickstart.md file (default: quickstart.md)'
    )
    parser.add_argument(
        '--project-dir',
        type=str,
        default='.',
        help='Project directory to execute commands from (default: current directory)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Optional path to save the validation report'
    )

    args = parser.parse_args()

    # Resolve paths
    quickstart_path = Path(args.quickstart)
    project_dir = Path(args.project_dir).resolve()

    # If quickstart is relative, look in project_dir
    if not quickstart_path.is_absolute():
        quickstart_path = project_dir / quickstart_path

    # Run validation
    results = validate_quickstart(quickstart_path, project_dir)

    # Generate report
    report = generate_report(results, Path(args.output) if args.output else None)
    print(report)

    # Print summary with colors
    if results['success']:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ All commands passed validation!{Colors.RESET}\n")
        sys.exit(0)
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ Some commands failed validation!{Colors.RESET}\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
