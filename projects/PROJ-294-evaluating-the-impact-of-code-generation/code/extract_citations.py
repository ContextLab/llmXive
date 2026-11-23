"""
Citation Extraction Module

Scans project documentation (spec.md, plan.md, research.md) for citations
and creates a structured YAML file at state/citations.yaml.
"""
import os
import re
import sys
import logging
import yaml
from typing import List, Dict, Optional, Tuple
from utils import setup_logging, get_logger, set_task_id, get_timestamp

# Configuration
DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
SPECS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "specs")
STATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "state")
OUTPUT_FILE = os.path.join(STATE_DIR, "citations.yaml")

# Target files to scan
TARGET_FILES = [
    "spec.md",
    "plan.md",
    "research.md"
]

# Regex patterns for common citation formats
# Matches formats like: [1], (Author, Year), [URL], or markdown links [Title](URL)
PATTERNS = [
    # Markdown links: [Title](URL)
    r'\[([^\]]+)\]\((https?://[^\s\)]+)\)',
    # Inline URLs: http(s)://...
    r'(https?://[^\s\)<>\[\]"]+)',
    # Bracketed references: [1], [2]
    r'\[(\d+)\]',
    # Parenthetical citations: (Author, Year) - simplified
    r'\(([A-Za-z]+(?:\s+[A-Za-z]+)*),\s*(\d{4})\)'
]

def ensure_state_dir():
    """Ensure the state directory exists."""
    if not os.path.exists(STATE_DIR):
        os.makedirs(STATE_DIR)
        logging.info(f"Created state directory: {STATE_DIR}")

def scan_file_for_citations(filepath: str, logger: logging.Logger) -> List[Dict]:
    """
    Scan a single file for citations and extract structured data.
    
    Args:
        filepath: Path to the file to scan
        logger: Logger instance
        
    Returns:
        List of dictionaries containing citation data
    """
    citations = []
    if not os.path.exists(filepath):
        logger.warning(f"File not found: {filepath}")
        return citations

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Error reading file {filepath}: {e}")
        return citations

    source_name = os.path.basename(filepath)

    # Track found URLs to avoid duplicates within this file
    found_urls = set()

    for pattern in PATTERNS:
        matches = re.finditer(pattern, content)
        for match in matches:
            try:
                if "http" in match.group(0):
                    # Extract URL and title
                    if match.group(0).startswith('['):
                        # Markdown link format
                        title = match.group(1)
                        url = match.group(2)
                    else:
                        # Inline URL
                        title = match.group(0)
                        url = match.group(0)
                    
                    if url not in found_urls:
                        found_urls.add(url)
                        citations.append({
                            "source_file": source_name,
                            "type": "url",
                            "url": url,
                            "title": title,
                            "context": match.group(0)
                        })
                elif match.group(0).startswith('[') and match.group(0).endswith(']'):
                    # Numeric reference [1]
                    citations.append({
                        "source_file": source_name,
                        "type": "numeric_reference",
                        "reference_id": match.group(1),
                        "context": match.group(0)
                    })
                elif match.group(0).startswith('('):
                    # Parenthetical citation
                    citations.append({
                        "source_file": source_name,
                        "type": "parenthetical",
                        "author": match.group(1),
                        "year": match.group(2),
                        "context": match.group(0)
                    })
            except Exception as e:
                logger.warning(f"Error processing match in {filepath}: {e}")
                continue

    return citations

def extract_citations(logger: logging.Logger) -> List[Dict]:
    """
    Extract citations from all target documentation files.
    
    Args:
        logger: Logger instance
        
    Returns:
        List of all extracted citations
    """
    all_citations = []
    
    # Search in docs directory first, then specs, then root
    search_dirs = [DOCS_DIR, SPECS_DIR, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
    
    for target_file in TARGET_FILES:
        found = False
        for search_dir in search_dirs:
            if not search_dir or not os.path.exists(search_dir):
                continue
                
            filepath = os.path.join(search_dir, target_file)
            if os.path.exists(filepath):
                logger.info(f"Scanning {filepath} for citations")
                citations = scan_file_for_citations(filepath, logger)
                all_citations.extend(citations)
                found = True
                break
        
        if not found:
            logger.warning(f"Target file {target_file} not found in any search directory")

    return all_citations

def save_citations(citations: List[Dict], logger: logging.Logger) -> bool:
    """
    Save extracted citations to state/citations.yaml.
    
    Args:
        citations: List of citation dictionaries
        logger: Logger instance
        
    Returns:
        True if successful, False otherwise
    """
    ensure_state_dir()
    
    try:
        # Create a structured output
        output_data = {
            "metadata": {
                "generated_at": get_timestamp(),
                "task_id": get_task_id(),
                "source_files_scanned": TARGET_FILES,
                "total_citations_found": len(citations)
            },
            "citations": citations
        }
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(output_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
        logger.info(f"Successfully saved {len(citations)} citations to {OUTPUT_FILE}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save citations: {e}")
        return False

def main():
    """Main entry point for citation extraction."""
    task_id = "T006a"
    set_task_id(task_id)
    logger = setup_logging(task_id)
    
    logger.info(f"Starting citation extraction task: {task_id}")
    logger.info(f"Searching for citations in: {', '.join(TARGET_FILES)}")
    
    try:
        citations = extract_citations(logger)
        
        if not citations:
            logger.warning("No citations found in scanned files")
            # Still create the file with empty list
            success = save_citations([], logger)
        else:
            success = save_citations(citations, logger)
        
        if success:
            logger.info(f"Citation extraction completed successfully. Output: {OUTPUT_FILE}")
            sys.exit(0)
        else:
            logger.error("Citation extraction failed to save output")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Unexpected error during citation extraction: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()