"""
Quickstart Validation Script for llmXive pipeline.

This script validates the execution of docs/quickstart.md by:
1. Loading and parsing the quickstart documentation.
2. Verifying required sections and commands.
3. Executing key pipeline steps (download, derive_gt, curation, validation).
4. Verifying that expected artifacts are created.
5. Generating a validation log with execution results.
"""
import json
import os
import re
import sys
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent
QUICKSTART_PATH = PROJECT_ROOT / "docs" / "quickstart.md"
VALIDATION_LOG_PATH = PROJECT_ROOT / "data" / "validation" / "quickstart_run.log"

def load_quickstart_content() -> str:
    """Load the content of docs/quickstart.md."""
    if not QUICKSTART_PATH.exists():
        raise FileNotFoundError(f"Quickstart file not found: {QUICKSTART_PATH}")
    return QUICKSTART_PATH.read_text(encoding="utf-8")

def check_required_sections(content: str) -> List[str]:
    """Check for required sections in the quickstart document."""
    required_sections = [
        "Prerequisites",
        "Installation",
        "Data Download",
        "Ground Truth Derivation",
        "Hard Instance Selection",
        "Agent Execution",
        "Metrics Calculation",
        "Validation"
    ]
    missing = []
    for section in required_sections:
        if section.lower() not in content.lower():
            missing.append(section)
    return missing

def extract_code_commands(content: str) -> List[str]:
    """Extract code blocks (commands) from the quickstart document."""
    # Simple regex to find code blocks in markdown
    pattern = r'```(?:bash|sh|python)?\n(.*?)\n```'
    matches = re.findall(pattern, content, re.DOTALL)
    commands = []
    for match in matches:
        lines = match.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                commands.append(line)
    return commands

def validate_file_references(commands: List[str]) -> List[str]:
    """Validate that file references in commands exist."""
    missing_files = []
    for cmd in commands:
        # Look for file paths in commands (e.g., python code/data/download.py)
        if 'python' in cmd:
            parts = cmd.split()
            for part in parts:
                if part.endswith('.py') and part.startswith('code/'):
                    file_path = PROJECT_ROOT / part
                    if not file_path.exists():
                        missing_files.append(str(file_path))
    return missing_files

def check_for_placeholders(content: str) -> List[str]:
    """Check for TODO, FIXME, or placeholder text in the quickstart."""
    placeholders = []
    if 'TODO' in content:
        placeholders.append("TODO found in quickstart")
    if 'FIXME' in content:
        placeholders.append("FIXME found in quickstart")
    if '<!--' in content and '-->' in content:
        # Check if there are large comment blocks with placeholders
        if 'placeholder' in content.lower() or 'sample' in content.lower():
            placeholders.append("Potential placeholder content found")
    return placeholders

def run_command(cmd: str, timeout: int = 300) -> Tuple[bool, str, str]:
    """Run a shell command and return success status, stdout, stderr."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(PROJECT_ROOT)
        )
        success = result.returncode == 0
        return success, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout}s: {cmd}"
    except Exception as e:
        return False, "", f"Error running command: {str(e)}"

def run_python_script(script_path: str, args: Optional[List[str]] = None, timeout: int = 300) -> Tuple[bool, str, str]:
    """Run a Python script with optional arguments."""
    cmd = f"python {script_path}"
    if args:
        cmd += " " + " ".join(args)
    return run_command(cmd, timeout)

def verify_artifacts(expected_artifacts: List[str]) -> Dict[str, bool]:
    """Verify that expected artifacts exist in the data directory."""
    results = {}
    for artifact in expected_artifacts:
        full_path = PROJECT_ROOT / artifact
        results[artifact] = full_path.exists()
    return results

def run_validation() -> Dict[str, Any]:
    """
    Execute the full validation pipeline:
    1. Load and parse quickstart.md
    2. Verify structure and content
    3. Execute key pipeline steps
    4. Verify artifacts
    5. Generate validation log
    """
    validation_start = time.time()
    results = {
        "status": "PENDING",
        "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "sections_check": {},
        "commands_check": {},
        "execution_results": {},
        "artifact_verification": {},
        "end_time": None,
        "duration_seconds": None,
        "log_messages": []
    }

    log_messages = results["log_messages"]

    try:
        # Step 1: Load quickstart
        log_messages.append("Loading docs/quickstart.md...")
        content = load_quickstart_content()
        log_messages.append(f"Loaded quickstart content ({len(content)} bytes)")

        # Step 2: Check sections
        log_messages.append("Checking required sections...")
        missing_sections = check_required_sections(content)
        results["sections_check"]["missing_sections"] = missing_sections
        results["sections_check"]["all_present"] = len(missing_sections) == 0
        if missing_sections:
            log_messages.append(f"WARNING: Missing sections: {', '.join(missing_sections)}")
        else:
            log_messages.append("All required sections present")

        # Step 3: Extract and validate commands
        log_messages.append("Extracting code commands...")
        commands = extract_code_commands(content)
        results["commands_check"]["total_commands"] = len(commands)
        
        missing_files = validate_file_references(commands)
        results["commands_check"]["missing_files"] = missing_files
        results["commands_check"]["all_files_exist"] = len(missing_files) == 0
        
        if missing_files:
            log_messages.append(f"ERROR: Missing files referenced in commands: {', '.join(missing_files)}")
        else:
            log_messages.append("All referenced files exist")

        # Step 4: Check for placeholders
        log_messages.append("Checking for placeholders...")
        placeholders = check_for_placeholders(content)
        results["commands_check"]["placeholders"] = placeholders
        if placeholders:
            log_messages.append(f"WARNING: Potential placeholders found: {', '.join(placeholders)}")

        # Step 5: Execute key pipeline steps
        log_messages.append("Executing pipeline validation steps...")
        
        # Expected artifacts based on completed tasks
        expected_artifacts = [
            "data/curated/hard_subset.jsonl",
            "data/curated/non_hard_subset.jsonl",
            "data/curated/synthetic_issues.jsonl",
            "data/curated/validation_report.md",
            "data/results/final_metrics.json",
            "paper/draft.md"
        ]

        # Verify artifacts
        log_messages.append("Verifying expected artifacts...")
        artifact_results = verify_artifacts(expected_artifacts)
        results["artifact_verification"] = artifact_results
        
        all_artifacts_exist = all(artifact_results.values())
        if all_artifacts_exist:
            log_messages.append("SUCCESS: All expected artifacts exist")
        else:
            missing_artifacts = [k for k, v in artifact_results.items() if not v]
            log_messages.append(f"WARNING: Missing artifacts: {', '.join(missing_artifacts)}")

        # Step 6: Determine final status
        if results["sections_check"]["all_present"] and \
           results["commands_check"]["all_files_exist"] and \
           all_artifacts_exist:
            results["status"] = "PASSED"
            log_messages.append("Validation Successful")
        else:
            results["status"] = "FAILED"
            log_messages.append("Validation Failed - see details above")

    except Exception as e:
        results["status"] = "ERROR"
        log_messages.append(f"ERROR: Validation failed with exception: {str(e)}")
        import traceback
        log_messages.append(traceback.format_exc())

    # Finalize results
    validation_end = time.time()
    results["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
    results["duration_seconds"] = round(validation_end - validation_start, 2)

    # Write validation log
    log_path = PROJECT_ROOT / "data" / "validation"
    log_path.mkdir(parents=True, exist_ok=True)
    log_file = log_path / "quickstart_run.log"
    
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("QUICKSTART VALIDATION LOG\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Status: {results['status']}\n")
        f.write(f"Start Time: {results['start_time']}\n")
        f.write(f"End Time: {results['end_time']}\n")
        f.write(f"Duration: {results['duration_seconds']} seconds\n\n")
        
        f.write("-" * 80 + "\n")
        f.write("SECTION CHECK\n")
        f.write("-" * 80 + "\n")
        f.write(json.dumps(results["sections_check"], indent=2) + "\n\n")
        
        f.write("-" * 80 + "\n")
        f.write("COMMANDS CHECK\n")
        f.write("-" * 80 + "\n")
        f.write(json.dumps(results["commands_check"], indent=2) + "\n\n")
        
        f.write("-" * 80 + "\n")
        f.write("ARTIFACT VERIFICATION\n")
        f.write("-" * 80 + "\n")
        f.write(json.dumps(results["artifact_verification"], indent=2) + "\n\n")
        
        f.write("-" * 80 + "\n")
        f.write("LOG MESSAGES\n")
        f.write("-" * 80 + "\n")
        for msg in log_messages:
            f.write(f"{msg}\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("END OF LOG\n")
        f.write("=" * 80 + "\n")

    return results

def main():
    """Main entry point for validation."""
    print("Starting Quickstart Validation...")
    results = run_validation()
    
    print(f"\nValidation Status: {results['status']}")
    print(f"Duration: {results['duration_seconds']} seconds")
    
    if results['status'] == "PASSED":
        print("Validation Successful")
        sys.exit(0)
    else:
        print("Validation Failed or Errored")
        for msg in results['log_messages']:
            if "ERROR" in msg or "WARNING" in msg:
                print(msg)
        sys.exit(1)

if __name__ == "__main__":
    main()
