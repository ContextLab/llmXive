"""
Quickstart Validation Script

This script validates the quickstart.md file by:
1. Parsing all bash code blocks
2. Executing each command in sequence
3. Verifying all commands return exit code 0
4. Generating a validation report
"""

import subprocess
import sys
import os
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple
import json


def extract_bash_commands(markdown_content: str) -> List[str]:
    """
    Extract bash commands from markdown code blocks.
    
    Args:
        markdown_content: The content of the markdown file
        
    Returns:
        List of bash commands to execute
    """
    # Pattern to match bash code blocks
    pattern = r'```bash\s*\n(.*?)\n```'
    matches = re.findall(pattern, markdown_content, re.DOTALL)
    
    commands = []
    for match in matches:
        # Split by newlines and filter out empty lines and comments
        lines = match.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                commands.append(line)
    
    return commands


def run_command(command: str, cwd: Path) -> Tuple[int, str, str]:
    """
    Run a single command and return its result.
    
    Args:
        command: The command to execute
        cwd: Working directory for the command
        
    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per command
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out after 5 minutes"
    except Exception as e:
        return -1, "", str(e)


def validate_quickstart(project_root: Path) -> Dict[str, Any]:
    """
    Validate the quickstart.md file by executing all commands.
    
    Args:
        project_root: The root directory of the project
        
    Returns:
        Validation report as a dictionary
    """
    quickstart_path = project_root / "quickstart.md"
    
    if not quickstart_path.exists():
        return {
            "success": False,
            "error": "quickstart.md not found",
            "commands_tested": 0,
            "commands_passed": 0,
            "commands_failed": 0,
            "results": []
        }
    
    # Read quickstart.md
    with open(quickstart_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract commands
    commands = extract_bash_commands(content)
    
    if not commands:
        return {
            "success": False,
            "error": "No commands found in quickstart.md",
            "commands_tested": 0,
            "commands_passed": 0,
            "commands_failed": 0,
            "results": []
        }
    
    # Execute commands
    results = []
    passed = 0
    failed = 0
    
    for i, command in enumerate(commands, 1):
        print(f"[{i}/{len(commands)}] Executing: {command}")
        exit_code, stdout, stderr = run_command(command, project_root)
        
        result = {
            "command": command,
            "exit_code": exit_code,
            "success": exit_code == 0,
            "stdout": stdout[:1000] if stdout else "",  # Truncate for readability
            "stderr": stderr[:1000] if stderr else ""
        }
        results.append(result)
        
        if exit_code == 0:
            passed += 1
            print(f"  ✓ Success")
        else:
            failed += 1
            print(f"  ✗ Failed (exit code: {exit_code})")
            if stderr:
                print(f"    Error: {stderr[:200]}")
    
    # Generate report
    report = {
        "timestamp": datetime.now().isoformat(),
        "quickstart_path": str(quickstart_path),
        "commands_tested": len(commands),
        "commands_passed": passed,
        "commands_failed": failed,
        "success": failed == 0,
        "results": results
    }
    
    return report


def save_report(report: Dict[str, Any], output_path: Path):
    """Save the validation report to a file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)

def main():
    """Main entry point for the validation script."""
    # Determine project root
    # Assume script is in code/ directory
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    print(f"Project root: {project_root}")
    print(f"Looking for: {project_root / 'quickstart.md'}")
    
    # Validate
    report = validate_quickstart(project_root)
    
    # Save report
    results_dir = project_root / "results"
    results_dir.mkdir(exist_ok=True)
    report_path = results_dir / "quickstart_validation_report.json"
    save_report(report, report_path)
    
    # Print summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    print(f"Commands tested: {report['commands_tested']}")
    print(f"Commands passed: {report['commands_passed']}")
    print(f"Commands failed: {report['commands_failed']}")
    print(f"Overall success: {'YES' if report['success'] else 'NO'}")
    print(f"Report saved to: {report_path}")
    print("="*60)
    
    # Exit with appropriate code
    sys.exit(0 if report['success'] else 1)


if __name__ == "__main__":
    main()
