"""
Constitution Checker Module.
Validates file checksums against the state file to ensure data integrity.
Implements Constitution Principle III (Checksums).
"""
import os
import sys
import json
import hashlib
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List

class ConstitutionCheckResult:
    def __init__(self, status: str, message: str, details: Dict[str, Any]):
        self.status = status  # 'PASS', 'FAIL', 'MISSING'
        self.message = message
        self.details = details

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "message": self.message,
            "details": self.details
        }

def calculate_file_checksum(file_path: str) -> str:
    """
    Calculate SHA256 checksum of a file.
    
    Args:
        file_path: Path to the file to checksum.
        
    Returns:
        Hexadecimal SHA256 hash string.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found for checksum: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load a YAML schema file.
    
    Args:
        schema_path: Path to the schema file.
        
    Returns:
        Dictionary containing the schema.
    """
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_manifest_against_schema(manifest: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate a manifest dictionary against a schema.
    
    Args:
        manifest: The data to validate.
        schema: The schema definition.
        
    Returns:
        List of validation error messages.
    """
    errors = []
    # Basic validation: check for required keys
    required_keys = schema.get('required_keys', [])
    for key in required_keys:
        if key not in manifest:
            errors.append(f"Missing required key: {key}")
    return errors

def validate_checksum_recording(file_path: str, state_file_path: str) -> bool:
    """
    Validate that a file's checksum is recorded correctly in the state file.
    
    Args:
        file_path: Path to the artifact file.
        state_file_path: Path to the state YAML file.
        
    Returns:
        True if valid, False otherwise.
    """
    if not os.path.exists(state_file_path):
        return False
        
    try:
        with open(state_file_path, 'r') as f:
            state_data = yaml.safe_load(f)
    except Exception:
        return False
        
    if 'artifact_hashes' not in state_data:
        return False
        
    relative_path = os.path.relpath(file_path, os.getcwd())
    if relative_path not in state_data['artifact_hashes']:
        return False
        
    recorded_entry = state_data['artifact_hashes'][relative_path]
    if not isinstance(recorded_entry, str) or not recorded_entry.startswith('sha256:'):
        return False
        
    recorded_hash = recorded_entry.split('sha256:')[1]
    current_hash = calculate_file_checksum(file_path)
    
    return recorded_hash == current_hash

def update_state_with_checksum(file_path: str, state_file_path: str) -> bool:
    """
    Update the state file with the checksum of a specific artifact.
    
    Args:
        file_path: Path to the artifact file.
        state_file_path: Path to the state YAML file.
        
    Returns:
        True if successful, False otherwise.
    """
    if not os.path.exists(file_path):
        print(f"Error: Artifact file not found: {file_path}")
        return False
        
    try:
        # Ensure state directory exists
        state_dir = os.path.dirname(state_file_path)
        if state_dir and not os.path.exists(state_dir):
            os.makedirs(state_dir)
        
        # Load existing state or initialize
        state_data = {}
        if os.path.exists(state_file_path):
            with open(state_file_path, 'r') as f:
                state_data = yaml.safe_load(f) or {}
        
        # Calculate checksum
        checksum = calculate_file_checksum(file_path)
        relative_path = os.path.relpath(file_path, os.getcwd())
        
        # Update artifact_hashes
        if 'artifact_hashes' not in state_data:
            state_data['artifact_hashes'] = {}
        
        state_data['artifact_hashes'][relative_path] = f"sha256:{checksum}"
        
        # Write back to state file
        with open(state_file_path, 'w') as f:
            yaml.safe_dump(state_data, f, default_flow_style=False, sort_keys=False)
        
        return True
        
    except Exception as e:
        print(f"Error updating state file: {e}")
        return False

def run_constitution_check(file_path: str, state_file_path: str) -> ConstitutionCheckResult:
    """
    Run a full constitution check for a given file against the state file.
    
    Args:
        file_path: Path to the artifact file.
        state_file_path: Path to the state YAML file.
        
    Returns:
        ConstitutionCheckResult object.
    """
    if not os.path.exists(file_path):
        return ConstitutionCheckResult(
            status="MISSING",
            message=f"Artifact file not found: {file_path}",
            details={"file_path": file_path}
        )
    
    if not os.path.exists(state_file_path):
        return ConstitutionCheckResult(
            status="MISSING",
            message=f"State file not found: {state_file_path}",
            details={"state_file_path": state_file_path}
        )
    
    try:
        with open(state_file_path, 'r') as f:
            state_data = yaml.safe_load(f)
    except Exception as e:
        return ConstitutionCheckResult(
            status="FAIL",
            message=f"Failed to load state file: {e}",
            details={}
        )
        
    relative_path = os.path.relpath(file_path, os.getcwd())
    
    if 'artifact_hashes' not in state_data:
        return ConstitutionCheckResult(
            status="FAIL",
            message="State file missing 'artifact_hashes' key",
            details={"state_file": state_file_path}
        )
        
    if relative_path not in state_data['artifact_hashes']:
        return ConstitutionCheckResult(
            status="FAIL",
            message=f"Checksum not found for artifact: {relative_path}",
            details={"relative_path": relative_path}
        )
        
    recorded_entry = state_data['artifact_hashes'][relative_path]
    if not isinstance(recorded_entry, str) or not recorded_entry.startswith('sha256:'):
        return ConstitutionCheckResult(
            status="FAIL",
            message="Invalid checksum format in state file",
            details={"entry": recorded_entry}
        )
        
    recorded_hash = recorded_entry.split('sha256:')[1]
    current_hash = calculate_file_checksum(file_path)
    
    if recorded_hash != current_hash:
        return ConstitutionCheckResult(
            status="FAIL",
            message="Checksum mismatch: file has been modified since recording",
            details={
                "relative_path": relative_path,
                "recorded_hash": recorded_hash,
                "current_hash": current_hash
            }
        )
        
    return ConstitutionCheckResult(
        status="PASS",
        message="Checksum validation successful",
        details={"relative_path": relative_path}
    )

def main():
    """
    CLI entry point for the Constitution Checker.
    Usage: python code/constitution_checker.py --action {check,register} --file <path> --state <path>
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Constitution Checker for Data Integrity")
    parser.add_argument('--action', choices=['check', 'register'], required=True,
                      help='Action to perform: check existing checksum or register new one')
    parser.add_argument('--file', required=True, help='Path to the artifact file')
    parser.add_argument('--state', required=True, help='Path to the state YAML file')
    
    args = parser.parse_args()
    
    if args.action == 'register':
        success = update_state_with_checksum(args.file, args.state)
        if success:
            print(f"Successfully registered checksum for {args.file}")
            sys.exit(0)
        else:
            print(f"Failed to register checksum for {args.file}")
            sys.exit(1)
    elif args.action == 'check':
        result = run_constitution_check(args.file, args.state)
        print(json.dumps(result.to_dict(), indent=2))
        sys.exit(0 if result.status == "PASS" else 1)

if __name__ == "__main__":
    main()