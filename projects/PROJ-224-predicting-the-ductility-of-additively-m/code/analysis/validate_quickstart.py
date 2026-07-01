"""
Task T039: Run quickstart.md validation.

This script validates the quickstart.md documentation by:
1. Parsing the quickstart.md file to extract command blocks.
2. Verifying that referenced files (scripts, data, artifacts) exist.
3. Simulating or executing key commands to ensure they run without error.
4. Reporting validation status.

Expected output: A validation report printed to stdout and a JSON summary saved to data/validation_results.json.
"""
import os
import sys
import time
import json
import logging
import subprocess
import re
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_commands_from_markdown(md_path: Path) -> list[str]:
    """
    Parse code blocks from markdown file that look like shell commands.
    Returns a list of command strings.
    """
    if not md_path.exists():
        logger.error(f"quickstart.md not found at {md_path}")
        return []
    
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract code blocks (assuming shell commands are in ```bash or ```sh blocks)
    # Also look for generic ``` blocks if no language specified
    pattern = r'```(?:bash|sh)?\n(.*?)```'
    matches = re.findall(pattern, content, re.DOTALL)
    
    commands = []
    for match in matches:
        lines = match.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                commands.append(line)
    
    return commands

def check_file_exists(path_str: str, base_dir: Path) -> bool:
    """Check if a referenced file exists relative to base_dir."""
    full_path = base_dir / path_str
    return full_path.exists()

def run_command(cmd: str, timeout: int = 60) -> tuple[bool, str]:
    """
    Execute a command and return (success, output).
    """
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=Path.cwd()
        )
        output = result.stdout + result.stderr
        success = result.returncode == 0
        return success, output
    except subprocess.TimeoutExpired:
        return False, f"Command timed out after {timeout}s"
    except Exception as e:
        return False, str(e)

def validate_quickstart():
    """Main validation logic."""
    start_time = time.time()
    project_root = Path.cwd()
    quickstart_path = project_root / "quickstart.md"
    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "file_exists": False,
        "commands_found": 0,
        "commands_passed": 0,
        "commands_failed": 0,
        "checks": [],
        "total_time_seconds": 0.0
    }

    # 1. Check if quickstart.md exists
    if not quickstart_path.exists():
        logger.error("quickstart.md not found in project root.")
        results["file_exists"] = False
        results["error"] = "quickstart.md not found"
    else:
        logger.info("quickstart.md found.")
        results["file_exists"] = True
        
        # 2. Parse commands
        commands = parse_commands_from_markdown(quickstart_path)
        results["commands_found"] = len(commands)
        logger.info(f"Found {len(commands)} potential commands in quickstart.md.")

        # 3. Validate and Run commands
        for cmd in commands:
            check_result = {
                "command": cmd,
                "passed": False,
                "reason": ""
            }

            # Pre-check: Does the script/file referenced exist?
            # Simple heuristic: if command starts with 'python code/', check file
            if cmd.startswith("python code/"):
                parts = cmd.split()
                if len(parts) >= 2:
                    script_path = parts[1]
                    if not check_file_exists(script_path, project_root):
                        check_result["reason"] = f"Referenced script not found: {script_path}"
                        results["checks"].append(check_result)
                        results["commands_failed"] += 1
                        continue

            # Execute command
            logger.info(f"Executing: {cmd}")
            success, output = run_command(cmd, timeout=30) # Short timeout for validation
            
            if success:
                check_result["passed"] = True
                results["commands_passed"] += 1
            else:
                check_result["passed"] = False
                check_result["reason"] = output[:200] # Truncate long output
                results["commands_failed"] += 1

            results["checks"].append(check_result)

    # 4. Summary
    elapsed = time.time() - start_time
    results["total_time_seconds"] = elapsed
    
    # Save results
    output_dir = project_root / "data"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "validation_results.json"
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Validation completed in {elapsed:.2f}s. Results saved to {output_file}")
    logger.info(f"Passed: {results['commands_passed']}, Failed: {results['commands_failed']}")

    # Print summary to stdout for immediate feedback
    print("\n--- Quickstart Validation Summary ---")
    print(f"File Found: {results['file_exists']}")
    print(f"Commands Found: {results['commands_found']}")
    print(f"Passed: {results['commands_passed']}")
    print(f"Failed: {results['commands_failed']}")
    if results['commands_failed'] > 0:
        print("\nFailed Commands:")
        for check in results['checks']:
            if not check['passed']:
                print(f"  - {check['command']}")
                print(f"    Reason: {check['reason']}")
    print("------------------------------------")

    return 0 if results['commands_failed'] == 0 else 1

def main():
    """Entry point."""
    sys.exit(validate_quickstart())

if __name__ == "__main__":
    main()