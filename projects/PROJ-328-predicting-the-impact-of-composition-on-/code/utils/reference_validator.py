import os
import re
import logging
import requests
from pathlib import Path
from typing import List, Optional, Tuple
from utils.error_handlers import ConfigurationError
from utils.logging_config import get_logger

logger = get_logger(__name__)

class ConstitutionError(Exception):
    """Raised when a reference violates constitutional requirements."""
    pass

def validate_url(url: str) -> bool:
    """
    Validate that a URL is well-formed and accessible.
    
    Args:
        url: The URL string to validate.
        
    Returns:
        True if the URL is valid and accessible, False otherwise.
    """
    if not url or not isinstance(url, str):
        return False
        
    # Basic URL format check
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
    if not url_pattern.match(url):
        logger.warning(f"Invalid URL format: {url}")
        return False
        
    # Check accessibility (with timeout to avoid hanging)
    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        # 200 OK or 301/302 redirects are acceptable
        if response.status_code in [200, 301, 302, 403]:
            # 403 might be a paywall but the URL is valid
            return True
        else:
            logger.warning(f"URL returned status {response.status_code}: {url}")
            return False
    except requests.RequestException as e:
        logger.warning(f"Failed to access URL {url}: {e}")
        return False

def validate_citation_format(citation: str) -> bool:
    """
    Validate that a citation string follows a basic format.
    
    Args:
        citation: The citation string to validate.
        
    Returns:
        True if the citation appears valid, False otherwise.
    """
    if not citation or not isinstance(citation, str):
        return False
        
    # Basic check: should have some text and not be empty
    # A more sophisticated check could validate DOI format, author names, etc.
    if len(citation.strip()) < 10:
        logger.warning(f"Citation too short: {citation}")
        return False
        
    # Check for DOI pattern if present
    doi_pattern = r'10\.\d{4,9}/[-._;()/:A-Z0-9]+'
    if 'doi:' in citation.lower() or 'doi.org' in citation.lower():
        if not re.search(doi_pattern, citation, re.IGNORECASE):
            logger.warning(f"Citation mentions DOI but no valid DOI found: {citation}")
            return False
            
    return True

def validate_research_md(research_md_path: Path, output_path: Path) -> Tuple[bool, List[dict]]:
    """
    Validate the research.md file and extract verified references.
    
    Args:
        research_md_path: Path to the research.md file to validate.
        output_path: Path where the verified research file will be written.
        
    Returns:
        Tuple of (success: bool, verified_sources: List[dict])
    """
    if not research_md_path.exists():
        logger.error(f"Research file not found: {research_md_path}")
        return False, []
        
    verified_sources = []
    failed_sources = []
    
    with open(research_md_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Parse markdown to extract URLs and citations
    # Look for patterns like: - [URL](description) or - URL: description
    url_pattern = re.compile(r'[-*]\s*\[([^\]]+)\]\(([^)]+)\)|[-*]\s*([^\s]+)\s*[:\-]\s*(.+)', re.MULTILINE)
    
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        # Try to extract URL and citation from markdown link format
        match = re.search(r'\[([^\]]+)\]\(([^)]+)\)', line)
        if match:
            citation = match.group(1)
            url = match.group(2)
        else:
            # Try alternative format: URL: citation
            alt_match = re.search(r'(https?://[^\s]+)\s*[:\-]\s*(.+)', line)
            if alt_match:
                url = alt_match.group(1)
                citation = alt_match.group(2)
            else:
                continue
                
        # Validate URL
        is_valid_url = validate_url(url)
        # Validate citation format
        is_valid_citation = validate_citation_format(citation)
        
        source_entry = {
            'url': url,
            'citation': citation,
            'source_type': 'pdf' if url.endswith('.pdf') or 'doi.org' in url else 'api',
            'verified': is_valid_url and is_valid_citation
        }
        
        if is_valid_url and is_valid_citation:
            verified_sources.append(source_entry)
            logger.info(f"Verified source: {citation} -> {url}")
        else:
            failed_sources.append(source_entry)
            if not is_valid_url:
                logger.warning(f"Failed URL validation: {url}")
            if not is_valid_citation:
                logger.warning(f"Failed citation validation: {citation}")
    
    # Write verified sources to output file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Verified Research Sources\n\n")
        f.write("This file contains only verified citations and URLs from the research process.\n")
        f.write("Generated by Reference-Validator Agent.\n\n")
        f.write("## Verified Sources\n\n")
        
        for i, source in enumerate(verified_sources, 1):
            f.write(f"{i}. **{source['citation']}**\n")
            f.write(f"   - URL: {source['url']}\n")
            f.write(f"   - Type: {source['source_type']}\n\n")
            
        if not verified_sources:
            f.write("No verified sources found.\n\n")
            logger.warning("No verified sources found in research.md")
            
        if failed_sources:
            f.write("## Failed Sources (Excluded)\n\n")
            for i, source in enumerate(failed_sources, 1):
                f.write(f"{i}. **{source['citation']}**\n")
                f.write(f"   - URL: {source['url']}\n")
                f.write(f"   - Reason: {'Invalid URL' if not validate_url(source['url']) else 'Invalid citation'}\n\n")
    
    success = len(verified_sources) > 0
    if not success:
        logger.error("No verified sources found - verification failed")
        
    return success, verified_sources

def main():
    """Main entry point for reference validation."""
    logger.info("Starting reference validation...")
    
    # Define paths
    project_root = Path(__file__).parent.parent.parent
    research_md_path = project_root / 'data' / 'config' / 'candidate_sources.txt'
    output_path = project_root / 'specs' / '001-predict-solder-hardness' / 'research_verified.md'
    
    # If candidate_sources.txt exists as JSON, convert to markdown format first
    if research_md_path.exists():
        # Check if it's the JSON format from T008a
        import json
        try:
            with open(research_md_path, 'r') as f:
                candidates = json.load(f)
                
            # Create a temporary markdown file for validation
            temp_md_path = project_root / 'data' / 'config' / 'research_draft.md'
            with open(temp_md_path, 'w') as f:
                f.write("# Candidate Research Sources\n\n")
                for item in candidates:
                    f.write(f"- [{item.get('citation', 'Unknown')}]({item.get('url', '')})\n")
            
            success, verified = validate_research_md(temp_md_path, output_path)
            
            if success:
                logger.info(f"Successfully verified {len(verified)} sources")
            else:
                logger.error("Verification failed - no sources verified")
                
        except json.JSONDecodeError:
            logger.error("Candidate sources file is not valid JSON")
            return 1
    else:
        logger.error(f"Research file not found: {research_md_path}")
        return 1
        
    return 0 if success else 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
