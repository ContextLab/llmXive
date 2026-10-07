"""
T009c: Populate sources.yaml from verified research_verified.md.

Reads the verified sources list from specs/001-predict-solder-hardness/research_verified.md
and populates/updates data/config/sources.yaml with the specific, verified URLs and API endpoints.

This task MUST run after T008b. If T008b failed (halted), this task is skipped.
"""
import os
import sys
import logging
import yaml
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logger import get_logger

logger = get_logger(__name__)

RESEARCH_VERIFIED_PATH = project_root / "specs" / "001-predict-solder-hardness" / "research_verified.md"
SOURCES_YAML_PATH = project_root / "data" / "config" / "sources.yaml"

# Regex patterns to extract source info from markdown
# Matches lines like: "- [URL] (verified) Citation: ..." or "- [URL] Citation: ..."
SOURCE_PATTERN = re.compile(
    r'^[-*]\s*\[([^\]]+)\]\s*\(([^)]+)\)\s*Citation:\s*(.+)$',
    re.IGNORECASE
)
# Alternative pattern for lines like: "- URL Citation: ..."
ALT_SOURCE_PATTERN = re.compile(
    r'^[-*]\s*(https?://[^\s]+)\s+Citation:\s*(.+)$',
    re.IGNORECASE
)
# Pattern for lines with just URL and no citation marker
URL_ONLY_PATTERN = re.compile(
    r'^[-*]\s*(https?://[^\s]+)\s*$',
    re.IGNORECASE
)

def parse_verified_sources(file_path: Path) -> List[Dict[str, Any]]:
    """
    Parse the research_verified.md file to extract verified sources.
    
    Args:
        file_path: Path to the research_verified.md file
        
    Returns:
        List of dictionaries containing source information
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Verified sources file not found: {file_path}")
    
    verified_sources = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        # Try primary pattern
        match = SOURCE_PATTERN.match(line)
        if match:
            url, status, citation = match.groups()
            if status.lower() == 'verified':
                verified_sources.append({
                    'url': url.strip(),
                    'status': 'verified',
                    'citation': citation.strip()
                })
            continue
            
        # Try alternative pattern
        match = ALT_SOURCE_PATTERN.match(line)
        if match:
            url, citation = match.groups()
            verified_sources.append({
                'url': url.strip(),
                'status': 'verified',
                'citation': citation.strip()
            })
            continue
            
        # Try URL-only pattern
        match = URL_ONLY_PATTERN.match(line)
        if match:
            url = match.group(1)
            # Determine if it's an API or PDF based on domain/path
            source_type = 'api' if 'api' in url.lower() or 'materialsproject' in url.lower() else 'pdf'
            verified_sources.append({
                'url': url,
                'status': 'verified',
                'citation': 'Auto-detected',
                'source_type': source_type
            })
            continue
            
    if not verified_sources:
        logger.warning("No verified sources found in the research_verified.md file.")
        
    return verified_sources

def save_sources_yaml(sources: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save the verified sources to a YAML file.
    
    Args:
        sources: List of source dictionaries
        output_path: Path to the output YAML file
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing data if file exists to preserve structure
    existing_data = {}
    if output_path.exists():
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                existing_data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            logger.warning(f"Could not parse existing YAML file: {e}. Starting fresh.")
    
    # Update verification metadata
    existing_data['_verification_status'] = 'verified'
    existing_data['_verified_count'] = len(sources)
    existing_data['_last_updated'] = '2024-01-01T00:00:00Z'  # Placeholder, could use datetime
    
    # Categorize sources
    api_sources = {}
    pdf_sources = []
    
    for i, source in enumerate(sources):
        url = source['url']
        citation = source.get('citation', 'Unknown')
        
        # Determine source type
        if 'api' in source.get('source_type', '').lower() or 'materialsproject' in url.lower() or 'openalloy' in url.lower():
            key = f"source_{i+1}"
            api_sources[key] = {
                'name': citation.split(':')[0] if ':' in citation else f"Source {i+1}",
                'type': 'api',
                'url': url,
                'verified': True,
                'citation': citation
            }
            # Add API key env var for known APIs
            if 'materialsproject' in url.lower():
                api_sources[key]['api_key_env'] = 'MP_API_KEY'
                api_sources[key]['endpoint'] = '/materials'
            elif 'openalloy' in url.lower():
                api_sources[key]['api_key_env'] = 'OPENALLOY_API_KEY'
                api_sources[key]['endpoint'] = '/compositions'
        else:
            # Assume PDF for literature sources
            pdf_sources.append({
                'name': citation.split(':')[0] if ':' in citation else f"Source {i+1}",
                'url': url,
                'format': 'pdf',
                'scraping_method': 'pdfplumber',
                'verified': True,
                'citation': citation
            })
    
    # Update existing data with new sources
    if api_sources:
        existing_data['api_sources'] = api_sources
    if pdf_sources:
        existing_data['literature_pdfs'] = pdf_sources
        
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(existing_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    logger.info(f"Saved {len(sources)} verified sources to {output_path}")

def main() -> int:
    """
    Main entry point for the task.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    logger.info("Starting T009c: Populate sources.yaml from verified sources")
    
    try:
        # Check if verified sources file exists
        if not RESEARCH_VERIFIED_PATH.exists():
            logger.error(f"Verified sources file not found: {RESEARCH_VERIFIED_PATH}")
            logger.error("T008b may have failed or not been run. Skipping T009c.")
            return 1
        
        # Parse verified sources
        logger.info(f"Parsing verified sources from {RESEARCH_VERIFIED_PATH}")
        verified_sources = parse_verified_sources(RESEARCH_VERIFIED_PATH)
        
        if not verified_sources:
            logger.warning("No verified sources found. Creating empty sources.yaml with verification status.")
            # Still create the file to indicate verification was attempted
            save_sources_yaml([], SOURCES_YAML_PATH)
            return 0
        
        # Save to YAML
        logger.info(f"Saving {len(verified_sources)} verified sources to {SOURCES_YAML_PATH}")
        save_sources_yaml(verified_sources, SOURCES_YAML_PATH)
        
        logger.info("T009c completed successfully")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during T009c: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == '__main__':
    sys.exit(main())
