"""
Terminology Audit Utility.

This module provides functions to load/save project state and scan files
for terminology compliance. It is used by the terminology_scanner.py
to update the project state file.
"""
import os
import re
import sys
import logging
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

STATE_FILE_PATH = "state/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate.yaml"

def load_state(project_root: Path) -> Dict[str, Any]:
    """Loads the project state YAML file."""
    state_path = project_root / STATE_FILE_PATH
    if not state_path.exists():
        logger.warning(f"State file not found at {state_path}. Creating new state.")
        return {"artifact_hashes": {}, "terminology_audit": []}

    try:
        with open(state_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {"artifact_hashes": {}, "terminology_audit": []}
    except Exception as e:
        logger.error(f"Failed to load state file: {e}")
        return {"artifact_hashes": {}, "terminology_audit": []}

def save_state(project_root: Path, state: Dict[str, Any]):
    """Saves the project state YAML file."""
    state_path = project_root / STATE_FILE_PATH
    state_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(state_path, 'w', encoding='utf-8') as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False)
        logger.info(f"State saved to {state_path}")
    except Exception as e:
        logger.error(f"Failed to save state file: {e}")
        raise

def scan_file(file_path: Path, patterns: List[re.Pattern]) -> List[Dict[str, Any]]:
    """
    Scans a file for forbidden patterns.
    Returns a list of found violations.
    """
    violations = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        logger.warning(f"Could not read file {file_path}: {e}")
        return violations

    for i, line in enumerate(lines):
        for pattern in patterns:
            matches = pattern.findall(line)
            if matches:
                for match in matches:
                    violations.append({
                        "file": str(file_path),
                        "line": i + 1,
                        "term": match,
                        "context": line.strip()[:100]
                    })
    return violations

def run_audit(project_root: Path) -> Dict[str, Any]:
    """
    Runs a full audit and updates the state file.
    """
    # Define patterns (simplified version of scanner patterns)
    patterns = [
        re.compile(r'\b(First-Principles|First Principles|Schrödinger|Hamiltonian)\b', re.IGNORECASE)
    ]

    state = load_state(project_root)
    audit_log = []

    scan_dirs = ["code", "docs"]
    exclude_dirs = ["data", "__pycache__", ".git"]
    extensions = {".py", ".md", ".txt", ".yaml", ".yml"}

    for dir_name in scan_dirs:
        target_dir = project_root / dir_name
        if not target_dir.exists():
            continue

        for root, dirs, files in os.walk(target_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file_name in files:
                if Path(file_name).suffix in extensions:
                    file_path = Path(root) / file_name
                    violations = scan_file(file_path, patterns)
                    if violations:
                        audit_log.extend(violations)

    # Update state
    state["terminology_audit"] = audit_log
    save_state(project_root, state)

    return {
        "violations_found": len(audit_log),
        "audit_log": audit_log
    }

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run terminology audit and update state.")
    parser.add_argument("--project-root", type=str, default=".", help="Project root path.")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    result = run_audit(project_root)

    print(f"Audit complete. Found {result['violations_found']} violations.")
    if result['violations_found'] > 0:
        for v in result['audit_log'][:5]: # Print first 5
            print(f"  - {v['file']}:{v['line']}: {v['term']}")
        if result['violations_found'] > 5:
            print(f"  ... and {result['violations_found'] - 5} more.")

if __name__ == "__main__":
    main()
