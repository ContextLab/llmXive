import os
import sys
import subprocess
import logging
import time
import json
import argparse
from pathlib import Path

from utils.logger import setup_logging, get_logger

def run_command(cmd: list, cwd: Path = None, timeout: int = 300) -> tuple:
    """
    Execute a shell command and return (success, stdout, stderr, return_code).
    """
    logger = get_logger()
    try:
        logger.info(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return (result.returncode == 0, result.stdout, result.stderr, result.returncode)
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out after {timeout}s: {' '.join(cmd)}")
        return (False, "", "Command timed out", -1)
    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        return (False, "", str(e), -1)

def verify_artifact(path: Path, expected_non_empty: bool = True) -> tuple:
    """
    Check if a file exists and optionally if it is non-empty.
    Returns (success, message).
    """
    logger = get_logger()
    if not path.exists():
        msg = f"Artifact missing: {path}"
        logger.error(msg)
        return (False, msg)
    
    if expected_non_empty:
        size = path.stat().st_size
        if size == 0:
            msg = f"Artifact empty: {path}"
            logger.error(msg)
            return (False, msg)
        logger.info(f"Artifact verified (size={size}): {path}")
    else:
        logger.info(f"Artifact verified (exists): {path}")
    
    return (True, f"Artifact exists: {path}")

def parse_quickstart_instructions(quickstart_path: Path) -> list:
    """
    Parse quickstart.md to extract command lines and expected artifact paths.
    Returns a list of dicts: {'command': str, 'expected_artifacts': [str]}
    """
    logger = get_logger()
    instructions = []
    
    if not quickstart_path.exists():
        logger.error(f"quickstart.md not found at {quickstart_path}")
        return instructions

    with open(quickstart_path, 'r') as f:
        content = f.read()

    # Simple heuristic: look for lines starting with 'python' or 'bash'
    # and lines mentioning 'data/', 'artifacts/', 'figures/' as expected outputs
    current_cmd = None
    current_artifacts = []
    
    for line in content.split('\n'):
        stripped = line.strip()
        
        # Detect command start (e.g., `python code/data/ingest.py`)
        if stripped.startswith('python ') or stripped.startswith('bash '):
            if current_cmd:
                instructions.append({
                    'command': current_cmd,
                    'expected_artifacts': current_artifacts
                })
            current_cmd = stripped
            current_artifacts = []
        elif current_cmd and (stripped.startswith('data/') or stripped.startswith('artifacts/') or stripped.startswith('figures/')):
            # Heuristic: if line mentions output paths, add to expected artifacts
            # Clean up the path (remove quotes, backticks, etc.)
            clean_path = stripped.replace('`', '').replace('"', '').replace("'", '').split()[0]
            current_artifacts.append(clean_path)

    if current_cmd:
        instructions.append({
            'command': current_cmd,
            'expected_artifacts': current_artifacts
        })

    logger.info(f"Parsed {len(instructions)} instructions from quickstart.md")
    return instructions

def validate_quickstart_instructions(instructions: list, project_root: Path) -> dict:
    """
    Execute instructions from quickstart.md and verify expected artifacts.
    Returns a validation report dict.
    """
    logger = get_logger()
    report = {
        'total_instructions': len(instructions),
        'passed': 0,
        'failed': 0,
        'details': []
    }

    for i, instr in enumerate(instructions):
        cmd_str = instr['command']
        expected_artifacts = instr['expected_artifacts']
        
        logger.info(f"Validating instruction {i+1}/{len(instructions)}: {cmd_str}")
        
        # Parse command
        parts = cmd_str.split()
        if not parts:
            continue
        
        success, stdout, stderr, return_code = run_command(parts, cwd=project_root)
        
        step_result = {
            'instruction_index': i,
            'command': cmd_str,
            'success': success,
            'return_code': return_code,
            'artifacts_verified': [],
            'errors': []
        }

        if not success:
            step_result['errors'].append(f"Command failed with code {return_code}: {stderr}")
            report['failed'] += 1
        else:
            # Verify artifacts
            all_artifacts_ok = True
            for artifact_rel in expected_artifacts:
                artifact_path = project_root / artifact_rel
                ok, msg = verify_artifact(artifact_path)
                if ok:
                    step_result['artifacts_verified'].append(artifact_rel)
                else:
                    step_result['errors'].append(msg)
                    all_artifacts_ok = False
            
            if all_artifacts_ok and not step_result['errors']:
                report['passed'] += 1
            else:
                report['failed'] += 1

        report['details'].append(step_result)

    return report

def run_verification(quickstart_path: Path, project_root: Path, output_path: Path):
    """
    Main verification routine.
    """
    logger = setup_logging("T034_Validation", project_root / "logs")
    logger.info(f"Starting quickstart validation. Project root: {project_root}")
    logger.info(f"Quickstart path: {quickstart_path}")

    if not quickstart_path.exists():
        logger.error(f"quickstart.md not found at {quickstart_path}")
        # Create a failure report
        report = {
            'status': 'failed',
            'reason': f"quickstart.md not found at {quickstart_path}",
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        raise SystemExit(1)

    instructions = parse_quickstart_instructions(quickstart_path)
    if not instructions:
        logger.warning("No instructions found in quickstart.md. Creating empty report.")
        report = {
            'status': 'warning',
            'reason': "No executable instructions found in quickstart.md",
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
        }
    else:
        report = validate_quickstart_instructions(instructions, project_root)
        report['status'] = 'success' if report['failed'] == 0 else 'partial_failure'
        report['timestamp'] = time.strftime("%Y-%m-%d %H:%M:%S")

    # Save report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Validation report saved to {output_path}")
    logger.info(f"Summary: {report['passed']} passed, {report['failed']} failed")

    if report['failed'] > 0:
        logger.error("Validation failed. Check report for details.")
        raise SystemExit(1)
    else:
        logger.info("Validation successful.")

def main():
    parser = argparse.ArgumentParser(description="Validate quickstart.md against execution")
    parser.add_argument("--project-root", type=str, default=".", help="Project root directory")
    parser.add_argument("--quickstart", type=str, default="specs/001-predict-sn1-rate-constants/quickstart.md", help="Path to quickstart.md")
    parser.add_argument("--output", type=str, default="artifacts/quickstart_validation_report.json", help="Output report path")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    quickstart_path = project_root / args.quickstart
    output_path = project_root / args.output

    run_verification(quickstart_path, project_root, output_path)

if __name__ == "__main__":
    main()