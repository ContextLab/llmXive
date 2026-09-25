import hashlib
import os
import yaml
import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def compute_sha256(file_path: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return ""
    except Exception as e:
        logger.error(f"Error computing hash for {file_path}: {e}")
        return ""

def get_relative_path(file_path: str, base_path: str) -> str:
    """Get relative path from base path."""
    return os.path.relpath(file_path, base_path)

def find_state_file(project_id: str) -> Optional[Path]:
    """Find the state file for a project."""
    state_dir = Path("state/projects")
    if not state_dir.exists():
        state_dir.mkdir(parents=True, exist_ok=True)
    
    # Look for files matching the project ID pattern
    for file in state_dir.glob(f"{project_id}*.yaml"):
        return file
    return None

def load_state(state_file: Path) -> Dict[str, Any]:
    """Load state file content."""
    try:
        with open(state_file, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"Error loading state file {state_file}: {e}")
        return {}

def save_state(state_file: Path, data: Dict[str, Any]) -> bool:
    """Save state file content."""
    try:
        with open(state_file, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)
        return True
    except Exception as e:
        logger.error(f"Error saving state file {state_file}: {e}")
        return False

def process_data_directory(data_dir: str, base_path: str) -> Dict[str, str]:
    """Process all files in data directory and compute hashes."""
    hashes = {}
    data_path = Path(data_dir)
    
    if not data_path.exists():
        logger.warning(f"Data directory not found: {data_dir}")
        return hashes
    
    for file_path in data_path.rglob('*'):
        if file_path.is_file():
            relative_path = get_relative_path(str(file_path), base_path)
            file_hash = compute_sha256(str(file_path))
            if file_hash:
                hashes[relative_path] = file_hash
    
    return hashes

def audit_data_integrity(state_file: Path, data_dir: str = "data") -> bool:
    """Audit data integrity by comparing current hashes with stored hashes."""
    state_data = load_state(state_file)
    if not state_data:
        logger.error("Failed to load state file for integrity audit")
        return False
    
    stored_hashes = state_data.get('artifact_hashes', {})
    current_hashes = process_data_directory(data_dir, ".")
    
    # Check for missing files
    for path, stored_hash in stored_hashes.items():
        if path not in current_hashes:
            logger.warning(f"File missing from data directory: {path}")
            continue
        
        if current_hashes[path] != stored_hash:
            logger.warning(f"Hash mismatch for {path}: stored={stored_hash}, current={current_hashes[path]}")
            return False
    
    # Check for new files not in state
    for path in current_hashes:
        if path not in stored_hashes:
            logger.info(f"New file detected: {path}")
    
    return True

def update_state_file(state_file: Path, new_hashes: Dict[str, str]) -> bool:
    """Update state file with new hashes."""
    state_data = load_state(state_file)
    state_data['artifact_hashes'] = new_hashes
    state_data['updated_at'] = datetime.utcnow().isoformat() + 'Z'
    return save_state(state_file, state_data)

def generate_reproducibility_audit(project_id: str) -> bool:
    """
    Generate a reproducibility audit file containing:
    - Git commit hash
    - requirements.txt hash
    - Python version
    
    Output: state/projects/{project_id}-reproducibility.yaml
    """
    logger.info(f"Generating reproducibility audit for project: {project_id}")
    
    # Initialize data structure
    audit_data = {
        "project_id": project_id,
        "audit_timestamp": datetime.utcnow().isoformat() + 'Z',
        "git_hash": "",
        "requirements_hash": "",
        "python_version": ""
    }
    
    # Get Git commit hash
    try:
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            capture_output=True,
            text=True,
            check=True,
            cwd=os.getcwd()
        )
        git_hash = result.stdout.strip()
        if git_hash:
            audit_data["git_hash"] = git_hash
            logger.info(f"Git commit hash: {git_hash}")
        else:
            logger.warning("Git commit hash is empty")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get git commit hash: {e}")
    except FileNotFoundError:
        logger.warning("Git command not found. Skipping git hash.")
    
    # Get requirements.txt hash
    requirements_path = Path("requirements.txt")
    if requirements_path.exists():
        req_hash = compute_sha256(str(requirements_path))
        if req_hash:
            audit_data["requirements_hash"] = req_hash
            logger.info(f"requirements.txt hash: {req_hash}")
        else:
            logger.warning("Failed to compute requirements.txt hash")
    else:
        logger.warning("requirements.txt not found")
    
    # Get Python version
    try:
        py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        audit_data["python_version"] = py_version
        logger.info(f"Python version: {py_version}")
    except Exception as e:
        logger.error(f"Failed to get Python version: {e}")
    
    # Validate that we got essential fields
    if not audit_data["git_hash"]:
        logger.warning("Git hash is missing. This may be due to not being in a git repository.")
    if not audit_data["python_version"]:
        logger.error("Python version is missing. This is critical.")
        return False
    
    # Save the audit file
    state_dir = Path("state/projects")
    state_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = state_dir / f"{project_id}-reproducibility.yaml"
    
    try:
        with open(output_file, 'w') as f:
            yaml.dump(audit_data, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Reproducibility audit saved to: {output_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to save reproducibility audit: {e}")
        return False

def main():
    """Main entry point for hygiene script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Project hygiene and reproducibility audit")
    parser.add_argument('--audit', action='store_true', help='Run data integrity audit')
    parser.add_argument('--update', action='store_true', help='Update state file with current hashes')
    parser.add_argument('--reproducibility', action='store_true', help='Generate reproducibility audit')
    parser.add_argument('--project-id', type=str, default='PROJ-163-exploring-the-role-of-network-structure-', 
                      help='Project ID for state file operations')
    
    args = parser.parse_args()
    
    # Find state file
    state_file = find_state_file(args.project_id)
    if not state_file:
        logger.error(f"No state file found for project: {args.project_id}")
        return 1
    
    logger.info(f"Using state file: {state_file}")
    
    if args.audit:
        if not audit_data_integrity(state_file):
            logger.warning("Data integrity audit failed or found issues.")
            return 1
        logger.info("Data integrity audit passed.")
    
    if args.update:
        current_hashes = process_data_directory("data", ".")
        if update_state_file(state_file, current_hashes):
            logger.info("State file updated successfully.")
        else:
            logger.error("Failed to update state file.")
            return 1
    
    if args.reproducibility:
        if not generate_reproducibility_audit(args.project_id):
            logger.error("Failed to generate reproducibility audit.")
            return 1
    
    # Default: run audit
    if not (args.audit or args.update or args.reproducibility):
        logger.info("Running default data integrity audit...")
        if not audit_data_integrity(state_file):
            logger.warning("Data integrity audit found issues.")
            return 1
        logger.info("Default audit passed.")
    
    return 0

if __name__ == '__main__':
    exit(main())