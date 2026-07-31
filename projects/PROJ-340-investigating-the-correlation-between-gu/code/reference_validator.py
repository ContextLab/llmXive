"""
Reference Validator Module.

Implements the Reference-Validator Agent logic and artifact checksum recording
to ensure reproducibility and data integrity (Constitution Principles I & III).
"""
import os
import sys
import json
import hashlib
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List

# Constants
STATE_FILE_PATH = "state/projects/PROJ-340-investigating-the-correlation-between-gu.yaml"
CHECKSUM_PREFIX = "sha256:"

class VerificationStatus:
    """Enum-like class for verification statuses."""
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"

class CitationSchema:
    """Schema for citation validation."""
    REQUIRED_FIELDS = ["source", "url", "accessed_date", "relevance"]

class VerificationResult:
    """Container for verification results."""
    def __init__(self, status: str, message: str, details: Optional[Dict] = None):
        self.status = status
        self.message = message
        self.details = details or {}

class ReferenceValidator:
    """
    Validates references and manages artifact checksums for reproducibility.
    """
    def __init__(self, state_file: str = STATE_FILE_PATH):
        self.state_file = Path(state_file)
        self.artifact_hashes: Dict[str, str] = {}

    def load_state(self) -> Dict[str, Any]:
        """Load the current state file or return an empty structure."""
        if not self.state_file.exists():
            # Ensure directory exists
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            return {"artifact_hashes": {}}
        
        with open(self.state_file, 'r') as f:
            try:
                data = yaml.safe_load(f)
                if data is None:
                    return {"artifact_hashes": {}}
                return data
            except yaml.YAMLError:
                return {"artifact_hashes": {}}

    def save_state(self, data: Dict[str, Any]) -> bool:
        """Save the state to the YAML file."""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w') as f:
                yaml.dump(data, f, default_flow_style=False)
            return True
        except Exception as e:
            print(f"Error saving state: {e}", file=sys.stderr)
            return False

    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return f"{CHECKSUM_PREFIX}{sha256_hash.hexdigest()}"
        except FileNotFoundError:
            raise FileNotFoundError(f"Artifact file not found: {file_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to calculate hash for {file_path}: {e}")

    def record_artifact_checksum(self, file_path: str, state_file: Optional[str] = None) -> bool:
        """
        Record the checksum of an artifact file into the project state.
        
        Args:
            file_path: Path to the artifact file to checksum.
            state_file: Optional path to the state file (defaults to project default).
        
        Returns:
            bool: True if successful, False otherwise.
        
        Raises:
            FileNotFoundError: If the artifact file does not exist.
            RuntimeError: If the hash calculation or state update fails.
        """
        if state_file is None:
            state_file = self.state_file
        
        state_path = Path(state_file)
        if not state_path.exists():
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_data = {"artifact_hashes": {}}
        else:
            with open(state_path, 'r') as f:
                try:
                    state_data = yaml.safe_load(f) or {"artifact_hashes": {}}
                except yaml.YAMLError:
                    state_data = {"artifact_hashes": {}}

        # Ensure artifact_hashes key exists
        if "artifact_hashes" not in state_data:
            state_data["artifact_hashes"] = {}

        # Calculate hash
        try:
            file_hash = self.calculate_file_hash(file_path)
        except Exception as e:
            print(f"Failed to calculate checksum for {file_path}: {e}", file=sys.stderr)
            return False

        # Update state
        state_data["artifact_hashes"][file_path] = file_hash

        # Save state
        try:
            with open(state_path, 'w') as f:
                yaml.dump(state_data, f, default_flow_style=False)
            return True
        except Exception as e:
            print(f"Failed to write state file: {e}", file=sys.stderr)
            return False

    def validate_artifact_integrity(self, file_path: str, state_file: Optional[str] = None) -> bool:
        """
        Validate that an artifact's current checksum matches the recorded one.
        
        Args:
            file_path: Path to the artifact file.
            state_file: Optional path to the state file.
        
        Returns:
            bool: True if checksum matches or no record exists, False if mismatch.
        """
        if state_file is None:
            state_file = self.state_file
        
        state_path = Path(state_file)
        if not state_path.exists():
            return True # No record to validate against

        with open(state_path, 'r') as f:
            try:
                state_data = yaml.safe_load(f) or {}
            except yaml.YAMLError:
                return True

        recorded_hash = state_data.get("artifact_hashes", {}).get(file_path)
        if not recorded_hash:
            return True # No record to validate against

        try:
            current_hash = self.calculate_file_hash(file_path)
            return current_hash == recorded_hash
        except FileNotFoundError:
            return False
        except Exception:
            return False

def create_sample_schema() -> Dict[str, Any]:
    """Create a sample schema for reference validation."""
    return {
        "type": "object",
        "properties": {
            "source": {"type": "string"},
            "url": {"type": "string"},
            "accessed_date": {"type": "string"},
            "relevance": {"type": "string"}
        },
        "required": CitationSchema.REQUIRED_FIELDS
    }

def main():
    """Main entry point for CLI usage."""
    import argparse
    parser = argparse.ArgumentParser(description="Reference Validator CLI")
    parser.add_argument("--action", choices=["record", "validate"], required=True,
                        help="Action to perform: record checksum or validate integrity")
    parser.add_argument("--file", required=True, help="Path to the artifact file")
    parser.add_argument("--state", default=STATE_FILE_PATH, help="Path to the state file")
    
    args = parser.parse_args()
    
    validator = ReferenceValidator(state_file=args.state)
    
    if args.action == "record":
        success = validator.record_artifact_checksum(args.file, args.state)
        if success:
            print(f"Successfully recorded checksum for {args.file}")
            sys.exit(0)
        else:
            print(f"Failed to record checksum for {args.file}")
            sys.exit(1)
    elif args.action == "validate":
        is_valid = validator.validate_artifact_integrity(args.file, args.state)
        if is_valid:
            print(f"Integrity check passed for {args.file}")
            sys.exit(0)
        else:
            print(f"Integrity check FAILED for {args.file}")
            sys.exit(1)

if __name__ == "__main__":
    main()