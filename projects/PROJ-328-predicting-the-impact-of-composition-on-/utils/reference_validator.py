"""
Reference Validator utilities for Constitution Principle II compliance.

Implements validation logic for research sources including:
- Citation title overlap threshold (CITATION_TITLE_OVERLAP_THRESHOLD = 0.7)
- URL format validation
- Source type verification
"""

import re
from typing import Dict, Any, List, Optional
from difflib import SequenceMatcher

# Constitution Principle II defaults
CITATION_TITLE_OVERLAP_THRESHOLD = 0.7

class ConstitutionError(Exception):
    """Exception raised for Constitution Principle II violations."""
    pass

def calculate_title_overlap(title1: str, title2: str) -> float:
    """
    Calculate the overlap ratio between two titles.
    
    Uses SequenceMatcher to determine similarity ratio.
    
    Args:
        title1: First title string
        title2: Second title string
        
    Returns:
        Float between 0.0 and 1.0 representing similarity
    """
    if not title1 or not title2:
        return 0.0
    
    # Normalize: lowercase and remove extra whitespace
    t1 = ' '.join(title1.lower().split())
    t2 = ' '.join(title2.lower().split())
    
    return SequenceMatcher(None, t1, t2).ratio()

def validate_citation_uniqueness(
    new_citation: str, 
    existing_citations: List[str]
) -> bool:
    """
    Validate that a new citation doesn't duplicate an existing one.
    
    Uses CITATION_TITLE_OVERLAP_THRESHOLD to determine duplicates.
    
    Args:
        new_citation: The new citation string to validate
        existing_citations: List of existing citation strings
        
    Returns:
        True if citation is unique, False if it overlaps with existing
        
    Raises:
        ConstitutionError: If citation overlaps with existing above threshold
    """
    for existing in existing_citations:
        overlap = calculate_title_overlap(new_citation, existing)
        if overlap >= CITATION_TITLE_OVERLAP_THRESHOLD:
            raise ConstitutionError(
                f"Citation '{new_citation}' overlaps with '{existing}' "
                f"(overlap: {overlap:.2f} >= {CITATION_TITLE_OVERLAP_THRESHOLD})"
            )
    
    return True

def validate_url_format(url: str) -> bool:
    """
    Validate that a URL has a valid format.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not url:
        return False
    
    # Basic URL pattern
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url))

def validate_research_md(
    research_md_path: str,
    existing_sources: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Validate a research.md file against Constitution Principle II.
    
    Args:
        research_md_path: Path to the research.md file
        existing_sources: Optional list of existing source dictionaries
        
    Returns:
        Dict with validation results:
        - 'valid': bool
        - 'errors': list of error messages
        - 'warnings': list of warning messages
        - 'duplicate_count': int
    """
    import os
    
    results = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'duplicate_count': 0
    }
    
    if not os.path.exists(research_md_path):
        results['valid'] = False
        results['errors'].append(f"File not found: {research_md_path}")
        return results
    
    with open(research_md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract citations from markdown
    # Look for patterns like "- **Citation**:" or numbered lists
    citation_pattern = r'[-*]\s+\*\*(.+?)\*\*|^\d+\.\s+(.+)'
    citations = re.findall(citation_pattern, content, re.MULTILINE)
    
    # Flatten and clean citations
    citation_list = []
    for match in citations:
        for group in match:
            if group:
                citation_list.append(group.strip())
    
    # Check for duplicates
    if existing_sources:
        existing_citations = [src.get('citation', '') for src in existing_sources if src.get('citation')]
        
        for citation in citation_list:
            try:
                validate_citation_uniqueness(citation, existing_citations)
            except ConstitutionError as e:
                results['errors'].append(str(e))
                results['duplicate_count'] += 1
                results['valid'] = False
    
    # Validate URLs in the document
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    urls = re.findall(url_pattern, content)
    
    for url in urls:
        if not validate_url_format(url):
            results['warnings'].append(f"Potentially invalid URL format: {url}")
    
    return results

def validate_source_completeness(source: Dict[str, Any]) -> List[str]:
    """
    Validate that a source dictionary has all required fields.
    
    Args:
        source: Source dictionary to validate
        
    Returns:
        List of missing field names
    """
    required_fields = ['url', 'source_type', 'citation']
    missing = []
    
    for field in required_fields:
        if field not in source or not source[field]:
            missing.append(field)
    
    return missing
