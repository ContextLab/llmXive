"""
Quickstart Validation Script (T049)

This script validates the project's quickstart procedure by:
1. Verifying the existence of `quickstart.md`.
2. Parsing the `quickstart.md` to extract shell commands (lines starting with `# Run:` or code blocks).
3. Executing each command in a subprocess.
4. Validating that expected output artifacts (defined in `tasks.md` or `quickstart.md`) are created.
5. Writing a validation report to `output/quickstart_validation_report.json`.

If any command fails or an expected artifact is missing, the script exits with code 1.
"""
import os
import sys
import json
import hashlib
import subprocess
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import logging setup from existing utils
# We use the existing logging_init to ensure consistency with the rest of the pipeline
try:
    from utils.logging_init import setup_global_logger
except ImportError:
    # Fallback if logging_init isn't fully wired in test environments, 
    # though T008b/T008a should have ensured it exists.
    import logging.config
    def setup_global_logger():
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_project_root() -> Path:
    """Returns the project root directory."""
    return Path(__file__).resolve().parent.parent

def compute_file_hash(file_path: Path) -> Optional[str]:
    """Computes the SHA-256 hash of a file."""
    if not file_path.exists():
        return None
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def run_script(script_path: Path, args: List[str] = None) -> subprocess.CompletedProcess:
    """Runs a Python script with optional arguments."""
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
    logging.info(f"Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        cwd=get_project_root(),
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        logging.error(f"Script failed with returncode {result.returncode}")
        logging.error(f"STDOUT: {result.stdout}")
        logging.error(f"STDERR: {result.stderr}")
    return result

def validate_artifact(path: Path, expected_hash: Optional[str] = None) -> bool:
    """Validates that an artifact exists and optionally matches a hash."""
    if not path.exists():
        logging.error(f"Artifact missing: {path}")
        return False
    
    if expected_hash:
        actual_hash = compute_file_hash(path)
        if actual_hash != expected_hash:
            logging.warning(f"Hash mismatch for {path}: expected {expected_hash}, got {actual_hash}")
            # We log a warning but return True for existence if the task didn't strictly require hash match
            # However, for a strict validation, we might fail. Let's be strict.
            return False
    
    logging.info(f"Artifact validated: {path}")
    return True

def parse_quickstart_commands(quickstart_path: Path) -> List[Dict[str, Any]]:
    """
    Parses quickstart.md to find commands to run.
    Looks for:
    - Lines starting with `# Run:`
    - Code blocks in markdown (```bash ... ```)
    - Explicit references to scripts in tasks.md if quickstart is vague
    """
    commands = []
    if not quickstart_path.exists():
        logging.error("quickstart.md not found")
        return commands

    content = quickstart_path.read_text()
    
    # Strategy 1: Look for explicit `# Run:` comments or markdown code blocks
    # Pattern for code blocks
    code_blocks = re.findall(r'```(?:bash|sh)?\n(.*?)```', content, re.DOTALL)
    
    # Pattern for `# Run:` lines
    run_lines = re.findall(r'# Run:\s*(.+)', content)

    # We will prioritize code blocks as they are more likely to be actual commands
    # If no code blocks, we fallback to run_lines or known scripts from tasks.md
    
    if code_blocks:
        for block in code_blocks:
            for line in block.strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    commands.append({"command": line, "source": "code_block"})
    elif run_lines:
        for line in run_lines:
            commands.append({"command": line, "source": "run_comment"})
    
    # Fallback: If quickstart is empty or vague, check tasks.md for the "Phase N" execution order
    if not commands:
        logging.warning("No explicit commands found in quickstart.md. Checking tasks.md for execution order.")
        tasks_path = get_project_root() / "tasks.md"
        if tasks_path.exists():
            tasks_content = tasks_path.read_text()
            # Extract script names from tasks.md that are marked as executable
            # Looking for patterns like `code/02_preprocess_gaze.py`
            scripts = re.findall(r'code/(\d+_[a-z_]+\.py)', tasks_content)
            for script_name in scripts:
                # Skip setup scripts that might not produce artifacts if run in isolation without data
                if script_name.startswith('01_') or script_name.startswith('02_') or script_name.startswith('03_') or script_name.startswith('04_') or script_name.startswith('05_'):
                    commands.append({"command": f"python code/{script_name}", "source": "tasks_fallback"})
    
    return commands

def validate_artifacts_exist(artifacts: List[str]) -> Dict[str, bool]:
    """Validates that a list of artifact paths exist."""
    results = {}
    for artifact in artifacts:
        path = get_project_root() / artifact
        results[artifact] = path.exists()
        if not results[artifact]:
            logging.error(f"Missing expected artifact: {artifact}")
    return results

def main():
    setup_global_logger()
    root = get_project_root()
    quickstart_path = root / "quickstart.md"
    output_dir = root / "output"
    output_dir.mkdir(exist_ok=True)
    
    report = {
        "status": "passed",
        "timestamp": "",
        "commands_executed": [],
        "artifacts_validated": [],
        "errors": []
    }

    # 1. Verify quickstart.md exists
    if not quickstart_path.exists():
        report["status"] = "failed"
        report["errors"].append("quickstart.md not found")
        logging.error("Validation Failed: quickstart.md not found")
        with open(output_dir / "quickstart_validation_report.json", "w") as f:
            json.dump(report, f, indent=2)
        sys.exit(1)

    # 2. Parse commands
    commands = parse_quickstart_commands(quickstart_path)
    if not commands:
        # If no commands found, we assume the task is to verify the project structure and key artifacts
        # based on the completed tasks list
        logging.info("No explicit commands found. Validating key artifacts from completed tasks.")
        # Define key artifacts based on tasks.md
        key_artifacts = [
            "data/raw/eye_tracking_raw.parquet",
            "data/derived/preprocessed_gaze.csv",
            "data/derived/regression_results.csv",
            "output/data_quality_report.csv",
            "output/stability_check.json"
        ]
        artifact_results = validate_artifacts_exist(key_artifacts)
        all_present = all(artifact_results.values())
        if all_present:
            logging.info("All key artifacts present.")
        else:
            report["status"] = "failed"
            missing = [k for k, v in artifact_results.items() if not v]
            report["errors"].append(f"Missing artifacts: {missing}")
        
        report["artifacts_validated"] = artifact_results
        with open(output_dir / "quickstart_validation_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        if not all_present:
            sys.exit(1)
        else:
            sys.exit(0)

    # 3. Execute commands
    for cmd_info in commands:
        cmd_str = cmd_info["command"]
        logging.info(f"Executing: {cmd_str}")
        
        try:
            # Handle python scripts specifically
            if cmd_str.startswith("python "):
                script_name = cmd_str.split(" ", 1)[1].split()[0]
                script_path = root / script_name
                args = cmd_str.split(" ", 2)[2].split() if " " in cmd_str.split(" ", 1)[1] else []
                result = run_script(script_path, args)
                if result.returncode != 0:
                    report["status"] = "failed"
                    report["errors"].append(f"Command failed: {cmd_str}\nError: {result.stderr}")
                    report["commands_executed"].append({"command": cmd_str, "status": "failed"})
                    break
                else:
                    report["commands_executed"].append({"command": cmd_str, "status": "success"})
            else:
                # Generic shell command
                result = subprocess.run(
                    cmd_str,
                    shell=True,
                    cwd=root,
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    report["status"] = "failed"
                    report["errors"].append(f"Command failed: {cmd_str}\nError: {result.stderr}")
                    report["commands_executed"].append({"command": cmd_str, "status": "failed"})
                    break
                else:
                    report["commands_executed"].append({"command": cmd_str, "status": "success"})
        except Exception as e:
            report["status"] = "failed"
            report["errors"].append(f"Exception running {cmd_str}: {str(e)}")
            report["commands_executed"].append({"command": cmd_str, "status": "failed"})
            break

    # 4. Validate final artifacts if commands were successful
    if report["status"] == "passed":
        # Define expected outputs from the pipeline
        expected_outputs = [
            "data/derived/regression_results.csv",
            "output/causal_framing_statement.txt",
            "output/quickstart_validation_report.json" # This one
        ]
        
        artifact_results = {}
        for artifact in expected_outputs:
            path = root / artifact
            exists = path.exists()
            artifact_results[artifact] = exists
            if not exists:
                report["status"] = "failed"
                report["errors"].append(f"Expected artifact missing after quickstart: {artifact}")
        
        report["artifacts_validated"] = artifact_results

    # 5. Write report
    report_path = output_dir / "quickstart_validation_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    logging.info(f"Validation report written to {report_path}")
    
    if report["status"] == "passed":
        logging.info("Quickstart validation PASSED.")
        sys.exit(0)
    else:
        logging.error("Quickstart validation FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()