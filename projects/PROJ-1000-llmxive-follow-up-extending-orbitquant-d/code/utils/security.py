import os
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the state directory and hash file path relative to project root
# Assuming the script runs from the project root or code/ directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATE_DIR = PROJECT_ROOT / "state"
HASH_FILE_PATH = STATE_DIR / "artifact_hashes.json"

class SecurityError(Exception):
    """Custom exception for security validation failures."""
    pass

class SecurityManager:
    """
    Manages security hardening tasks:
    1. Sanitizes file paths to prevent directory traversal.
    2. Validates model checksums against a known hash manifest.
    """

    def __init__(self, state_dir: Optional[Path] = None, hash_file: Optional[Path] = None):
        self.state_dir = state_dir or STATE_DIR
        self.hash_file = hash_file or HASH_FILE_PATH
        self._hashes: Dict[str, str] = {}
        self._load_hashes()

    def _load_hashes(self) -> None:
        """Load the artifact hashes from the JSON file."""
        if not self.hash_file.exists():
            logger.warning(f"Hash manifest not found at {self.hash_file}. Creating empty manifest.")
            self.state_dir.mkdir(parents=True, exist_ok=True)
            self._hashes = {}
            self._save_hashes()
            return

        try:
            with open(self.hash_file, 'r', encoding='utf-8') as f:
                self._hashes = json.load(f)
            logger.info(f"Loaded {len(self._hashes)} artifact hashes from {self.hash_file}")
        except json.JSONDecodeError as e:
            raise SecurityError(f"Failed to parse hash manifest {self.hash_file}: {e}")
        except Exception as e:
            raise SecurityError(f"Failed to load hash manifest {self.hash_file}: {e}")

    def _save_hashes(self) -> None:
        """Save the current hash dictionary to the JSON file."""
        self.state_dir.mkdir(parents=True, exist_ok=True)
        with open(self.hash_file, 'w', encoding='utf-8') as f:
            json.dump(self._hashes, f, indent=2)

    def sanitize_path(self, base_path: Path, user_input: str) -> Path:
        """
        Sanitize a user-provided path string to prevent directory traversal attacks.
        Ensures the resolved path is strictly within the base_path.
        
        Args:
            base_path: The allowed root directory.
            user_input: The user-provided path string (e.g., from config or CLI).
        
        Returns:
            The resolved, safe Path object.
        
        Raises:
            SecurityError: If the resolved path escapes the base_path.
        """
        if not base_path.is_absolute():
            base_path = base_path.resolve()
        
        # Construct the candidate path
        candidate = base_path / user_input
        
        # Resolve to handle symlinks, .., etc.
        try:
            resolved = candidate.resolve()
        except Exception as e:
            raise SecurityError(f"Path resolution failed for {user_input}: {e}")
        
        # Ensure the resolved path starts with the base path
        try:
            resolved.relative_to(base_path)
        except ValueError:
            raise SecurityError(
                f"Security violation: Path '{user_input}' resolves to '{resolved}' "
                f"which is outside the allowed base path '{base_path}'."
            )
        
        logger.debug(f"Path sanitized: {user_input} -> {resolved}")
        return resolved

    def compute_file_hash(self, file_path: Path, algorithm: str = 'sha256') -> str:
        """
        Compute the cryptographic hash of a file.
        
        Args:
            file_path: Path to the file to hash.
            algorithm: Hash algorithm (default 'sha256').
        
        Returns:
            Hexadecimal string of the hash.
        
        Raises:
            FileNotFoundError: If the file does not exist.
            SecurityError: If hashing fails.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found for hashing: {file_path}")
        
        try:
            hasher = hashlib.new(algorithm)
            with open(file_path, 'rb') as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(8192), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            raise SecurityError(f"Failed to compute hash for {file_path}: {e}")

    def validate_model_checksum(self, model_path: Path, artifact_id: Optional[str] = None) -> bool:
        """
        Validate a model file's checksum against the stored hash in state/artifact_hashes.json.
        
        Args:
            model_path: Path to the model file to validate.
            artifact_id: Optional explicit ID to look up in the manifest.
                        If None, the filename (stem) is used as the ID.
        
        Returns:
            True if the checksum matches.
        
        Raises:
            SecurityError: If the checksum does NOT match.
            FileNotFoundError: If the hash manifest is missing the entry.
        """
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # Determine the artifact ID
        if artifact_id is None:
            artifact_id = model_path.name
        
        if artifact_id not in self._hashes:
            raise FileNotFoundError(
                f"Hash entry not found for artifact '{artifact_id}' in {self.hash_file}. "
                "Cannot validate checksum."
            )
        
        expected_hash = self._hashes[artifact_id]
        actual_hash = self.compute_file_hash(model_path)
        
        if actual_hash != expected_hash:
            raise SecurityError(
                f"CHECKSUM MISMATCH for '{artifact_id}' ({model_path}).\n"
                f"Expected: {expected_hash}\n"
                f"Actual:   {actual_hash}\n"
                "Refusing to load potentially corrupted or tampered model."
            )
        
        logger.info(f"Checksum validated successfully for '{artifact_id}'.")
        return True

    def register_model_hash(self, model_path: Path, artifact_id: Optional[str] = None) -> None:
        """
        Compute and register a model's hash into the manifest.
        Use this after downloading or generating a new model file.
        
        Args:
            model_path: Path to the model file.
            artifact_id: Optional ID. Defaults to filename.
        """
        if artifact_id is None:
            artifact_id = model_path.name
        
        if not model_path.exists():
            raise FileNotFoundError(f"Cannot register hash for missing file: {model_path}")
        
        hash_value = self.compute_file_hash(model_path)
        self._hashes[artifact_id] = hash_value
        self._save_hashes()
        logger.info(f"Registered hash for '{artifact_id}': {hash_value}")

def main():
    """
    CLI entry point for security validation tasks.
    Usage:
      python -m code.utils.security --validate <path_to_model> [--id <artifact_id>]
      python -m code.utils.security --register <path_to_model> [--id <artifact_id>]
      python -m code.utils.security --sanitize <base_dir> <user_path>
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Security Hardening Utilities")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate model checksum")
    validate_parser.add_argument("model_path", type=str, help="Path to model file")
    validate_parser.add_argument("--id", type=str, default=None, help="Artifact ID in manifest")
    
    # Register command
    register_parser = subparsers.add_parser("register", help="Register model checksum")
    register_parser.add_argument("model_path", type=str, help="Path to model file")
    register_parser.add_argument("--id", type=str, default=None, help="Artifact ID in manifest")
    
    # Sanitize command
    sanitize_parser = subparsers.add_parser("sanitize", help="Sanitize a path")
    sanitize_parser.add_argument("base_dir", type=str, help="Base directory")
    sanitize_parser.add_argument("user_path", type=str, help="User input path")
    
    args = parser.parse_args()
    manager = SecurityManager()
    
    try:
        if args.command == "validate":
            manager.validate_model_checksum(Path(args.model_path), args.id)
            print("VALIDATION PASSED")
        elif args.command == "register":
            manager.register_model_hash(Path(args.model_path), args.id)
            print("REGISTRATION COMPLETE")
        elif args.command == "sanitize":
            safe_path = manager.sanitize_path(Path(args.base_dir), args.user_path)
            print(f"SAFE PATH: {safe_path}")
        else:
            parser.print_help()
    except SecurityError as e:
        logger.error(f"SECURITY ERROR: {e}")
        exit(1)
    except FileNotFoundError as e:
        logger.error(f"FILE ERROR: {e}")
        exit(1)

if __name__ == "__main__":
    main()