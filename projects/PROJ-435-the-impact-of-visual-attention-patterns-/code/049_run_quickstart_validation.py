import os
import sys
import json
import hashlib
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import project utilities to ensure consistency with the rest of the pipeline
# We assume utils.logging_init is available as per T008b
try:
    from utils.logging_init import setup_global_logger, get_project_root
except ImportError:
    # Fallback if logging_init isn't fully set up in this specific run context,
    # though T008b should have completed.
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    def get_project_root():
        return Path(__file__).parent.parent

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found for hashing: {file_path}")

def run_script(script_path: Path, args: Optional[List[str]] = None) -> Tuple[bool, str, str]:
    """
    Execute a script and capture stdout/stderr.
    Returns (success, stdout, stderr).
    """
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300, # 5 minute timeout per script
            cwd=str(script_path.parent)
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Script timed out: {script_path}"
    except Exception as e:
        return False, "", str(e)

def validate_artifact(artifact_path: Path, expected_hash: Optional[str] = None) -> Dict[str, Any]:
    """
    Validate an artifact exists and optionally matches a hash.
    """
    result = {
        "path": str(artifact_path),
        "exists": artifact_path.exists(),
        "valid": False,
        "hash": None,
        "message": ""
    }
    
    if not result["exists"]:
        result["message"] = "Artifact does not exist"
        return result
    
    try:
        current_hash = compute_file_hash(artifact_path)
        result["hash"] = current_hash
        
        if expected_hash:
            if current_hash == expected_hash:
                result["valid"] = True
                result["message"] = "Hash matches"
            else:
                result["valid"] = False
                result["message"] = f"Hash mismatch. Expected: {expected_hash}, Got: {current_hash}"
        else:
            result["valid"] = True
            result["message"] = "Artifact exists (no hash provided for verification)"
    except Exception as e:
        result["message"] = f"Error validating artifact: {str(e)}"
    
    return result

def parse_quickstart_commands(quickstart_path: Path) -> List[Dict[str, Any]]:
    """
    Parse quickstart.md to extract commands to run and artifacts to check.
    This is a simplified parser assuming standard markdown code blocks for commands.
    """
    commands = []
    if not quickstart_path.exists():
        return commands
    
    content = quickstart_path.read_text()
    lines = content.split('\n')
    
    current_command = None
    current_artifact_check = None
    
    in_code_block = False
    
    for line in lines:
        stripped = line.strip()
        
        if stripped.startswith("```bash") or stripped.startswith("```sh"):
            in_code_block = True
            current_command = []
            continue
        elif stripped.startswith("```"):
            in_code_block = False
            if current_command:
                commands.append({
                    "type": "run",
                    "command": "\n".join(current_command),
                    "description": "Quickstart command"
                })
                current_command = None
            continue
        
        if in_code_block and current_command is not None:
            current_command.append(stripped)
        
        # Look for artifact checks in comments or specific markdown patterns
        if "data/derived/" in stripped or "output/" in stripped or "state/" in stripped:
            if "verify" in stripped.lower() or "check" in stripped.lower() or "exists" in stripped.lower():
                # Extract path
                parts = stripped.split()
                for part in parts:
                    if part.startswith(("data/", "output/", "state/")):
                        commands.append({
                            "type": "check",
                            "path": part.strip("()\"'`"),
                            "description": "Artifact check"
                        })
                        break
    
    # If no explicit commands found, try to infer from common pipeline steps
    if not commands:
        # Fallback: check for standard pipeline scripts
        standard_scripts = [
            "01_extract_empirical_outcome.py",
            "02_preprocess_gaze.py",
            "03_data_merge.py",
            "05_regression_analysis.py",
            "07_generate_causal_framing.py"
        ]
        for script_name in standard_scripts:
            script_path = get_project_root() / "code" / script_name
            if script_path.exists():
                commands.append({
                    "type": "run",
                    "command": f"python code/{script_name}",
                    "description": f"Run {script_name}"
                })
    
    return commands

def validate_artifacts_exist(artifacts: List[str]) -> List[Dict[str, Any]]:
    """Check if a list of artifact paths exist."""
    results = []
    for artifact_path in artifacts:
        full_path = get_project_root() / artifact_path
        res = validate_artifact(full_path)
        results.append(res)
    return results

def main():
    project_root = get_project_root()
    quickstart_path = project_root / "quickstart.md"
    output_path = project_root / "output" / "quickstart_validation_report.json"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting Quickstart Validation for project: {project_root}")
    
    validation_report = {
        "project_root": str(project_root),
        "quickstart_path": str(quickstart_path),
        "timestamp": None, # Will be set by caller or runtime
        "status": "unknown",
        "commands_run": [],
        "artifacts_checked": [],
        "errors": []
    }
    
    if not quickstart_path.exists():
        error_msg = "quickstart.md not found. Cannot validate."
        logger.error(error_msg)
        validation_report["status"] = "failed"
        validation_report["errors"].append(error_msg)
    else:
        try:
            # 1. Parse commands
            commands = parse_quickstart_commands(quickstart_path)
            logger.info(f"Parsed {len(commands)} validation steps from quickstart.md")
            
            if not commands:
                logger.warning("No commands found in quickstart.md. Running standard pipeline checks.")
                # Fallback to checking key artifacts if no commands found
                key_artifacts = [
                    "data/derived/empirical_outcomes.csv",
                    "data/derived/preprocessed_gaze.csv",
                    "data/derived/merged_dataset_full.csv",
                    "data/derived/regression_results.csv",
                    "output/causal_framing_statement.txt",
                    "state/data_hashes.json"
                ]
                validation_report["artifacts_checked"] = validate_artifacts_exist(key_artifacts)
                all_exist = all(a["valid"] for a in validation_report["artifacts_checked"])
                validation_report["status"] = "passed" if all_exist else "failed"
                if not all_exist:
                    validation_report["errors"].append("Key artifacts missing.")
            else:
                # 2. Execute commands and check artifacts
                for step in commands:
                    step_result = {"type": step["type"], "details": step.get("description", ""), "success": False}
                    
                    if step["type"] == "run":
                        cmd_str = step["command"]
                        logger.info(f"Executing: {cmd_str}")
                        # Parse the command to get script path and args
                        parts = cmd_str.split()
                        if parts[0] == "python":
                            script_name = parts[1]
                            args = parts[2:]
                            script_path = project_root / "code" / script_name
                            
                            if not script_path.exists():
                                step_result["success"] = False
                                step_result["error"] = f"Script not found: {script_path}"
                                validation_report["errors"].append(step_result["error"])
                            else:
                                success, stdout, stderr = run_script(script_path, args)
                                step_result["success"] = success
                                step_result["stdout"] = stdout[:500] # Truncate for log
                                step_result["stderr"] = stderr[:500]
                                if not success:
                                    error_msg = f"Script failed: {script_name}. Error: {stderr}"
                                    validation_report["errors"].append(error_msg)
                                    logger.error(error_msg)
                    elif step["type"] == "check":
                        artifact_path = step["path"]
                        full_path = project_root / artifact_path
                        res = validate_artifact(full_path)
                        step_result["success"] = res["valid"]
                        step_result["artifact_result"] = res
                        if not res["valid"]:
                            validation_report["errors"].append(f"Artifact missing or invalid: {artifact_path}")
                    
                    validation_report["commands_run"].append(step_result)
                
                # Determine overall status
                all_success = all(r["success"] for r in validation_report["commands_run"])
                validation_report["status"] = "passed" if all_success else "failed"
        
        except Exception as e:
            error_msg = f"Validation process failed unexpectedly: {str(e)}"
            logger.error(error_msg, exc_info=True)
            validation_report["status"] = "failed"
            validation_report["errors"].append(error_msg)
    
    # Write report
    with open(output_path, 'w') as f:
        json.dump(validation_report, f, indent=2)
    
    logger.info(f"Validation report written to: {output_path}")
    print(f"Quickstart Validation Complete. Status: {validation_report['status']}")
    print(f"Report saved to: {output_path}")
    
    # Return exit code based on status
    sys.exit(0 if validation_report['status'] == 'passed' else 1)

if __name__ == "__main__":
    main()
