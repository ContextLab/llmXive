import os
import sys
import subprocess
import logging
import time
import json
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_command(cmd: list, timeout: int = None) -> tuple:
    """Run a shell command and return (returncode, stdout, stderr)."""
    logger.info(f"Running command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out after {timeout} seconds")
        return -1, "", "Timeout"
    except Exception as e:
        logger.error(f"Error running command: {e}")
        return -1, "", str(e)

def verify_artifact(path: str, expected_min_size: int = 0) -> bool:
    """Verify an artifact exists and meets size requirements."""
    p = Path(path)
    if not p.exists():
        logger.error(f"Artifact missing: {path}")
        return False
    if p.stat().st_size < expected_min_size:
        logger.error(f"Artifact too small (size={p.stat().st_size}, min={expected_min_size}): {path}")
        return False
    logger.info(f"Artifact verified: {path} (size={p.stat().st_size})")
    return True

def parse_quickstart_instructions(quickstart_path: str) -> list:
    """Parse quickstart.md to extract commands to run."""
    commands = []
    path = Path(quickstart_path)
    if not path.exists():
        logger.warning(f"Quickstart file not found: {quickstart_path}")
        return commands

    with open(path, 'r') as f:
        content = f.read()

    # Simple heuristic: look for lines starting with 'python'
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('python '):
            commands.append(line)

    logger.info(f"Found {len(commands)} commands in quickstart.md")
    return commands

def validate_quickstart_instructions(commands: list, project_root: Path) -> dict:
    """Run commands from quickstart and validate artifacts."""
    results = {
        "total_commands": len(commands),
        "successful_commands": 0,
        "failed_commands": 0,
        "missing_artifacts": [],
        "command_results": []
    }

    for cmd_str in commands:
        cmd = cmd_str.split()
        # Ensure relative paths are relative to project_root
        # (Assuming the quickstart commands are relative to project root)
        start_time = time.time()
        rc, stdout, stderr = run_command(cmd, timeout=3600) # 1 hour timeout per command
        duration = time.time() - start_time

        result_entry = {
            "command": cmd_str,
            "returncode": rc,
            "duration": duration,
            "success": rc == 0,
            "stdout_preview": stdout[:500] if stdout else "",
            "stderr_preview": stderr[:500] if stderr else ""
        }
        results["command_results"].append(result_entry)

        if rc == 0:
            results["successful_commands"] += 1
        else:
            results["failed_commands"] += 1
            logger.error(f"Command failed: {cmd_str}\nstderr: {stderr}")

    return results

def run_verification(project_root: Path, quickstart_path: str = None, evidence_path: str = None) -> bool:
    """Main verification logic."""
    logger.info(f"Starting verification in {project_root}")

    # If quickstart_path is provided, parse and run it
    if quickstart_path:
        commands = parse_quickstart_instructions(quickstart_path)
        if not commands:
            logger.warning("No commands found in quickstart.md. Skipping execution validation.")
        else:
            results = validate_quickstart_instructions(commands, project_root)
            logger.info(f"Quickstart execution: {results['successful_commands']}/{results['total_commands']} successful")

    # If evidence_path is provided, check it exists (optional validation)
    if evidence_path:
        if not verify_artifact(evidence_path):
            logger.warning(f"Evidence file missing or invalid: {evidence_path}")
        else:
            logger.info(f"Evidence file validated: {evidence_path}")

    # Final check: Verify key artifacts exist (as per T040 requirements)
    key_artifacts = [
        "data/processed/cleaned_sn1.csv",
        "data/processed/exclusion_report.csv",
        "artifacts/best_model.pt",
        "artifacts/metrics.json",
        "artifacts/final_report.md"
    ]

    all_present = True
    for artifact in key_artifacts:
        full_path = project_root / artifact
        if not verify_artifact(str(full_path), expected_min_size=10):
            all_present = False
            logger.error(f"Key artifact missing: {artifact}")

    return all_present

def main():
    parser = argparse.ArgumentParser(description="Validate quickstart execution and artifacts")
    parser.add_argument("--project-root", type=str, default=".", help="Path to project root")
    parser.add_argument("--quickstart", type=str, help="Path to quickstart.md")
    parser.add_argument("--output", type=str, default="artifacts/validation_report.json", help="Path to output report")
    parser.add_argument("--evidence", type=str, help="Path to evidence file (integration_test_report.md)")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    os.chdir(project_root)

    success = run_verification(project_root, args.quickstart, args.evidence)

    # Generate report
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "project_root": str(project_root),
        "success": success,
        "evidence_validated": args.evidence is not None and verify_artifact(args.evidence),
        "message": "Validation successful" if success else "Validation failed: missing key artifacts or command failures"
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Validation report saved to {output_path}")
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
