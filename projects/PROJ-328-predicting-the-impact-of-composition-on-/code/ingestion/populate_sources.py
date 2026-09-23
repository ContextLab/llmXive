"""
Task T009c: Populate sources.yaml from verified research sources.

Reads the verified research sources (research_verified.md or candidate_sources.txt)
and populates/updates data/config/sources.yaml with specific URLs and API endpoints.
"""
import os
import sys
import logging
import yaml
import re
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger

logger = get_logger(__name__)

# Define paths relative to project root
RESEARCH_VERIFIED_PATH = project_root / "specs" / "001-predict-solder-hardness" / "research_verified.md"
CANDIDATE_SOURCES_PATH = project_root / "data" / "config" / "candidate_sources.txt"
SOURCES_YAML_PATH = project_root / "data" / "config" / "sources.yaml"

def parse_verified_sources(filepath: Path) -> dict:
    """
    Parse the verified research sources file (Markdown or JSON list).

    Args:
        filepath: Path to research_verified.md or candidate_sources.txt

    Returns:
        Dictionary of sources organized by category
    """
    sources = {
        "materials_project": {},
        "nist_uci": {},
        "openalloy": {},
        "literature_pdfs": []
    }

    if not filepath.exists():
        logger.warning(f"Source file not found: {filepath}")
        return sources

    content = filepath.read_text(encoding='utf-8')

    # Try to parse as JSON list first (candidate_sources.txt format)
    if filepath.suffix == '.txt' and content.strip().startswith('['):
        import json
        try:
            data = json.loads(content)
            for item in data:
                url = item.get('url', '')
                source_type = item.get('source_type', '')
                citation = item.get('citation', '')

                if 'materialsproject' in url.lower():
                    sources['materials_project'] = {
                        'name': 'Materials Project',
                        'type': 'api',
                        'url': url,
                        'api_key_env': 'MP_API_KEY',
                        'endpoint': '/materials',
                        'description': 'High-throughput DFT calculations for materials properties',
                        'verified': source_type == 'api'
                    }
                elif 'archive.ics.uci.edu' in url.lower():
                    sources['nist_uci'] = {
                        'name': 'NIST/UCI Repository',
                        'type': 'repository',
                        'url': url,
                        'dataset_id': 'solder_alloys',
                        'description': 'Standardized alloy composition and property datasets',
                        'verified': source_type == 'api'
                    }
                elif 'openalloy' in url.lower():
                    sources['openalloy'] = {
                        'name': 'OpenAlloy Database',
                        'type': 'api',
                        'url': url,
                        'endpoint': '/compositions',
                        'description': 'Open source alloy composition database',
                        'verified': source_type == 'api'
                    }
                elif url.endswith('.pdf') or 'doi.org' in url:
                    sources['literature_pdfs'].append({
                        'name': citation.split(':')[0] if ':' in citation else citation,
                        'url': url,
                        'format': 'pdf',
                        'scraping_method': 'pdfplumber',
                        'verified': source_type == 'pdf',
                        'citation': citation
                    })
        except json.JSONDecodeError:
            logger.warning("Failed to parse as JSON, trying Markdown format")
    else:
        # Parse as Markdown (research_verified.md format)
        # Look for URL patterns in the markdown
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, content)

        for url in urls:
            if 'materialsproject' in url.lower():
                sources['materials_project'] = {
                    'name': 'Materials Project',
                    'type': 'api',
                    'url': url,
                    'api_key_env': 'MP_API_KEY',
                    'endpoint': '/materials',
                    'description': 'High-throughput DFT calculations for materials properties',
                    'verified': True
                }
            elif 'archive.ics.uci.edu' in url.lower():
                sources['nist_uci'] = {
                    'name': 'NIST/UCI Repository',
                    'type': 'repository',
                    'url': url,
                    'dataset_id': 'solder_alloys',
                    'description': 'Standardized alloy composition and property datasets',
                    'verified': True
                }
            elif 'openalloy' in url.lower():
                sources['openalloy'] = {
                    'name': 'OpenAlloy Database',
                    'type': 'api',
                    'url': url,
                    'endpoint': '/compositions',
                    'description': 'Open source alloy composition database',
                    'verified': True
                }
            elif url.endswith('.pdf') or 'doi.org' in url:
                # Extract citation from nearby text if possible
                citation = "Literature Source"
                sources['literature_pdfs'].append({
                    'name': citation,
                    'url': url,
                    'format': 'pdf',
                    'scraping_method': 'pdfplumber',
                    'verified': True,
                    'citation': citation
                })

    # Mark verification status
    verified_count = sum([
        1 if sources['materials_project'].get('verified') else 0,
        1 if sources['nist_uci'].get('verified') else 0,
        1 if sources['openalloy'].get('verified') else 0,
        sum(1 for pdf in sources['literature_pdfs'] if pdf.get('verified'))
    ])

    sources['_verification_status'] = 'verified' if verified_count > 0 else 'provisional'
    sources['_verified_count'] = verified_count

    return sources

def save_sources_yaml(sources: dict, filepath: Path) -> None:
    """
    Save the sources dictionary to a YAML file.

    Args:
        sources: Dictionary of sources
        filepath: Output path for sources.yaml
    """
    # Ensure directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        yaml.dump(sources, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    logger.info(f"Saved sources to {filepath}")

def main():
    """Main entry point for T009c."""
    logger.info("Starting T009c: Populate sources.yaml")

    # Determine which source file to use
    source_file = RESEARCH_VERIFIED_PATH if RESEARCH_VERIFIED_PATH.exists() else CANDIDATE_SOURCES_PATH

    if not source_file.exists():
        logger.error(f"No source file found: {RESEARCH_VERIFIED_PATH} or {CANDIDATE_SOURCES_PATH}")
        sys.exit(1)

    logger.info(f"Parsing sources from: {source_file}")
    sources = parse_verified_sources(source_file)

    # Save to sources.yaml
    save_sources_yaml(sources, SOURCES_YAML_PATH)

    # Report summary
    verified_count = sources.get('_verified_count', 0)
    logger.info(f"Populated sources.yaml with {verified_count} verified sources")

    if verified_count == 0:
        logger.warning("No verified sources found. Check research_verified.md or candidate_sources.txt")

    logger.info("T009c completed successfully")

if __name__ == "__main__":
    main()
