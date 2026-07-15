import os
import sys
import time
import json
import logging
import subprocess
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_commands_from_markdown(file_path: Path) -> list:
    """
    Parses a markdown file to extract shell commands intended for execution.
    Looks for code blocks marked with 'bash' or 'sh'.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    commands = []
    in_code_block = False
    current_command = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith('```bash') or stripped.startswith('```sh'):
                in_code_block = True
                continue
            if stripped.startswith('```'):
                if in_code_block:
                    if current_command:
                        cmd_str = ' '.join(current_command)
                        if cmd_str:
                            commands.append(cmd_str)
                        current_command = []
                    in_code_block = False
                continue

            if in_code_block:
                # Skip empty lines within a command block if they separate logical steps,
                # but here we assume a continuous block represents a sequence or a single command.
                # We'll join lines to handle multi-line commands if necessary, or treat as sequence.
                # For simplicity in quickstart validation, we treat non-empty lines as part of the command.
                if stripped:
                    current_command.append(stripped)

    return commands

def check_file_exists(file_path: str, base_dir: Path) -> bool:
    """Checks if a relative file path exists from the base directory."""
    full_path = base_dir / file_path
    if full_path.exists():
        logger.info(f"Found: {full_path}")
        return True
    else:
        logger.warning(f"Missing: {full_path}")
        return False

def run_command(cmd: str, timeout: int = 300) -> dict:
    """
    Executes a shell command and returns the result status and output.
    """
    logger.info(f"Executing: {cmd}")
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            timeout=timeout
        )
        elapsed = time.time() - start_time
        return {
            "command": cmd,
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "elapsed_seconds": elapsed
        }
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out after {timeout}s: {cmd}")
        return {
            "command": cmd,
            "success": False,
            "return_code": -1,
            "stdout": "",
            "stderr": f"Timeout expired after {timeout} seconds",
            "elapsed_seconds": timeout
        }
    except Exception as e:
        logger.error(f"Error running command: {e}")
        return {
            "command": cmd,
            "success": False,
            "return_code": -1,
            "stdout": "",
            "stderr": str(e),
            "elapsed_seconds": 0
        }

def validate_quickstart(quickstart_path: str = "quickstart.md") -> dict:
    """
    Main validation routine for quickstart.md.
    1. Parses commands.
    2. Checks file existence for any 'ls', 'cat', or explicit path checks.
    3. Runs commands.
    4. Aggregates results.
    """
    base_dir = Path.cwd()
    qs_path = base_dir / quickstart_path

    if not qs_path.exists():
        return {
            "status": "failed",
            "error": f"quickstart.md not found at {qs_path}",
            "results": []
        }

    commands = parse_commands_from_markdown(qs_path)
    logger.info(f"Found {len(commands)} commands in {quickstart_path}")

    results = []
    all_passed = True

    for cmd in commands:
        # Simple heuristic: if command is just a path or 'ls path', check existence
        # This is a lightweight check before running potentially destructive commands
        # In a real scenario, we might parse the command more deeply.
        # For now, we just run it and capture output.
        res = run_command(cmd)
        results.append(res)
        if not res["success"]:
            all_passed = False
            # Log the error but continue to validate other steps if possible
            # unless it's a critical dependency failure.
            # For T039, we just report the status.

    summary = {
        "status": "passed" if all_passed else "failed",
        "total_commands": len(commands),
        "passed_commands": sum(1 for r in results if r["success"]),
        "failed_commands": sum(1 for r in results if not r["success"]),
        "details": results
    }

    # Write the validation log to data/
    log_path = base_dir / "data" / "quickstart_validation_log.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Validation log written to {log_path}")
    logger.info(f"Final Status: {summary['status']}")

    return summary

def main():
    """Entry point for the quickstart validation script."""
    logger.info("Starting quickstart validation (Task T039)...")
    result = validate_quickstart("quickstart.md")

    if result["status"] == "failed":
        logger.error("Quickstart validation failed.")
        sys.exit(1)
    else:
        logger.info("Quickstart validation passed.")
        sys.exit(0)

if __name__ == "__main__":
    main()
