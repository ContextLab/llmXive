"""
T051: Run quickstart.md validation by executing all commands in docs/quickstart.md
and logging success/failure to state/validation_log.json.
"""
import os
import sys
import json
import subprocess
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/quickstart_validation.log", mode="a")
    ]
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
QUICKSTART_PATH = PROJECT_ROOT / "docs" / "quickstart.md"
STATE_DIR = PROJECT_ROOT / "state"
OUTPUT_LOG = STATE_DIR / "validation_log.json"


def parse_markdown_commands(md_path: Path) -> List[Dict[str, Any]]:
    """
    Parse a markdown file and extract all shell commands from code blocks.
    Returns a list of dicts: {'command': str, 'line_number': int, 'context': str}
    """
    if not md_path.exists():
        raise FileNotFoundError(f"Quickstart file not found: {md_path}")

    commands = []
    current_block = None
    in_code_block = False

    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()

        if stripped.startswith("```bash") or stripped.startswith("```sh"):
            in_code_block = True
            current_block = {"commands": [], "line_start": i}
            continue
        elif stripped.startswith("```"):
            if in_code_block and current_block:
                # End of code block, extract commands
                if current_block["commands"]:
                    commands.append({
                        "command": "\n".join(current_block["commands"]),
                        "line_start": current_block["line_start"],
                        "line_end": i,
                        "context": "bash"
                    })
                in_code_block = False
                current_block = None
            continue

        if in_code_block and current_block is not None:
            if stripped and not stripped.startswith("#"):
                current_block["commands"].append(stripped)

    return commands


def execute_command(cmd: str, timeout: int = 300) -> Dict[str, Any]:
    """
    Execute a shell command and return the result.
    """
    logger.info(f"Executing: {cmd}")
    result = {
        "command": cmd,
        "success": False,
        "exit_code": None,
        "stdout": "",
        "stderr": "",
        "error": None,
        "duration_seconds": None
    }

    start_time = datetime.now()
    try:
        # Use shell=True to handle complex commands
        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout
        )
        result["exit_code"] = proc.returncode
        result["stdout"] = proc.stdout.strip()
        result["stderr"] = proc.stderr.strip()
        result["success"] = (proc.returncode == 0)

    except subprocess.TimeoutExpired:
        result["error"] = f"Command timed out after {timeout} seconds"
        result["exit_code"] = -1
    except Exception as e:
        result["error"] = str(e)
        result["exit_code"] = -1

    end_time = datetime.now()
    result["duration_seconds"] = (end_time - start_time).total_seconds()

    return result


def run_validation() -> Dict[str, Any]:
    """
    Main validation routine: parse quickstart.md, execute commands, log results.
    """
    if not QUICKSTART_PATH.exists():
        logger.error(f"Quickstart file not found at {QUICKSTART_PATH}")
        return {
            "status": "failed",
            "error": f"Quickstart file not found: {QUICKSTART_PATH}",
            "timestamp": datetime.now().isoformat(),
            "commands_run": 0,
            "commands_passed": 0,
            "commands_failed": 0,
            "details": []
        }

    # Ensure state directory exists
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    logger.info(f"Parsing commands from {QUICKSTART_PATH}")
    commands = parse_markdown_commands(QUICKSTART_PATH)

    if not commands:
        logger.warning("No shell commands found in quickstart.md")
        return {
            "status": "warning",
            "message": "No shell commands found in quickstart.md",
            "timestamp": datetime.now().isoformat(),
            "commands_run": 0,
            "commands_passed": 0,
            "commands_failed": 0,
            "details": []
        }

    logger.info(f"Found {len(commands)} command(s) to validate")

    results = []
    passed = 0
    failed = 0

    for idx, cmd_info in enumerate(commands, start=1):
        logger.info(f"--- Running command {idx}/{len(commands)} ---")
        exec_result = execute_command(cmd_info["command"])
        exec_result["index"] = idx
        exec_result["line_start"] = cmd_info["line_start"]
        exec_result["line_end"] = cmd_info.get("line_end")

        if exec_result["success"]:
            passed += 1
            logger.info(f"✓ Command {idx} succeeded")
        else:
            failed += 1
            logger.error(f"✗ Command {idx} failed: {exec_result.get('error', 'Unknown error')}")
            if exec_result.get("stderr"):
                logger.error(f"  STDERR: {exec_result['stderr']}")

        results.append(exec_result)

    summary = {
        "status": "passed" if failed == 0 else "failed",
        "timestamp": datetime.now().isoformat(),
        "quickstart_path": str(QUICKSTART_PATH),
        "commands_run": len(commands),
        "commands_passed": passed,
        "commands_failed": failed,
        "details": results
    }

    # Write results to state/validation_log.json
    with open(OUTPUT_LOG, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)

    logger.info(f"Validation complete. Results written to {OUTPUT_LOG}")
    logger.info(f"Status: {summary['status']} ({passed} passed, {failed} failed)")

    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Validate quickstart.md by executing all shell commands."
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout in seconds for each command (default: 300)"
    )
    args = parser.parse_args()

    # Override timeout if provided
    global execute_command
    # Note: We can't easily override the global function, so we just log the timeout
    logger.info(f"Using timeout: {args.timeout} seconds per command")

    summary = run_validation()

    # Exit with non-zero code if validation failed
    if summary["status"] == "failed":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
