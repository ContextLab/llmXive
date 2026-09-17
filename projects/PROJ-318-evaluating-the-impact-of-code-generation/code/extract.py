"""
Extract public method signatures and docstrings from Python repositories.

This module implements the AST-based extraction pipeline for User Story 1.
It processes repositories listed in the frozen repo list, extracts public methods
with their signatures and docstrings, and serializes the results to JSON.
"""
import json
import logging
import os
import sys
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from project utilities
from utils.ast_parser import parse_python_file, ASTParsingException
from utils.file_walker import walk_python_files, FileWalkerException
from utils.repo_loader import load_repo_list, RepoLoaderException
from utils.exceptions import GitCloneException, SerializationException
import utils.git_clone as git_clone

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

# Constants
MAX_METHODS_PER_REPO = 1000  # Per Spec FR-001
REPO_LIST_PATH = Path('data/raw/frozen_repo_list.json')
REPOS_DIR = Path('data/raw/repos')


def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def extract_repo_methods(
    repo_path: Path,
    max_methods: int = MAX_METHODS_PER_REPO
) -> List[Dict[str, Any]]:
    """
    Extract public method signatures and docstrings from a repository.
    
    Args:
        repo_path: Path to the cloned repository
        max_methods: Maximum number of methods to extract (per Spec FR-001)
        
    Returns:
        List of dictionaries containing method signatures and docstrings
    """
    logger.info(f"Extracting methods from {repo_path}")
    all_methods = []
    
    try:
        # Walk through all Python files in the repository
        python_files = list(walk_python_files(repo_path))
        logger.info(f"Found {len(python_files)} Python files in {repo_path}")
        
        for py_file in python_files:
            try:
                # Parse the file using AST
                parsed_data = parse_python_file(py_file)
                
                if parsed_data and 'methods' in parsed_data:
                    for method in parsed_data['methods']:
                        # Only include public methods (not starting with underscore)
                        if not method['name'].startswith('_'):
                            all_methods.append({
                                'file_path': str(py_file),
                                'method_name': method['name'],
                                'signature': method['signature'],
                                'human_docstring': method.get('docstring'),
                                'ast_params': method.get('params', []),
                                'line_number': method.get('line_number')
                            })
                            
                            # Check if we've reached the limit
                            if len(all_methods) >= max_methods:
                                logger.info(
                                    f"Reached maximum method limit ({max_methods}) "
                                    f"for {repo_path.name}"
                                )
                                return all_methods[:max_methods]
                                
            except ASTParsingException as e:
                logger.warning(f"Failed to parse {py_file}: {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error parsing {py_file}: {e}")
                continue
                
    except FileWalkerException as e:
        logger.error(f"Failed to walk repository {repo_path}: {e}")
        raise
        
    logger.info(f"Extracted {len(all_methods)} public methods from {repo_path}")
    return all_methods


def process_repositories(
    repo_list_path: Optional[Path] = None,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Process all repositories in the frozen list.
    
    Args:
        repo_list_path: Path to the frozen repo list JSON
        output_dir: Directory to write output JSON files
        
    Returns:
        Dictionary with processing statistics
    """
    if repo_list_path is None:
        repo_list_path = REPO_LIST_PATH
    if output_dir is None:
        output_dir = REPOS_DIR
        
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load repository list
    try:
        repos = load_repo_list(repo_list_path)
    except RepoLoaderException as e:
        logger.error(f"Failed to load repository list: {e}")
        raise
        
    logger.info(f"Processing {len(repos)} repositories")
    
    stats = {
        'total_repos': len(repos),
        'successful_repos': 0,
        'failed_repos': 0,
        'total_methods': 0,
        'repos': []
    }
    
    for repo_info in repos:
        repo_slug = repo_info['repo_slug']
        repo_url = repo_info['github_url']
        repo_local_path = output_dir.parent / 'repos' / repo_slug
        
        logger.info(f"Processing repository: {repo_slug}")
        
        try:
            # Clone repository if it doesn't exist
            if not repo_local_path.exists():
                logger.info(f"Cloning {repo_url} to {repo_local_path}")
                git_clone.clone_repository(repo_url, repo_local_path)
            
            # Verify repository exists
            if not repo_local_path.exists():
                raise FileNotFoundError(f"Repository not found at {repo_local_path}")
            
            # Extract methods
            methods = extract_repo_methods(repo_local_path, MAX_METHODS_PER_REPO)
            
            # Prepare output data
            output_data = {
                'repo_slug': repo_slug,
                'repo_url': repo_url,
                'total_methods': len(methods),
                'max_methods_limit': MAX_METHODS_PER_REPO,
                'methods': methods
            }
            
            # Write to JSON file
            output_file = output_dir / f"{repo_slug}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            # Compute and record checksum
            checksum = compute_file_checksum(output_file)
            output_data['checksum'] = checksum
            
            # Update statistics
            stats['successful_repos'] += 1
            stats['total_methods'] += len(methods)
            stats['repos'].append({
                'slug': repo_slug,
                'methods_extracted': len(methods),
                'output_file': str(output_file),
                'checksum': checksum
            })
            
            logger.info(
                f"Successfully processed {repo_slug}: "
                f"{len(methods)} methods extracted, "
                f"output: {output_file}"
            )
            
        except Exception as e:
            stats['failed_repos'] += 1
            logger.error(f"Failed to process {repo_slug}: {e}", exc_info=True)
            stats['repos'].append({
                'slug': repo_slug,
                'error': str(e)
            })
            
    # Log summary
    logger.info(
        f"Processing complete: {stats['successful_repos']}/{stats['total_repos']} "
        f"repositories successful, {stats['total_methods']} total methods extracted"
    )
    
    return stats


def record_state_hash(
    state_file: Path,
    artifact_path: Path,
    checksum: str
) -> None:
    """
    Record the checksum of an artifact in the project state file.
    
    Args:
        state_file: Path to the YAML state file
        artifact_path: Path to the artifact
        checksum: SHA-256 checksum of the artifact
    """
    import yaml
    
    # Ensure state directory exists
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing state or create new
    if state_file.exists():
        with open(state_file, 'r', encoding='utf-8') as f:
            state = yaml.safe_load(f) or {}
    else:
        state = {'artifact_hashes': {}}
        
    if 'artifact_hashes' not in state:
        state['artifact_hashes'] = {}
        
    # Update checksum
    state['artifact_hashes'][str(artifact_path)] = checksum
    
    # Write back to file
    with open(state_file, 'w', encoding='utf-8') as f:
        yaml.dump(state, f, default_flow_style=False)
        
    logger.info(f"Recorded checksum for {artifact_path} in {state_file}")


def main() -> int:
    """
    Main entry point for the extraction pipeline.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        logger.info("Starting repository extraction pipeline")
        
        # Verify repo list exists
        if not REPO_LIST_PATH.exists():
            raise FileNotFoundError(
                f"Repository list not found at {REPO_LIST_PATH}. "
                f"Run T010 to generate it first."
            )
        
        # Process all repositories
        stats = process_repositories()
        
        # Verify output
        output_files = list(REPOS_DIR.glob("*.json"))
        logger.info(f"Generated {len(output_files)} output files")
        
        # Check that each file has <= 1000 methods
        for output_file in output_files:
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            method_count = data.get('total_methods', 0)
            if method_count > MAX_METHODS_PER_REPO:
                raise ValueError(
                    f"File {output_file} contains {method_count} methods, "
                    f"exceeding limit of {MAX_METHODS_PER_REPO}"
                )
                
        logger.info(
            f"All output files verified: method counts <= {MAX_METHODS_PER_REPO}"
        )
        
        # Record state hashes
        state_file = Path('state/projects/PROJ-318-evaluating-the-impact-of-code-generation.yaml')
        for output_file in output_files:
            checksum = compute_file_checksum(output_file)
            record_state_hash(state_file, output_file, checksum)
        
        logger.info("Extraction pipeline completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())