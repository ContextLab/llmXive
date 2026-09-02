"""
Populate data/config/sources.yaml from specs/001-predict-solder-hardness/research_verified.md.

This task (T009c) reads the verified research sources generated in T008b
and populates the sources.yaml configuration file with specific, verified
URLs and API endpoints.

CRITICAL: This task MUST run after T008b. If research_verified.md is missing
or contains no verified sources, this script will raise a ConfigurationError.
"""

import os
import sys
import logging
import yaml
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.error_handlers import ConfigurationError
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Paths
RESEARCH_VERIFIED_PATH = project_root / "specs" / "001-predict-solder-hardness" / "research_verified.md"
SOURCES_YAML_PATH = project_root / "data" / "config" / "sources.yaml"


def parse_verified_sources(filepath: Path) -> Dict[str, Any]:
    """
    Parse research_verified.md to extract verified URLs and API endpoints.

    Expected format in research_verified.md:
    - Sections with headers like "## Materials Project"
    - Lines containing URLs (http/https) and optionally API info
    - Citation blocks with DOI links

    Returns a structured dict suitable for YAML serialization.
    """
    if not filepath.exists():
        raise ConfigurationError(f"Verified research file not found: {filepath}")

    sources = {
        "materials_project": {
            "name": "Materials Project",
            "type": "api",
            "url": None,
            "api_key_env": "MP_API_KEY",
            "endpoint": "/materials",
            "description": "High-throughput DFT calculations for materials properties",
            "verified": False
        },
        "nist_uci": {
            "name": "NIST/UCI Repository",
            "type": "repository",
            "url": None,
            "dataset_id": "solder_alloys",
            "description": "Standardized alloy composition and property datasets",
            "verified": False
        },
        "openalloy": {
            "name": "OpenAlloy Database",
            "type": "api",
            "url": None,
            "endpoint": "/compositions",
            "description": "Open source alloy composition database",
            "verified": False
        },
        "literature_pdfs": []
    }

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract URLs using regex
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    all_urls = re.findall(url_pattern, content)

    logger.info(f"Found {len(all_urls)} URLs in research_verified.md")

    # Categorize URLs
    for url in all_urls:
        # Check for Materials Project
        if 'materialsproject.org' in url or 'mp-api' in url:
            sources["materials_project"]["url"] = url
            sources["materials_project"]["verified"] = True
            logger.info(f"Verified Materials Project URL: {url}")

        # Check for NIST/UCI
        elif 'archive.ics.uci.edu' in url or 'nist.gov' in url:
            sources["nist_uci"]["url"] = url
            sources["nist_uci"]["verified"] = True
            logger.info(f"Verified NIST/UCI URL: {url}")

        # Check for OpenAlloy
        elif 'openalloy' in url.lower():
            sources["openalloy"]["url"] = url
            sources["openalloy"]["verified"] = True
            logger.info(f"Verified OpenAlloy URL: {url}")

        # Check for PDF/DOI links (literature)
        elif ('doi.org' in url or '.pdf' in url or 'jallcom' in url or 
              'journalofalloys' in url or 'solder' in url.lower()):
            # Extract DOI if present
            doi_match = re.search(r'doi\.org/10\.[0-9]+/[^\s]+', url)
            if doi_match:
                doi_url = doi_match.group(0)
            else:
                doi_url = url

            # Extract title from context if possible
            title = "Literature Source"
            # Try to find a title near the URL (simplified approach)
            for line in content.split('\n'):
                if url in line and not line.strip().startswith('#'):
                    # Clean up the line to get a potential title
                    clean_line = re.sub(r'https?://[^\s]+', '', line).strip()
                    if clean_line and len(clean_line) < 100:
                        title = clean_line
                        break

            pdf_entry = {
                "name": title,
                "url": doi_url,
                "format": "pdf",
                "scraping_method": "pdfplumber",
                "verified": True
            }
            sources["literature_pdfs"].append(pdf_entry)
            logger.info(f"Added literature source: {title} -> {doi_url}")

    # Validate that at least one source was verified
    has_verified = (
        sources["materials_project"]["verified"] or
        sources["nist_uci"]["verified"] or
        sources["openalloy"]["verified"] or
        len(sources["literature_pdfs"]) > 0
    )

    if not has_verified:
        raise ConfigurationError(
            "No verified sources found in research_verified.md. "
            "Ensure T008b has successfully verified at least one source."
        )

    return sources


def save_sources_yaml(sources: Dict[str, Any], filepath: Path) -> None:
    """
    Save the sources dictionary to a YAML file.
    """
    # Ensure directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        # Add header comment
        f.write("# Verified data sources for solder hardness dataset\n")
        f.write("# Populated from research_verified.md (T008b)\n")
        f.write("# Generated by: code/ingestion/populate_sources.py (T009c)\n")
        f.write("#\n")
        f.write(f"# Generated at: {sources.get('_generated_at', 'N/A')}\n")
        f.write("#\n\n")

        # Remove internal metadata before dumping
        sources_to_dump = {k: v for k, v in sources.items() if k != '_generated_at'}

        yaml.dump(
            sources_to_dump,
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            indent=2
        )

    logger.info(f"Successfully saved sources.yaml to {filepath}")


def main() -> int:
    """
    Main entry point for populating sources.yaml.
    """
    logger.info("Starting T009c: Populate sources.yaml from research_verified.md")

    try:
        # Parse verified sources
        sources = parse_verified_sources(RESEARCH_VERIFIED_PATH)

        # Add generation metadata
        from datetime import datetime
        sources['_generated_at'] = datetime.utcnow().isoformat()

        # Save to YAML
        save_sources_yaml(sources, SOURCES_YAML_PATH)

        # Summary
        verified_count = sum([
            1 if sources["materials_project"]["verified"] else 0,
            1 if sources["nist_uci"]["verified"] else 0,
            1 if sources["openalloy"]["verified"] else 0,
            len(sources["literature_pdfs"])
        ])

        logger.info(f"T009c completed successfully. Verified {verified_count} sources.")
        logger.info(f"Output: {SOURCES_YAML_PATH}")

        return 0

    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during T009c: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
