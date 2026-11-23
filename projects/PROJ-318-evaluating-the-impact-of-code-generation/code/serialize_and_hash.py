import json
import hashlib
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Import existing utilities from project API
from utils.repo_loader import load_repo_list, RepoLoaderException
from utils.exceptions import SerializationException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_sha256(file_path: Path) -> str:
    """
    Compute SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to hash
        
    Returns:
        Hexadecimal string of the SHA-256 hash
        
    Raises:
        FileNotFoundError: If the file does not exist
        IOError: If the file cannot be read
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")

def validate_ast_params(data: Dict[str, Any]) -> bool:
    """
    Validate that the data contains the required 'ast_params' list.
    
    Args:
        data: The JSON data to validate
        
    Returns:
        True if ast_params exists and is a list, False otherwise
    """
    if not isinstance(data, dict):
        return False
    if 'ast_params' not in data:
        logger.warning(f"Missing 'ast_params' key in data: {data.get('repo_slug', 'unknown')}")
        return False
    if not isinstance(data['ast_params'], list):
        logger.warning(f"'ast_params' is not a list in data: {data.get('repo_slug', 'unknown')}")
        return False
    return True

def ensure_state_file(state_file_path: Path) -> Dict[str, Any]:
    """
    Ensure the state YAML file exists and initialize it if missing.
    
    Args:
        state_file_path: Path to the state YAML file
        
    Returns:
        The loaded or initialized state dictionary
    """
    # Ensure parent directory exists
    state_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not state_file_path.exists():
        logger.info(f"Initializing new state file: {state_file_path}")
        state_data = {
            "artifact_hashes": {}
        }
        # Write initial YAML content
        with open(state_file_path, 'w') as f:
            f.write("artifact_hashes: {}\n")
        return state_data
    
    # Load existing state
    logger.info(f"Loading existing state file: {state_file_path}")
    state_data = {}
    try:
        with open(state_file_path, 'r') as f:
            content = f.read().strip()
            if not content:
                state_data = {"artifact_hashes": {}}
            else:
                # Simple YAML parsing for this specific structure
                # Format: artifact_hashes: { 'key': 'value' }
                if content.startswith("artifact_hashes:"):
                    # Handle empty dict case
                    if "{}" in content:
                        state_data = {"artifact_hashes": {}}
                    else:
                        # Parse the dictionary part manually
                        dict_str = content.split("artifact_hashes:")[1].strip()
                        # Remove outer braces and split by comma
                        dict_str = dict_str.strip("{}")
                        if dict_str:
                            pairs = {}
                            # Handle quoted keys and values
                            import re
                            matches = re.findall(r"'([^']+)'\s*:\s*'([^']+)'", dict_str)
                            for key, value in matches:
                                pairs[key] = value
                            state_data = {"artifact_hashes": pairs}
                        else:
                            state_data = {"artifact_hashes": {}}
        return state_data
    except Exception as e:
        logger.error(f"Error reading state file {state_file_path}: {e}")
        # Return empty state on error to allow recovery
        return {"artifact_hashes": {}}

def update_state_file(state_file_path: Path, filename: str, sha256_hash: str) -> None:
    """
    Update the state YAML file with a new artifact hash.
    
    Args:
        state_file_path: Path to the state YAML file
        filename: The filename to record as key
        sha256_hash: The SHA-256 hash value
        
    Raises:
        SerializationException: If the file cannot be written
    """
    try:
        state_data = ensure_state_file(state_file_path)
        
        # Update the hash
        state_data["artifact_hashes"][filename] = sha256_hash
        
        # Write back to file
        with open(state_file_path, 'w') as f:
            f.write("artifact_hashes: {\n")
            items = list(state_data["artifact_hashes"].items())
            for i, (key, value) in enumerate(items):
                comma = "," if i < len(items) - 1 else ""
                f.write(f"  '{key}': '{value}'{comma}\n")
            f.write("}\n")
        
        logger.info(f"Updated state file with hash for {filename}")
    except Exception as e:
        raise SerializationException(f"Failed to update state file: {e}")

def process_repos(
    repos_dir: Path,
    state_file_path: Path,
    max_methods: Optional[int] = None
) -> Dict[str, str]:
    """
    Process all repository JSON files in the directory, compute their checksums,
    and record them in the state file.
    
    Args:
        repos_dir: Directory containing repo JSON files
        state_file_path: Path to the state YAML file
        max_methods: Optional maximum number of methods to validate per repo
        
    Returns:
        Dictionary mapping filenames to their SHA-256 hashes
        
    Raises:
        FileNotFoundError: If the repos directory does not exist
        SerializationException: If any file cannot be processed
    """
    if not repos_dir.exists():
        raise FileNotFoundError(f"Repositories directory not found: {repos_dir}")
    
    # Ensure state file exists
    ensure_state_file(state_file_path)
    
    hashes = {}
    repo_files = sorted(repos_dir.glob("*.json"))
    
    if not repo_files:
        logger.warning(f"No JSON files found in {repos_dir}")
        return hashes
    
    logger.info(f"Processing {len(repo_files)} repository files...")
    
    for repo_file in repo_files:
        try:
            # Compute checksum
            sha256_hash = compute_sha256(repo_file)
            hashes[str(repo_file)] = sha256_hash
            
            # Validate structure and row count
            with open(repo_file, 'r') as f:
                data = json.load(f)
            
            # Validate ast_params
            if not validate_ast_params(data):
                logger.warning(f"Invalid ast_params in {repo_file.name}")
            
            # Validate row count if max_methods is specified
            if max_methods is not None:
                methods = data.get('methods', [])
                if len(methods) > max_methods:
                    logger.warning(
                        f"Repository {repo_file.name} has {len(methods)} methods, "
                        f"exceeding max of {max_methods}"
                    )
            
            # Update state file
            update_state_file(state_file_path, str(repo_file), sha256_hash)
            
            logger.info(f"Processed {repo_file.name}: {sha256_hash[:16]}...")
            
        except json.JSONDecodeError as e:
            raise SerializationException(f"Invalid JSON in {repo_file}: {e}")
        except Exception as e:
            raise SerializationException(f"Error processing {repo_file}: {e}")
    
    return hashes

def main():
    """Main entry point for the serialization and hashing script."""
    try:
        # Define paths
        repos_dir = Path("data/raw/repos")
        state_file_path = Path("state/projects/PROJ-318-evaluating-the-impact-of-code-generation.yaml")
        
        # Load config for max_methods if needed
        try:
            from config import MAX_METHODS
            max_methods = MAX_METHODS
        except ImportError:
            max_methods = 1000  # Default fallback
        
        logger.info("Starting repository serialization and hashing...")
        logger.info(f"Repos directory: {repos_dir}")
        logger.info(f"State file: {state_file_path}")
        logger.info(f"Max methods per repo: {max_methods}")
        
        # Process repositories
        hashes = process_repos(repos_dir, state_file_path, max_methods)
        
        # Summary
        logger.info(f"Successfully processed {len(hashes)} repositories")
        logger.info("Artifact hashes recorded in state file")
        
        # Print summary for verification
        print(f"\nProcessed {len(hashes)} repositories:")
        for filename, hash_val in sorted(hashes.items()):
            print(f"  {filename}: {hash_val[:16]}...")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except SerializationException as e:
        logger.error(f"Serialization error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
