"""
Repository extraction pipeline for code documentation analysis.

This module handles the extraction of public method signatures and
human-written docstrings from Python repositories.
"""
import json
import logging
import os
import sys
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
import argparse

# Import from local utilities
from utils.git_clone import clone_repository, clone_repos_from_list
from utils.file_walker import walk_python_files
from utils.ast_parser import parse_python_file
from utils.models import MethodSignature, DocstringPair, serialize_pairs_to_json, compute_checksum
from utils.repo_loader import load_repo_list
from utils.exceptions import GitCloneException, FileWalkerException, ASTParsingException, SerializationException

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

def extract_repo_methods(repo_path: Path, max_methods: int = 1000) -> List[Dict[str, Any]]:
    """
    Extract public method signatures and docstrings from a repository.
    
    Args:
        repo_path: Path to the cloned repository
        max_methods: Maximum number of methods to extract per repository
        
    Returns:
        List of method signature dictionaries
    """
    if not repo_path.exists():
        raise FileWalkerException(f"Repository path does not exist: {repo_path}")
    
    results = []
    python_files = list(walk_python_files(repo_path))
    logger.info(f"Found {len(python_files)} Python files in {repo_path.name}")
    
    for file_path in python_files:
        if len(results) >= max_methods:
            logger.warning(f"Reached max_methods limit ({max_methods}) for {repo_path.name}")
            break
            
        try:
            methods = parse_python_file(file_path)
            for method in methods:
                if len(results) >= max_methods:
                    break
                results.append(method)
        except ASTParsingException as e:
            logger.warning(f"Skipping malformed file {file_path}: {e}")
            continue
            
    logger.info(f"Extracted {len(results)} methods from {repo_path.name}")
    return results

def process_repositories(repo_list: List[Dict[str, Any]], output_dir: Path, max_methods: int = 1000) -> List[Path]:
    """
    Process all repositories in the list and extract method data.
    
    Args:
        repo_list: List of repository dictionaries with 'repo_url' and 'github_url'
        output_dir: Directory to save extracted data
        max_methods: Maximum methods per repository
        
    Returns:
        List of paths to generated JSON files
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_files = []
    
    for repo_info in repo_list:
        repo_url = repo_info.get('repo_url')
        repo_name = repo_info.get('github_url', repo_url.split('/')[-1])
        
        logger.info(f"Processing repository: {repo_name}")
        
        try:
            # Clone repository
            repo_path = clone_repository(repo_url, output_dir.parent / 'repos' / repo_name)
            
            # Extract methods
            methods = extract_repo_methods(repo_path, max_methods)
            
            if not methods:
                logger.warning(f"No methods extracted from {repo_name}")
                continue
                
            # Create output filename
            output_file = output_dir / f"{repo_name}_methods.json"
            
            # Serialize to JSON
            serialized_data = serialize_pairs_to_json(methods)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(serialized_data, f, indent=2)
                
            generated_files.append(output_file)
            logger.info(f"Saved {len(methods)} methods to {output_file}")
            
        except (GitCloneException, FileWalkerException, ASTParsingException) as e:
            logger.error(f"Failed to process {repo_name}: {e}")
            continue
            
    return generated_files

def compute_file_checksum(file_path: Path) -> str:
    """
    Compute SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Hexadecimal string of the SHA-256 hash
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def record_state_hash(project_id: str, artifact_paths: List[Path], state_dir: Path) -> None:
    """
    Record checksums of generated artifacts in the project state file.
    
    Args:
        project_id: Project identifier
        artifact_paths: List of paths to artifact files
        state_dir: Directory containing project state
    """
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / f"{project_id}.yaml"
    
    import yaml
    
    artifact_hashes = {}
    for path in artifact_paths:
        if path.exists():
            checksum = compute_file_checksum(path)
            artifact_hashes[path.name] = checksum
            
    state_data = {
        'project_id': project_id,
        'artifact_hashes': artifact_hashes,
        'generated_files': [str(p) for p in artifact_paths]
    }
    
    with open(state_file, 'w', encoding='utf-8') as f:
        yaml.dump(state_data, f, default_flow_style=False)
        
    logger.info(f"State recorded to {state_file}")

def main():
    """
    Main entry point for the extraction pipeline.
    
    Parses command-line arguments and orchestrates the extraction process.
    """
    parser = argparse.ArgumentParser(
        description='Extract method signatures and docstrings from Python repositories.'
    )
    parser.add_argument(
        '--repo-list',
        type=str,
        default='data/raw/repo_list.json',
        help='Path to the repository list JSON file'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/raw/repos',
        help='Output directory for extracted data'
    )
    parser.add_argument(
        '--state-dir',
        type=str,
        default='state/projects',
        help='Directory for project state files'
    )
    parser.add_argument(
        '--max-methods',
        type=int,
        default=1000,
        help='Maximum number of methods to extract per repository'
    )
    parser.add_argument(
        '--project-id',
        type=str,
        default='PROJ-318-evaluating-the-impact-of-code-generation',
        help='Project identifier for state tracking'
    )
    
    args = parser.parse_args()
    
    logger.info("Starting repository extraction pipeline")
    logger.info(f"Repository list: {args.repo_list}")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"Max methods per repo: {args.max_methods}")
    
    # Load repository list
    try:
        repo_list = load_repo_list(Path(args.repo_list))
        logger.info(f"Loaded {len(repo_list)} repositories")
    except Exception as e:
        logger.error(f"Failed to load repository list: {e}")
        sys.exit(1)
        
    # Process repositories
    output_path = Path(args.output_dir)
    try:
        generated_files = process_repositories(repo_list, output_path, args.max_methods)
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        sys.exit(1)
        
    if not generated_files:
        logger.warning("No files were generated")
        sys.exit(0)
        
    # Record state
    try:
        record_state_hash(args.project_id, generated_files, Path(args.state_dir))
    except Exception as e:
        logger.error(f"Failed to record state: {e}")
        # Don't exit on state recording failure
        
    logger.info("Extraction pipeline completed successfully")

if __name__ == '__main__':
    main()