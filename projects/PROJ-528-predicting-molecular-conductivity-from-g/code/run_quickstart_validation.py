"""
Utility script to parse and execute commands from quickstart.md for validation.
Used by T049 to ensure the run-book commands are correct.
"""
import os
import sys
import subprocess
import logging
import argparse
import re
from datetime import datetime

from code.logging_config import setup_logging

logger = setup_logging()

def parse_markdown_commands(md_path):
    """Parse code blocks from markdown file."""
    commands = []
    if not os.path.exists(md_path):
        raise FileNotFoundError(f"Markdown file not found: {md_path}")
    
    with open(md_path, 'r') as f:
        content = f.read()
    
    # Regex to find code blocks
    pattern = r'```(?:bash)?\s*(.*?)```'
    matches = re.findall(pattern, content, re.DOTALL)
    
    for match in matches:
        # Split lines and filter non-empty
        lines = [line.strip() for line in match.split('\n') if line.strip()]
        for line in lines:
            if line.startswith('#') or not line:
                continue
            commands.append(line)
    
    return commands

def execute_command(cmd):
    """Execute a shell command and return result."""
    logger.info(f"Executing: {cmd}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout per command
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

def run_validation(md_path="docs/quickstart.md"):
    """Run all commands in the quickstart guide."""
    commands = parse_markdown_commands(md_path)
    results = []
    all_passed = True

    logger.info(f"Found {len(commands)} commands to execute.")

    for i, cmd in enumerate(commands):
        logger.info(f"Step {i+1}/{len(commands)}: {cmd[:50]}...")
        rc, stdout, stderr = execute_command(cmd)
        
        status = "PASS" if rc == 0 else "FAIL"
        if rc != 0:
            all_passed = False
            logger.error(f"Command failed: {cmd}")
            logger.error(f"Stderr: {stderr}")
        
        results.append({
            "command": cmd,
            "return_code": rc,
            "status": status,
            "stdout": stdout[:500] if stdout else "",
            "stderr": stderr[:500] if stderr else ""
        })
    
    return all_passed, results

def main():
    parser = argparse.ArgumentParser(description="Run quickstart validation")
    parser.add_argument("--md-path", default="docs/quickstart.md", help="Path to quickstart.md")
    args = parser.parse_args()

    try:
        success, results = run_validation(args.md_path)
        
        log_path = "state/validation_log.json"
        if not os.exists("state"):
            os.makedirs("state")
        
        with open(log_path, "w") as f:
            import json
            json.dump({
                "task_id": "T051",
                "timestamp": datetime.now().isoformat(),
                "success": success,
                "results": results
            }, f, indent=2)
        
        if success:
            logger.info("All commands executed successfully.")
            sys.exit(0)
        else:
            logger.error("Some commands failed.")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
