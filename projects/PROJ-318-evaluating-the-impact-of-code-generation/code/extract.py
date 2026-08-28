import json
import logging
import os
import sys
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.ast_parser import parse_python_files, ASTParsingException
from utils.file_walker import collect_python_files
from utils.models import MethodSignature, DocstringPair, serialize_pairs_to_json, compute_checksum
from utils.repo_loader import load_repo_list
from config import get_config

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

def extract_repo_methods(repo_path: Path, repo_name: str) -> List[DocstringPair]:
    """
    Extract public method signatures and docstrings from a single repository.
    
    Args:
        repo_path: Path to the cloned repository
        repo_name: Name of the repository for logging
        
    Returns:
        List of DocstringPair objects containing method signatures and docstrings
    """
    logger.info(f"Processing repository: {repo_name}")
    
    # Collect all Python files
    py_files = list(collect_python_files(repo_path))
    logger.info(f"Found {len(py_files)} Python files in {repo_name}")
    
    if not py_files:
        logger.warning(f"No Python files found in {repo_name}")
        return []
    
    # Parse all files
    try:
        parsed_data = parse_python_files(py_files)
    except ASTParsingException as e:
        logger.error(f"AST parsing failed for {repo_name}: {e}")
        return []
    
    # Process parsed data into DocstringPair objects
    pairs = []
    for file_path, methods in parsed_data.items():
        for method_name, method_info in methods.items():
            # Extract signature
            signature = method_info.get('signature', '')
            
            # Extract docstring - ensure null for missing, not empty string
            docstring_text = method_info.get('docstring')
            human_docstring = None if not docstring_text else docstring_text.strip()
            
            # If docstring is only whitespace, treat as null
            if human_docstring and not human_docstring.strip():
                human_docstring = None
            
            pair = DocstringPair(
                repo_name=repo_name,
                file_path=str(file_path),
                method_name=method_name,
                signature=signature,
                human_docstring=human_docstring
            )
            pairs.append(pair)
    
    # Truncate to max methods per repository
    if len(pairs) > MAX_METHODS_PER_REPO:
        logger.info(f"Truncating {repo_name} from {len(pairs)} to {MAX_METHODS_PER_REPO} methods")
        pairs = pairs[:MAX_METHODS_PER_REPO]
    
    logger.info(f"Extracted {len(pairs)} methods from {repo_name}")
    return pairs

def process_repositories(repo_list_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Process all repositories in the repo list and extract method signatures.
    
    Args:
        repo_list_path: Optional path to repo list JSON file. If None, uses default config.
        
    Returns:
        Dictionary containing extraction results and metadata
    """
    config = get_config()
    if repo_list_path is None:
        repo_list_path = config.repo_list_path
    
    logger.info(f"Loading repository list from: {repo_list_path}")
    repos = load_repo_list(repo_list_path)
    logger.info(f"Loaded {len(repos)} repositories")
    
    all_pairs = []
    repo_stats = {}
    
    for repo_info in repos:
        repo_name = repo_info['repo_name']
        repo_path = Path(repo_info['local_path'])
        
        if not repo_path.exists():
            logger.warning(f"Repository not found: {repo_path}, skipping")
            continue
        
        pairs = extract_repo_methods(repo_path, repo_name)
        all_pairs.extend(pairs)
        
        repo_stats[repo_name] = {
            'total_methods': len(pairs),
            'methods_with_docstrings': sum(1 for p in pairs if p.human_docstring is not None),
            'methods_without_docstrings': sum(1 for p in pairs if p.human_docstring is None)
        }
    
    # Serialize to JSON
    output_path = Path(config.output_dir) / 'extraction_results.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Validate that human_docstring is null (not empty string) for missing docstrings
    for pair in all_pairs:
        if pair.human_docstring == "":
            pair.human_docstring = None
            logger.warning(f"Converted empty string docstring to null for {pair.repo_name}/{pair.method_name}")
    
    data = {
        'metadata': {
            'total_repos': len(repos),
            'total_methods': len(all_pairs),
            'max_methods_per_repo': MAX_METHODS_PER_REPO,
            'repo_stats': repo_stats
        },
        'data': [
            {
                'repo_name': p.repo_name,
                'file_path': p.file_path,
                'method_name': p.method_name,
                'signature': p.signature,
                'human_docstring': p.human_docstring
            }
            for p in all_pairs
        ]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Compute checksum
    checksum = compute_checksum(output_path)
    logger.info(f"Saved extraction results to {output_path}")
    logger.info(f"Total methods extracted: {len(all_pairs)}")
    logger.info(f"Checksum: {checksum}")
    
    return {
        'output_path': str(output_path),
        'total_methods': len(all_pairs),
        'checksum': checksum,
        'repo_stats': repo_stats
    }

def main():
    """Main entry point for the extraction pipeline."""
    try:
        logger.info("Starting extraction pipeline")
        result = process_repositories()
        logger.info(f"Extraction completed successfully: {result['total_methods']} methods")
        return 0
    except Exception as e:
        logger.error(f"Extraction pipeline failed: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())