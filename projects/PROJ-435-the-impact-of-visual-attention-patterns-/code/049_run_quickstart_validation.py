import os
import sys
import json
import hashlib
import subprocess
import logging
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional

def get_project_root() -> Path:
    """Return the project root directory."""
    current = Path(__file__).resolve()
    # Traverse up to find the root (usually 3 levels up from code/049...)
    # Assuming structure: code/049_run_quickstart_validation.py
    # We look for a file like 'tasks.md' or 'config.yaml' at root
    for parent in current.parents:
        if (parent / 'tasks.md').exists() and (parent / 'code').is_dir():
            return parent
    raise FileNotFoundError("Could not determine project root")

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return ""

def run_script(script_path: Path, args: List[str] = None) -> Dict[str, Any]:
    """Run a Python script and capture output."""
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
    
    logging.info(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300, # 5 minutes timeout
            cwd=script_path.parent
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Timeout expired",
            "returncode": -1
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }

def validate_artifact(expected_path: Path, description: str) -> Dict[str, Any]:
    """Check if an artifact exists and is non-empty."""
    if not expected_path.exists():
        return {
            "valid": False,
            "reason": f"File not found: {expected_path}",
            "path": str(expected_path)
        }
    
    size = expected_path.stat().st_size
    if size == 0:
        return {
            "valid": False,
            "reason": f"File is empty: {expected_path}",
            "path": str(expected_path)
        }
    
    return {
        "valid": True,
        "size_bytes": size,
        "hash": compute_file_hash(expected_path),
        "path": str(expected_path)
    }

def parse_quickstart_commands(quickstart_path: Path) -> List[Dict[str, Any]]:
    """Parse quickstart.md to extract expected scripts and outputs."""
    if not quickstart_path.exists():
        # If quickstart doesn't exist, use a default set based on task descriptions
        logging.warning("quickstart.md not found. Using default validation set.")
        return [
            {"script": "code/01_ingest_and_preprocess.py", "outputs": ["data/raw/eye_tracking_raw.parquet", "data/derived/preprocessed_gaze.csv"]},
            {"script": "code/03_data_merge.py", "outputs": ["data/derived/merged_dataset_full.csv"]},
            {"script": "code/05_regression_analysis.py", "outputs": ["data/derived/regression_results.csv"]},
            {"script": "code/07_generate_causal_framing.py", "outputs": ["output/causal_framing_statement.txt"]}
        ]

    commands = []
    with open(quickstart_path, 'r') as f:
        content = f.read()
    
    # Simple heuristic: look for python code blocks or explicit file paths
    # This is a simplified parser; a robust one would parse Markdown properly
    lines = content.split('\n')
    current_script = None
    
    for line in lines:
        line = line.strip()
        if line.startswith("python code/") and ".py" in line:
            # Extract script path
            parts = line.split()
            for part in parts:
                if part.startswith("code/") and part.endswith(".py"):
                    current_script = part
                    commands.append({"script": current_script, "outputs": []})
                    break
        elif current_script and (line.startswith("data/") or line.startswith("output/") or line.startswith("state/")):
            # Assume this line mentions an output file
            # Clean up markdown formatting if any
            clean_line = line.replace("`", "").replace("*", "").strip()
            if clean_line.endswith(".csv") or clean_line.endswith(".json") or clean_line.endswith(".txt") or clean_line.endswith(".parquet"):
                commands[-1]["outputs"].append(clean_line)

    return commands if commands else []

def validate_artifacts_exist(project_root: Path, artifacts: List[str]) -> List[Dict[str, Any]]:
    """Validate that a list of artifacts exist."""
    results = []
    for artifact in artifacts:
        full_path = project_root / artifact
        results.append(validate_artifact(full_path, artifact))
    return results

def main():
    """Main entry point for quickstart validation."""
    setup_logger = logging.getLogger("quickstart_validation")
    if not setup_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        setup_logger.addHandler(handler)
        setup_logger.setLevel(logging.INFO)
    
    project_root = get_project_root()
    quickstart_path = project_root / "quickstart.md"
    output_path = project_root / "output" / "quickstart_validation_report.json"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    validation_results = {
        "timestamp": subprocess.check_output(["date", "-Iseconds"]).decode().strip(),
        "project_root": str(project_root),
        "quickstart_path": str(quickstart_path),
        "steps": [],
        "summary": {
            "total_steps": 0,
            "passed": 0,
            "failed": 0,
            "errors": []
        }
    }
    
    # Parse quickstart or use defaults
    steps = parse_quickstart_commands(quickstart_path)
    validation_results["summary"]["total_steps"] = len(steps)
    
    logging.info(f"Validating {len(steps)} steps from quickstart.")
    
    for i, step in enumerate(steps):
        step_result = {
            "step_index": i,
            "script": step["script"],
            "status": "pending",
            "execution": None,
            "artifacts": []
        }
        
        script_path = project_root / step["script"]
        
        # 1. Check if script exists
        if not script_path.exists():
            step_result["status"] = "failed"
            step_result["error"] = f"Script not found: {script_path}"
            validation_results["summary"]["failed"] += 1
            validation_results["summary"]["errors"].append(step_result["error"])
            validation_results["steps"].append(step_result)
            logging.error(f"Step {i}: Script not found: {script_path}")
            continue
        
        # 2. Run the script
        logging.info(f"Step {i}: Running {step['script']}...")
        exec_result = run_script(script_path)
        step_result["execution"] = exec_result
        
        if not exec_result["success"]:
            step_result["status"] = "failed"
            step_result["error"] = f"Script failed with code {exec_result['returncode']}: {exec_result['stderr']}"
            validation_results["summary"]["failed"] += 1
            validation_results["summary"]["errors"].append(step_result["error"])
            logging.error(f"Step {i} failed: {step_result['error']}")
        else:
            # 3. Validate outputs
            step_result["status"] = "passed" # Tentative
            artifacts_valid = True
            
            for output_file in step.get("outputs", []):
                artifact_res = validate_artifact(project_root / output_file, output_file)
                step_result["artifacts"].append(artifact_res)
                if not artifact_res["valid"]:
                    artifacts_valid = False
            
            if artifacts_valid:
                validation_results["summary"]["passed"] += 1
                logging.info(f"Step {i}: Passed. All artifacts valid.")
            else:
                step_result["status"] = "failed"
                validation_results["summary"]["failed"] += 1
                missing = [a["path"] for a in step_result["artifacts"] if not a["valid"]]
                step_result["error"] = f"Missing or empty artifacts: {missing}"
                validation_results["summary"]["errors"].append(step_result["error"])
                logging.error(f"Step {i} failed: {step_result['error']}")
        
        validation_results["steps"].append(step_result)
    
    # Write report
    with open(output_path, 'w') as f:
        json.dump(validation_results, f, indent=2)
    
    logging.info(f"Validation complete. Report written to {output_path}")
    print(json.dumps(validation_results["summary"], indent=2))
    
    # Exit with error if any step failed
    if validation_results["summary"]["failed"] > 0:
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
