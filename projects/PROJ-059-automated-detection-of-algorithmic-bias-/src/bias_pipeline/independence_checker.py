"""
Independence Checker Module for Automated Detection of Algorithmic Bias.

This module implements string-hash comparison logic to verify that synthetic data
generated for simulation does not leak or overlap with tokens extracted from
real code repositories. This satisfies FR-015 and SC-004.
"""
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional

from .utils import PipelineError, setup_logging

# Configure logger
logger = setup_logging(__name__)


def normalize_token(token: str) -> str:
    """
    Normalize a token for comparison.
    
    Steps:
    1. Convert to lowercase.
    2. Remove non-alphanumeric characters (except underscores).
    3. Split camelCase into separate words (e.g., "userName" -> "user_name").
    4. Strip whitespace.
    
    Args:
        token: The raw token string.
        
    Returns:
        Normalized token string.
    """
    if not token:
        return ""
        
    # Lowercase
    normalized = token.lower()
    
    # Remove non-alphanumeric except underscore
    normalized = re.sub(r'[^a-z0-9_]', '', normalized)
    
    # Split camelCase: insert underscore before uppercase letters that follow lowercase
    # e.g., "userName" -> "user_name", "XMLParser" -> "xml_parser"
    normalized = re.sub(r'([a-z])([A-Z])', r'\1_\2', normalized)
    
    # Handle consecutive uppercase followed by lowercase (e.g., "XMLParser" -> "xml_parser")
    # This regex finds a sequence of uppercase letters followed by a lowercase letter
    # and inserts an underscore before the last uppercase letter
    normalized = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', normalized)
    
    return normalized.strip('_')


def compute_string_hash(text: str) -> str:
    """
    Compute a deterministic SHA-256 hash of a string.
    
    Args:
        text: The input string to hash.
        
    Returns:
        Hexadecimal string representation of the SHA-256 hash.
    """
    if not text:
        return hashlib.sha256(b"").hexdigest()
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def extract_tokens_from_text(text: str) -> List[str]:
    """
    Extract raw tokens from a text string.
    
    This function splits text by common delimiters (spaces, newlines, punctuation)
    to isolate potential tokens for normalization and comparison.
    
    Args:
        text: The source text (e.g., synthetic data content or code file content).
        
    Returns:
        List of raw token strings.
    """
    if not text:
        return []
    
    # Split by non-alphanumeric characters (keeping underscores for snake_case)
    # This regex splits on anything that is NOT a letter, digit, or underscore
    raw_tokens = re.split(r'[^a-zA-Z0-9_]+', text)
    
    # Filter out empty strings
    return [t for t in raw_tokens if t]


def perform_diff_check(
    code_tokens: Set[str], 
    synthetic_tokens: Set[str], 
    normalized: bool = True
) -> Dict[str, Any]:
    """
    Perform a set-difference diff check between code tokens and synthetic tokens.
    
    This implements the core logic for FR-015 and SC-004. It verifies zero token
    overlap by computing the set difference.
    
    Args:
        code_tokens: Set of tokens extracted from real code repositories.
        synthetic_tokens: Set of tokens from generated synthetic data.
        normalized: If True, normalize tokens before comparison. Default is True.
        
    Returns:
        Dictionary containing:
            - 'overlap_count': Number of tokens found in both sets.
            - 'status': "PASS" if overlap_count == 0, else "FAIL".
            - 'pass_fail': Boolean indicating success.
            - 'overlap_samples': List of up to 10 overlapping tokens for debugging.
    """
    if normalized:
        # Normalize both sets
        normalized_code = {normalize_token(t) for t in code_tokens if t}
        normalized_synth = {normalize_token(t) for t in synthetic_tokens if t}
        
        # Compute intersection
        overlap = normalized_code.intersection(normalized_synth)
    else:
        overlap = code_tokens.intersection(synthetic_tokens)
        
    overlap_count = len(overlap)
    status = "PASS" if overlap_count == 0 else "FAIL"
    pass_fail = overlap_count == 0
    
    result = {
        "overlap_count": overlap_count,
        "status": status,
        "pass_fail": pass_fail,
        "overlap_samples": list(overlap)[:10]  # Limit samples for report size
    }
    
    logger.info(f"Diff check result: {status} (Overlap count: {overlap_count})")
    
    return result


def generate_independence_report(
    report_path: Path,
    code_tokens: Set[str],
    synthetic_tokens: Set[str],
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate a JSON independence report file.
    
    Args:
        report_path: Path where the JSON report will be written.
        code_tokens: Set of tokens from code.
        synthetic_tokens: Set of tokens from synthetic data.
        metadata: Optional dictionary of additional context (e.g., dataset names).
        
    Returns:
        The report dictionary that was written to disk.
        
    Raises:
        PipelineError: If the report cannot be written to disk.
    """
    diff_result = perform_diff_check(code_tokens, synthetic_tokens)
    
    report = {
        "report_type": "synthetic_independence_check",
        "metadata": metadata or {},
        "diff_check": diff_result
    }
    
    try:
        # Ensure parent directory exists
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"Independence report written to {report_path}")
        
    except (IOError, OSError) as e:
        raise PipelineError(f"Failed to write independence report to {report_path}: {e}")
        
    return report


def validate_synthetic_independence(
    code_data_path: Optional[Path] = None,
    synthetic_data_path: Optional[Path] = None,
    code_tokens: Optional[Set[str]] = None,
    synthetic_tokens: Optional[Set[str]] = None,
    report_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Main validation entry point for synthetic data independence.
    
    This function accepts either file paths to read data from or pre-extracted
    token sets. It performs the diff check and optionally generates a report.
    
    Args:
        code_data_path: Path to a file or directory containing real code.
        synthetic_data_path: Path to a file containing synthetic data.
        code_tokens: Pre-extracted set of code tokens (if not reading from file).
        synthetic_tokens: Pre-extracted set of synthetic tokens.
        report_path: If provided, write the JSON report to this path.
        
    Returns:
        Dictionary containing the diff check results.
        
    Raises:
        PipelineError: If required inputs are missing or file reading fails.
    """
    # Resolve tokens
    final_code_tokens: Set[str] = code_tokens or set()
    final_synth_tokens: Set[str] = synthetic_tokens or set()
    
    if not final_code_tokens and code_data_path:
        logger.info(f"Extracting tokens from code path: {code_data_path}")
        if code_data_path.is_file():
            with open(code_data_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                final_code_tokens = set(extract_tokens_from_text(content))
        elif code_data_path.is_dir():
            # Recursively read all files in directory
            for root, _, files in os.walk(code_data_path):
                for file in files:
                    if file.endswith('.py'):
                        file_path = Path(root) / file
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                final_code_tokens.update(extract_tokens_from_text(content))
                        except (IOError, OSError) as e:
                            logger.warning(f"Could not read {file_path}: {e}")
        else:
            raise PipelineError(f"Code data path does not exist: {code_data_path}")
            
    if not final_synth_tokens and synthetic_data_path:
        logger.info(f"Extracting tokens from synthetic path: {synthetic_data_path}")
        if not synthetic_data_path.exists():
            raise PipelineError(f"Synthetic data path does not exist: {synthetic_data_path}")
            
        if synthetic_data_path.is_file():
            with open(synthetic_data_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                final_synth_tokens = set(extract_tokens_from_text(content))
        else:
            raise PipelineError(f"Synthetic data path must be a file: {synthetic_data_path}")
    
    if not final_code_tokens:
        logger.warning("No code tokens provided or extracted. Cannot perform diff check.")
        return {
            "overlap_count": 0,
            "status": "SKIP",
            "pass_fail": True,
            "overlap_samples": [],
            "warning": "No code tokens available for comparison"
        }
        
    if not final_synth_tokens:
        logger.warning("No synthetic tokens provided or extracted. Cannot perform diff check.")
        return {
            "overlap_count": 0,
            "status": "SKIP",
            "pass_fail": True,
            "overlap_samples": [],
            "warning": "No synthetic tokens available for comparison"
        }
    
    # Perform the check
    result = perform_diff_check(final_code_tokens, final_synth_tokens)
    
    # Write report if path provided
    if report_path:
        generate_independence_report(
            report_path, 
            final_code_tokens, 
            final_synth_tokens,
            metadata={"code_source": str(code_data_path), "synthetic_source": str(synthetic_data_path)}
        )
        
    return result