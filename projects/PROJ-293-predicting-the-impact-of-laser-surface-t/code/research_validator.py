import re
import sys
from pathlib import Path
from typing import List, Tuple

import logging
from logging_config import get_logger, raise_on_missing_data

logger = get_logger(__name__)

# Patterns for static data sources
OPENML_PATTERN = re.compile(r'https?://www\.openml\.org/search\?type=data&id=\d+')
HUGGINGFACE_PATTERN = re.compile(r'https?://huggingface\.co/datasets/[a-zA-Z0-9_\-/]+')
GITHUB_DATA_PATTERN = re.compile(r'https?://github\.com/[a-zA-Z0-9_\-/]+/blob/[a-zA-Z0-9_\-/]+/data/[a-zA-Z0-9_\-./]+')
DOI_PATTERN = re.compile(r'https?://doi\.org/10\.\d+/[a-zA-Z0-9_\-./]+')

# Patterns for dynamic search logic (to be rejected)
DYNAMIC_SEARCH_PATTERNS = [
    re.compile(r'search\?q=', re.IGNORECASE),
    re.compile(r'query=', re.IGNORECASE),
    re.compile(r'keyword=', re.IGNORECASE),
    re.compile(r'filter=', re.IGNORECASE),
    re.compile(r'api/search', re.IGNORECASE),
]

def parse_research_md(file_path: str) -> Tuple[bool, List[str]]:
    """
    Verify that research.md contains only verified static URLs/IDs.
    
    Args:
        file_path: Path to research.md file
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    path = Path(file_path)
    
    if not path.exists():
        raise_on_missing_data(f"research.md not found at {file_path}")
    
    content = path.read_text(encoding='utf-8')
    lines = content.split('\n')
    
    # Check for dynamic search logic
    for i, line in enumerate(lines, 1):
        # Skip comments and empty lines
        if line.strip().startswith('#') or not line.strip():
            continue
        
        # Check for dynamic search patterns
        for pattern in DYNAMIC_SEARCH_PATTERNS:
            if pattern.search(line):
                errors.append(f"Line {i}: Dynamic search logic detected: '{line.strip()}'")
    
    # Check for valid static URLs
    static_urls = []
    for i, line in enumerate(lines, 1):
        # Skip comments and empty lines
        if line.strip().startswith('#') or not line.strip():
            continue
        
        # Extract URLs
        url_matches = re.findall(r'https?://[^\s]+', line)
        for url in url_matches:
            # Clean URL (remove trailing punctuation)
            url = url.rstrip('.,;:')
            
            # Check if it's a valid static source
            is_valid = False
            if OPENML_PATTERN.match(url):
                is_valid = True
                static_urls.append(('OpenML', url))
            elif HUGGINGFACE_PATTERN.match(url):
                is_valid = True
                static_urls.append(('HuggingFace', url))
            elif GITHUB_DATA_PATTERN.match(url):
                is_valid = True
                static_urls.append(('GitHub Data', url))
            elif DOI_PATTERN.match(url):
                is_valid = True
                static_urls.append(('DOI', url))
            
            if not is_valid and url.startswith('http'):
                errors.append(f"Line {i}: Unverified URL format: '{url}'")
    
    # Check for required sections
    required_sections = [
        '## Data Sources',
        '## OpenML Datasets',
        '## HuggingFace Datasets',
        '## Literature Supplements'
    ]
    
    for section in required_sections:
        if section not in content:
            errors.append(f"Missing required section: {section}")
    
    # Check for dataset IDs
    if '## OpenML Datasets' in content:
        openml_section = content.split('## OpenML Datasets')[1].split('## ')[0]
        if not re.search(r'id=\d+', openml_section):
            errors.append("No OpenML dataset IDs found in OpenML Datasets section")
    
    is_valid = len(errors) == 0
    return is_valid, errors

def main():
    """Main entry point for research validation."""
    logger.info("Starting research.md validation...")
    
    # Default path relative to project root
    research_path = Path("research.md")
    
    # Allow override via command line
    if len(sys.argv) > 1:
        research_path = Path(sys.argv[1])
    
    try:
        is_valid, errors = parse_research_md(research_path)
        
        if is_valid:
            logger.info("✓ research.md validation PASSED")
            logger.info("  - All URLs are static and verified")
            logger.info("  - No dynamic search logic detected")
            logger.info("  - All required sections present")
            return 0
        else:
            logger.error("✗ research.md validation FAILED")
            for error in errors:
                logger.error(f"  - {error}")
            return 1
            
    except Exception as e:
        logger.error(f"✗ Validation error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())