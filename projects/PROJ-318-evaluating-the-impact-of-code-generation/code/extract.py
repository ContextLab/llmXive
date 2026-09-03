import json
import logging
import os
import sys
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.ast_parser import parse_python_files
from utils.file_walker import collect_python_files
from utils.repo_loader import load_repo_list
from utils.exceptions import SerializationException, RepoLoaderException
from utils.models import serialize_pairs_to_json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/extract.log')
    ]
)
logger = logging.getLogger(__name__)

MAX_METHODS_PER_REPO = 1000

def extract_repo_methods(repo_path: Path, repo_id: str) -> List[Dict[str, Any]]:
    """
    Extract method signatures and docstrings from a single repository.
    Truncates to MAX_METHODS_PER_REPO.
    """
    logger.info(f"Extracting methods from {repo_path} (ID: {repo_id})")
    
    py_files = list(collect_python_files(repo_path))
    if not py_files:
        logger.warning(f"No Python files found in {repo_path}")
        return []

    # Parse all files
    all_methods = []
    for file_path in py_files:
        try:
            methods = parse_python_files([file_path])
            all_methods.extend(methods)
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            continue

    # Truncate if necessary
    if len(all_methods) > MAX_METHODS_PER_REPO:
        logger.info(f"Truncating {len(all_methods)} methods to {MAX_METHODS_PER_REPO} for {repo_id}")
        all_methods = all_methods[:MAX_METHODS_PER_REPO]
    
    logger.info(f"Extracted {len(all_methods)} methods from {repo_id}")
    return all_methods

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def record_state_hash(artifact_path: Path, project_id: str) -> None:
    """
    Compute SHA-256 of the artifact and record it in state/projects/{project_id}.yaml.
    Creates the state/projects directory and file if they don't exist.
    """
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact file not found: {artifact_path}")

    checksum = compute_file_checksum(artifact_path)
    logger.info(f"Computed checksum for {artifact_path}: {checksum}")

    state_dir = Path("state/projects")
    state_dir.mkdir(parents=True, exist_ok=True)

    state_file = state_dir / f"{project_id}.yaml"
    
    # Load existing state or initialize
    existing_hashes = {}
    if state_file.exists():
        try:
            import yaml
            with open(state_file, 'r') as f:
                state_data = yaml.safe_load(f) or {}
                existing_hashes = state_data.get('artifact_hashes', {})
        except Exception as e:
            logger.warning(f"Could not load existing state file: {e}")
            existing_hashes = {}

    # Update with new hash
    existing_hashes[artifact_path.name] = checksum

    # Write back
    import yaml
    state_data = {
        'project_id': project_id,
        'artifact_hashes': existing_hashes
    }
    with open(state_file, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Recorded checksum for {artifact_path.name} in {state_file}")

def process_repositories(repo_list_path: Path, output_dir: Path, project_id: str) -> None:
    """
    Process all repositories in the list, extract methods, and save to JSON.
    """
    try:
        repos = load_repo_list(repo_list_path)
    except RepoLoaderException as e:
        logger.error(f"Failed to load repo list: {e}")
        raise

    output_dir.mkdir(parents=True, exist_ok=True)

    processed_count = 0
    for repo in repos:
        repo_id = repo.get('id') or repo.get('repo_url', '').replace('/', '_').replace('.', '_')
        repo_path = Path(repo.get('local_path'))
        
        if not repo_path.exists():
            logger.warning(f"Repository path does not exist: {repo_path}. Skipping.")
            continue

        methods = extract_repo_methods(repo_path, repo_id)
        
        if not methods:
            logger.warning(f"No methods extracted for {repo_id}. Skipping serialization.")
            continue

        # Serialize to JSON
        output_file = output_dir / f"{repo_id}.json"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(methods, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(methods)} methods to {output_file}")
            
            # Record hash in state
            record_state_hash(output_file, project_id)
            processed_count += 1
        except Exception as e:
            logger.error(f"Failed to save or record state for {repo_id}: {e}")
            raise SerializationException(f"Failed to serialize {repo_id}: {e}")

    logger.info(f"Successfully processed {processed_count} repositories.")

def main():
    """Main entry point for extraction."""
    # Default paths
    repo_list_path = Path("data/raw/repo_list.json")
    output_dir = Path("data/raw/repos")
    project_id = "PROJ-318-evaluating-the-impact-of-code-generation"

    if len(sys.argv) > 1:
        repo_list_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_dir = Path(sys.argv[2])
    if len(sys.argv) > 3:
        project_id = sys.argv[3]

    logger.info(f"Starting extraction with repo list: {repo_list_path}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Project ID: {project_id}")

    try:
        process_repositories(repo_list_path, output_dir, project_id)
        logger.info("Extraction completed successfully.")
    except Exception as e:
        logger.error(f"Extraction failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()