import os
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from config import Config

logger = logging.getLogger(__name__)

class SecurityManager:
    """
    Security hardening utility for file path sanitization and artifact integrity verification.
    
    Implements:
    1. Path sanitization to prevent directory traversal attacks.
    2. SHA-256 checksum validation against a manifest file.
    """

    def __init__(self, config: Config):
        self.config = config
        self.state_dir = config.state_dir
        self.hashes_file = self.state_dir / "artifact_hashes.json"
        
        # Ensure state directory exists
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def sanitize_path(self, input_path: str, base_dir: Optional[Path] = None) -> Path:
        """
        Sanitize an input path to prevent directory traversal attacks.
        
        Args:
            input_path: The raw user-provided path string.
            base_dir: The base directory that the path must resolve within.
                      If None, uses the project root or config data_dir.
        
        Returns:
            A resolved, safe Path object.
        
        Raises:
            ValueError: If the resolved path escapes the allowed base directory.
        """
        if base_dir is None:
            base_dir = self.config.project_root

        # Resolve the base directory to an absolute path
        base_dir = base_dir.resolve()

        # Construct the candidate path
        # We join base_dir with the input path, then resolve to handle '..' and symlinks
        candidate = (base_dir / input_path).resolve()

        # Check if the candidate is strictly inside the base directory
        # We use os.path.commonpath to handle edge cases with symlinks and relative paths
        try:
            common = os.path.commonpath([str(base_dir), str(candidate)])
            if common != str(base_dir):
                raise ValueError(
                    f"Path traversal detected: '{input_path}' resolves to '{candidate}' "
                    f"which is outside the allowed base directory '{base_dir}'."
                )
        except ValueError as e:
            # If commonpath raises ValueError (different drives on Windows), it's a traversal
            if "path is on mount" in str(e) or "path is on drive" in str(e):
                raise ValueError(
                    f"Path traversal detected: '{input_path}' resolves to a different drive/mount."
                )
            raise

        return candidate

    def compute_hash(self, file_path: Path) -> str:
        """
        Compute the SHA-256 hash of a file.
        
        Args:
            file_path: Path to the file to hash.
        
        Returns:
            Hexadecimal string of the SHA-256 hash.
        
        Raises:
            FileNotFoundError: If the file does not exist.
            PermissionError: If the file cannot be read.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found for hashing: {file_path}")
        
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files (e.g., model weights)
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()

    def load_manifest(self) -> Dict[str, str]:
        """
        Load the artifact hash manifest from disk.
        
        Returns:
            Dictionary mapping relative file paths to their expected SHA-256 hashes.
        """
        if not self.hashes_file.exists():
            logger.warning(f"Hash manifest not found at {self.hashes_file}. Initializing empty manifest.")
            return {}
        
        try:
            with open(self.hashes_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Hash manifest at {self.hashes_file} is corrupted. Resetting.")
            return {}

    def save_manifest(self, manifest: Dict[str, str]) -> None:
        """
        Save the artifact hash manifest to disk.
        
        Args:
            manifest: Dictionary mapping relative file paths to SHA-256 hashes.
        """
        with open(self.hashes_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
            f.write("\n")

    def validate_artifact(self, file_path: Path, relative_path: Optional[str] = None) -> bool:
        """
        Validate a file's integrity against the manifest.
        
        Args:
            file_path: Absolute path to the file to validate.
            relative_path: The key used in the manifest. If None, uses the relative path
                           from the project root.
        
        Returns:
            True if validation passes.
        
        Raises:
            ValueError: If the hash does not match.
            FileNotFoundError: If the file or manifest is missing and cannot be recovered.
        """
        # Sanitize and resolve the path first
        safe_path = self.sanitize_path(str(file_path))
        
        if not safe_path.exists():
            raise FileNotFoundError(f"Artifact not found for validation: {safe_path}")

        if relative_path is None:
            try:
                relative_path = str(safe_path.relative_to(self.config.project_root))
            except ValueError:
                # File is outside project root, which is a security violation
                raise ValueError(f"Artifact '{safe_path}' is outside project root.")

        manifest = self.load_manifest()
        expected_hash = manifest.get(relative_path)

        if expected_hash is None:
            # If the file is new and not in manifest, we could choose to fail or add it.
            # For hardening, we fail loudly if a critical file is missing from the manifest.
            # However, for initial setup, we might need to generate the manifest.
            # Here we assume the manifest should exist for validated artifacts.
            raise ValueError(
                f"Artifact '{relative_path}' not found in manifest. "
                f"Run 'generate_hashes' to update the manifest or check file path."
            )

        actual_hash = self.compute_hash(safe_path)

        if actual_hash != expected_hash:
            raise ValueError(
                f"Integrity check failed for '{relative_path}'.\n"
                f"Expected: {expected_hash}\n"
                f"Actual:   {actual_hash}"
            )

        logger.info(f"Artifact '{relative_path}' validated successfully.")
        return True

    def register_artifact(self, file_path: Path) -> str:
        """
        Compute hash and register/update it in the manifest.
        
        Args:
            file_path: Path to the file to register.
        
        Returns:
            The computed hash.
        """
        safe_path = self.sanitize_path(str(file_path))
        relative_path = str(safe_path.relative_to(self.config.project_root))
        
        actual_hash = self.compute_hash(safe_path)
        
        manifest = self.load_manifest()
        manifest[relative_path] = actual_hash
        self.save_manifest(manifest)
        
        logger.info(f"Registered artifact '{relative_path}' with hash {actual_hash}")
        return actual_hash

    def validate_all_artifacts(self) -> List[Tuple[str, bool]]:
        """
        Validate all artifacts listed in the manifest.
        
        Returns:
            List of tuples (relative_path, is_valid).
        """
        manifest = self.load_manifest()
        results = []
        
        for rel_path, expected_hash in manifest.items():
            full_path = self.config.project_root / rel_path
            try:
                self.validate_artifact(full_path, rel_path)
                results.append((rel_path, True))
            except Exception as e:
                logger.error(f"Validation failed for '{rel_path}': {e}")
                results.append((rel_path, False))
        
        return results

def main():
    """
    Command-line interface for security hardening operations.
    
    Usage:
      python code/utils/security.py validate <file_path>
      python code/utils/security.py register <file_path>
      python code/utils/security.py validate_all
    """
    import sys
    
    config = Config()
    security = SecurityManager(config)
    
    if len(sys.argv) < 2:
        print("Usage: python code/utils/security.py <command> [args]")
        print("Commands: validate <path>, register <path>, validate_all")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "validate":
        if len(sys.argv) < 3:
            print("Error: Missing file path argument")
            sys.exit(1)
        file_path = Path(sys.argv[2])
        try:
            security.validate_artifact(file_path)
            print(f"Validation passed for {file_path}")
        except Exception as e:
            print(f"Validation failed: {e}")
            sys.exit(1)
            
    elif command == "register":
        if len(sys.argv) < 3:
            print("Error: Missing file path argument")
            sys.exit(1)
        file_path = Path(sys.argv[2])
        try:
            security.register_artifact(file_path)
            print(f"Registered {file_path}")
        except Exception as e:
            print(f"Registration failed: {e}")
            sys.exit(1)
            
    elif command == "validate_all":
        results = security.validate_all_artifacts()
        failed = [r[0] for r in results if not r[1]]
        if failed:
            print(f"Validation failed for {len(failed)} artifacts:")
            for f in failed:
                print(f"  - {f}")
            sys.exit(1)
        else:
            print(f"All {len(results)} artifacts validated successfully.")
            
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
