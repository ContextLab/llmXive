"""
Preprocessing module for PR data extraction.

This module handles:
- Token estimation and diff truncation
- Raw comment extraction
- Generating SHA-256 checksums for raw data files
- Saving processed data with checksums
"""

import os
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from local project structure
from code.config.settings import get_paths, ensure_directories

logger = logging.getLogger(__name__)

# Token estimation constants (approximate)
# Based on average 4 characters per token in code
CHAR_PER_TOKEN = 4
# Default truncation limit (tokens)
DEFAULT_TOKEN_LIMIT = 8000


def estimate_tokens(text: str) -> int:
    """
    Estimate the number of tokens in a text string.
    
    Uses a simple heuristic: characters / 4.
    For code, this is a reasonable approximation.
    
    Args:
        text: The text to estimate tokens for
        
    Returns:
        Estimated token count
    """
    if not text:
        return 0
    return len(text) // CHAR_PER_TOKEN


def truncate_diff(diff_text: str, token_limit: int = DEFAULT_TOKEN_LIMIT) -> Tuple[str, bool]:
    """
    Truncate a diff if it exceeds the token limit.
    
    Args:
        diff_text: The full diff text
        token_limit: Maximum tokens to allow
        
    Returns:
        Tuple of (truncated_diff, was_truncated)
    """
    if not diff_text:
        return diff_text, False
    
    estimated_tokens = estimate_tokens(diff_text)
    
    if estimated_tokens <= token_limit:
        return diff_text, False
    
    # Truncate by cutting off at approximately the token limit
    # We cut at character level, trying to preserve some structure
    max_chars = token_limit * CHAR_PER_TOKEN
    
    # Find a good cut point (preferably at a line boundary)
    truncated = diff_text[:max_chars]
    last_newline = truncated.rfind('\n')
    if last_newline > max_chars * 0.9:  # Only adjust if close
        truncated = truncated[:last_newline]
    
    truncated += "\n\n[TRUNCATED: Diff exceeded token limit. Analysis is partial.]"
    
    logger.warning(
        f"Diff truncated from {estimated_tokens} to {token_limit} tokens. "
        f"Analysis is partial."
    )
    
    return truncated, True


def preprocess_pr_data(pr_data: Dict[str, Any], token_limit: int = DEFAULT_TOKEN_LIMIT) -> Dict[str, Any]:
    """
    Preprocess a single PR's data.
    
    Args:
        pr_data: Raw PR data dictionary
        token_limit: Maximum tokens for diff truncation
        
    Returns:
        Preprocessed PR data with truncated diffs if needed
    """
    processed = pr_data.copy()
    
    # Handle diff truncation
    if 'diff' in processed and processed['diff']:
        original_diff = processed['diff']
        processed['diff'], was_truncated = truncate_diff(original_diff, token_limit)
        processed['truncation_flag'] = was_truncated
        
        if was_truncated:
            processed['original_diff_length'] = len(original_diff)
            processed['truncated_diff_length'] = len(processed['diff'])
    else:
        processed['truncation_flag'] = False
    
    return processed


def extract_raw_comments(pr_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract raw review comments from PR data.
    
    Args:
        pr_data: PR data containing review comments
        
    Returns:
        List of comment dictionaries with standardized fields
    """
    comments = []
    
    # Extract from 'review_comments' if present
    if 'review_comments' in pr_data:
        for comment in pr_data['review_comments']:
            comments.append({
                'reviewer_id': comment.get('user', {}).get('login', 'unknown'),
                'comment_body': comment.get('body', ''),
                'timestamp': comment.get('created_at', ''),
                'is_confirmed': False,  # Will be updated by filter_human_confirmations
                'linked_pr_id': pr_data.get('number'),
                'comment_type': 'review'
            })
    
    # Extract from 'comments' (general PR comments) if present
    if 'comments' in pr_data:
        for comment in pr_data['comments']:
            comments.append({
                'reviewer_id': comment.get('user', {}).get('login', 'unknown'),
                'comment_body': comment.get('body', ''),
                'timestamp': comment.get('created_at', ''),
                'is_confirmed': False,
                'linked_pr_id': pr_data.get('number'),
                'comment_type': 'comment'
            })
    
    return comments


def generate_checksums(file_path: Path) -> str:
    """
    Generate SHA-256 checksum for a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Hexadecimal SHA-256 checksum string
    """
    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        # Read in chunks for large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest()

def save_raw_with_checksums(raw_data: List[Dict[str, Any]], output_dir: Path) -> Path:
    """
    Save raw PR data to JSON and generate checksums.
    
    Args:
        raw_data: List of PR data dictionaries
        output_dir: Directory to save files
        
    Returns:
        Path to the saved checksums file
    """
    # Ensure output directory exists
    ensure_directories([output_dir])
    
    # Save raw data
    raw_file = output_dir / "pr_data_raw.json"
    with open(raw_file, 'w', encoding='utf-8') as f:
        json.dump(raw_data, f, indent=2, ensure_ascii=False)
    
    # Generate checksum for the raw file
    checksum = generate_checksums(raw_file)
    
    # Create checksums dictionary
    checksums_data = {
        'files': [
            {
                'filename': 'pr_data_raw.json',
                'checksum': checksum,
                'algorithm': 'sha256',
                'record_count': len(raw_data)
            }
        ],
        'generated_at': str(Path(output_dir).parent / 'logs' / 'checksums.log'),
        'checksum_file': str(raw_file)
    }
    
    # Save checksums
    checksums_file = output_dir / "checksums.json"
    with open(checksums_file, 'w', encoding='utf-8') as f:
        json.dump(checksums_data, f, indent=2)
    
    logger.info(f"Saved raw data to {raw_file} with checksum: {checksum}")
    logger.info(f"Saved checksums to {checksums_file}")
    
    return checksums_file


def main():
    """
    Main entry point for preprocessing with checksum generation.
    
    This function:
    1. Loads raw PR data from data/raw/pr_data_raw.json (output of T012)
    2. Preprocesses each PR (truncates diffs if needed)
    3. Saves processed data back to data/raw/ with SHA-256 checksums
    4. Logs truncation warnings to logs/truncation.log
    """
    # Setup logging
    from code.src.utils.logger import get_logger, setup_pipeline_logging
    setup_pipeline_logging()
    logger = get_logger(__name__)
    
    logger.info("Starting preprocessing with checksum generation (T015)")
    
    # Get paths
    paths = get_paths()
    raw_data_dir = paths['data_raw']
    
    # Check if raw data exists
    raw_file = raw_data_dir / "pr_data_raw.json"
    if not raw_file.exists():
        logger.error(f"Raw data file not found: {raw_file}")
        logger.error("Please run T012 (fetch_prs) first to generate raw data.")
        return
    
    # Load raw data
    logger.info(f"Loading raw data from {raw_file}")
    with open(raw_file, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    logger.info(f"Loaded {len(raw_data)} PR records")
    
    # Preprocess each PR
    processed_data = []
    for pr in raw_data:
        processed_pr = preprocess_pr_data(pr)
        processed_data.append(processed_pr)
        
        # Log truncation info
        if processed_pr.get('truncation_flag'):
            logger.warning(
                f"PR #{pr.get('number', 'unknown')} truncated: "
                f"original={processed_pr.get('original_diff_length', 0)} chars, "
                f"truncated={processed_pr.get('truncated_diff_length', 0)} chars"
            )
    
    # Save processed data with checksums
    checksums_path = save_raw_with_checksums(processed_data, raw_data_dir)
    
    logger.info("Preprocessing with checksum generation complete")
    logger.info(f"Checksums saved to: {checksums_path}")

if __name__ == "__main__":
    main()
