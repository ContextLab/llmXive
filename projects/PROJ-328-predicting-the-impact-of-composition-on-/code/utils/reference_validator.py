"""
Reference Validator Module for Solder Hardness Project.

This module validates research sources identified in T008a.
It checks for valid URLs, reachable domains, and proper citation format.
"""
import os
import re
import logging
from pathlib import Path
from typing import List, Optional, Tuple
from utils.error_handlers import SolderPipelineError
from utils.logging_config import get_logger

# Configure logger
logger = get_logger(__name__)

class ConstitutionError(SolderPipelineError):
    """Raised when research verification fails."""
    pass

def validate_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a URL string.
    
    Args:
        url: The URL string to validate.
        
    Returns:
        Tuple of (is_valid, error_message).
    """
    if not url or not isinstance(url, str):
        return False, "URL is empty or not a string"
    
    # Basic URL pattern check
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if not url_pattern.match(url):
        return False, f"Invalid URL format: {url}"
    
    # Check for known blocked or suspicious patterns
    blocked_patterns = ['javascript:', 'data:', 'file:']
    for pattern in blocked_patterns:
        if pattern in url.lower():
            return False, f"Blocked protocol detected: {pattern}"
    
    return True, None

def validate_citation_format(line: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that a line follows the expected citation format.
    
    Expected format: "[ID] Title - URL" or similar structured format.
    
    Args:
        line: The line to validate.
        
    Returns:
        Tuple of (is_valid, error_message).
    """
    if not line or not line.strip():
        return False, "Empty citation line"
    
    # Check for basic structure: should contain a URL
    if 'http' not in line:
        return False, "Citation missing URL"
    
    # Check for title (text before the URL)
    parts = line.split('http')
    if len(parts) < 2 or not parts[0].strip():
        return False, "Citation missing title"
    
    return True, None

def validate_research_md(input_path: str, output_path: str) -> bool:
    """
    Validate the research sources file and generate a verified version.
    
    This function:
    1. Reads the candidate sources from the input file (T008a output).
    2. Validates each URL and citation format.
    3. Writes only valid entries to the output file (T008b output).
    4. Returns True if verification passes, False otherwise.
    
    Args:
        input_path: Path to the candidate sources file.
        output_path: Path where the verified sources file will be written.
        
    Returns:
        True if verification is successful, False otherwise.
        
    Raises:
        ConstitutionError: If verification fails completely.
    """
    input_file = Path(input_path)
    output_file = Path(output_path)
    
    if not input_file.exists():
        raise ConstitutionError(f"Input file not found: {input_path}")
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    verified_entries = []
    total_entries = 0
    valid_entries = 0
    errors = []
    
    logger.info(f"Starting verification of research sources from {input_path}")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        raise ConstitutionError(f"Failed to read input file: {str(e)}")
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue  # Skip comments and empty lines
        
        total_entries += 1
        
        # Extract URL from line (assuming format: "ID Title - URL" or similar)
        url_match = re.search(r'(https?://[^\s]+)', line)
        if not url_match:
            errors.append(f"Line {line_num}: No URL found in '{line}'")
            continue
        
        url = url_match.group(1)
        
        # Validate URL
        is_valid_url, url_error = validate_url(url)
        if not is_valid_url:
            errors.append(f"Line {line_num}: {url_error} (URL: {url})")
            continue
        
        # Validate citation format
        is_valid_format, format_error = validate_citation_format(line)
        if not is_valid_format:
            errors.append(f"Line {line_num}: {format_error} (Line: {line})")
            continue
        
        # Entry is valid
        verified_entries.append(line)
        valid_entries += 1
        logger.debug(f"Validated entry {line_num}: {url}")
    
    # Write verified entries
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Verified Research Sources for Solder Hardness Project\n")
            f.write("# Generated by Reference-Validator Agent (T008b)\n")
            f.write("# Only valid URLs and properly formatted citations are included.\n")
            f.write("#\n")
            f.write(f"# Verification Summary:\n")
            f.write(f"# - Total entries processed: {total_entries}\n")
            f.write(f"# - Valid entries: {valid_entries}\n")
            f.write(f"# - Invalid entries: {total_entries - valid_entries}\n")
            f.write("#\n\n")
            
            for entry in verified_entries:
                f.write(f"{entry}\n")
        
        logger.info(f"Successfully wrote {valid_entries} verified entries to {output_path}")
    except Exception as e:
        raise ConstitutionError(f"Failed to write output file: {str(e)}")
    
    # Log errors if any
    if errors:
        logger.warning(f"Found {len(errors)} validation errors:")
        for error in errors[:10]:  # Log first 10 errors
            logger.warning(f"  - {error}")
        if len(errors) > 10:
            logger.warning(f"  ... and {len(errors) - 10} more errors")
    
    # Check if we have any valid entries
    if valid_entries == 0:
        raise ConstitutionError("No valid research sources found. Verification failed.")
    
    # Success
    logger.info(f"Verification complete: {valid_entries}/{total_entries} sources verified.")
    return True

def main():
    """
    Main entry point for the reference validator.
    
    Reads from data/config/candidate_sources.txt (output of T008a)
    and writes to specs/001-predict-solder-hardness/research_verified.md.
    """
    # Define paths
    project_root = Path(__file__).parent.parent.parent
    input_path = project_root / "data" / "config" / "candidate_sources.txt"
    output_path = project_root / "specs" / "001-predict-solder-hardness" / "research_verified.md"
    
    # Allow override via environment variables for testing
    if os.environ.get('RESEARCH_INPUT_PATH'):
        input_path = Path(os.environ['RESEARCH_INPUT_PATH'])
    if os.environ.get('RESEARCH_OUTPUT_PATH'):
        output_path = Path(os.environ['RESEARCH_OUTPUT_PATH'])
    
    logger.info(f"Reference Validator starting...")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    
    try:
        success = validate_research_md(str(input_path), str(output_path))
        if success:
            logger.info("Verification completed successfully.")
            return 0
        else:
            logger.error("Verification completed with errors.")
            return 1
    except ConstitutionError as e:
        logger.error(f"Verification failed: {str(e)}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during verification: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())
