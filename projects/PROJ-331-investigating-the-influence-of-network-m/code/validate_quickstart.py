"""
validate_quickstart.py
Python-based validation runner for quickstart.md.
This script parses the quickstart.md file, extracts commands, executes them,
and validates the resulting artifacts against the expected schema and existence.
"""

import os
import sys
import re
import json
import logging
import subprocess
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/logs/quickstart_validation.log')
    ]
)
logger = logging.getLogger(__name__)

def parse_quickstart(quickstart_path: str) -> list:
    """
    Parse quickstart.md to extract bash commands from code blocks.
    Returns a list of (description, command) tuples.
    """
    commands = []
    if not os.path.exists(quickstart_path):
        raise FileNotFoundError(f"Quickstart file not found: {quickstart_path}")

    with open(quickstart_path, 'r') as f:
        content = f.read()

    # Simple regex to find ```bash ... ``` blocks
    # This is a heuristic; a more robust parser might handle nested blocks or comments
    pattern = r'```bash\s+(.*?)\s+```'
    matches = re.findall(pattern, content, re.DOTALL)

    # Heuristic: try to associate descriptions with commands
    # We assume commands are grouped in blocks. We'll just extract the commands.
    # A more advanced version would parse headers for context.
    for match in matches:
        # Split into lines, filter empty
        lines = [line.strip() for line in match.split('\n') if line.strip()]
        if lines:
            # Assume the first line might be a comment or description, or just the command
            # For simplicity, we treat the whole block as a command sequence
            full_cmd = '\n'.join(lines)
            commands.append(("Quickstart Step", full_cmd))

    return commands

def validate_paths(project_root: str) -> bool:
    """Verify essential project directories and files exist."""
    required_paths = [
        os.path.join(project_root, 'code'),
        os.path.join(project_root, 'data'),
        os.path.join(project_root, 'data', 'logs'),
        os.path.join(project_root, 'requirements.txt'),
        os.path.join(project_root, 'quickstart.md')
    ]

    for path in required_paths:
        if not os.path.exists(path):
            logger.error(f"Required path missing: {path}")
            return False
    return True

def validate_commands(commands: list) -> bool:
    """
    Execute extracted commands and check for errors.
    Returns True if all commands succeed.
    """
    all_passed = True
    for i, (desc, cmd) in enumerate(commands):
        logger.info(f"Executing Step {i+1}: {desc}")
        logger.debug(f"Command: {cmd}")
        
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=300 # 5 minute timeout per step
            )
            
            if result.returncode != 0:
                logger.error(f"Step {i+1} failed with code {result.returncode}")
                logger.error(f"Stderr: {result.stderr}")
                all_passed = False
            else:
                logger.info(f"Step {i+1} passed.")
        except subprocess.TimeoutExpired:
            logger.error(f"Step {i+1} timed out.")
            all_passed = False
        except Exception as e:
            logger.error(f"Step {i+1} raised exception: {e}")
            all_passed = False
    
    return all_passed

def validate_prerequisites(project_root: str) -> bool:
    """Check that required Python packages are installed."""
    # Check for critical packages mentioned in requirements.txt
    critical_packages = ['numpy', 'pandas', 'networkx', 'scipy', 'nibabel']
    try:
        import importlib.util
        for pkg in critical_packages:
            if importlib.util.find_spec(pkg) is None:
                logger.warning(f"Package {pkg} not found. Might cause runtime issues.")
                # Don't fail immediately, as the pipeline might install them
        return True
    except Exception as e:
        logger.error(f"Error checking prerequisites: {e}")
        return False

def run_validation(project_root: str, quickstart_path: str) -> dict:
    """
    Main validation logic.
    Returns a report dictionary.
    """
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "project_root": project_root,
        "quickstart_path": quickstart_path,
        "prerequisites_check": False,
        "commands_executed": False,
        "outputs_validated": False,
        "status": "UNKNOWN",
        "details": []
    }

    # 1. Validate Prerequisites (Paths)
    logger.info("Checking project structure...")
    if not validate_paths(project_root):
        report["details"].append("Project structure validation failed.")
        report["status"] = "FAILED"
        return report
    
    report["prerequisites_check"] = True
    report["details"].append("Project structure valid.")

    # 2. Parse and Execute Commands
    logger.info("Parsing quickstart.md...")
    try:
        commands = parse_quickstart(quickstart_path)
        if not commands:
            logger.warning("No commands found in quickstart.md.")
            report["details"].append("No commands found in quickstart.md.")
        else:
            logger.info(f"Found {len(commands)} command blocks.")
            if validate_commands(commands):
                report["commands_executed"] = True
                report["details"].append("All commands executed successfully.")
            else:
                report["details"].append("Some commands failed.")
    except Exception as e:
        logger.error(f"Error during command execution: {e}")
        report["details"].append(f"Command execution error: {str(e)}")

    # 3. Validate Outputs
    logger.info("Validating output artifacts...")
    expected_outputs = [
        "data/processed/subject_list_manifest.json",
        "data/processed/canonical_binary_adj.npy",
        "data/processed/rsfc.npy",
        "data/processed/motif_profiles.json",
        "results/results.pdf",
        "data/logs/pipeline.log"
    ]
    
    missing_outputs = []
    for out in expected_outputs:
        full_path = os.path.join(project_root, out)
        if not os.path.exists(full_path):
            missing_outputs.append(out)
    
    if missing_outputs:
        report["details"].append(f"Missing outputs: {missing_outputs}")
    else:
        report["outputs_validated"] = True
        report["details"].append("All expected outputs found.")

    # Final Status
    if report["prerequisites_check"] and report["outputs_validated"]:
        report["status"] = "PASSED"
    else:
        report["status"] = "FAILED"

    return report

def save_report(report: dict, output_path: str):
    """Save the validation report to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Report saved to {output_path}")

def main():
    project_root = os.getenv('PROJECT_ROOT', os.getcwd())
    quickstart_path = os.path.join(project_root, 'quickstart.md')
    report_path = os.path.join(project_root, 'data/logs/quickstart_validation_report.json')

    # Ensure log directory exists
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    logger.info(f"Starting validation for project at {project_root}")
    report = run_validation(project_root, quickstart_path)
    save_report(report, report_path)

    if report["status"] == "PASSED":
        logger.info("Validation PASSED")
        sys.exit(0)
    else:
        logger.error("Validation FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()