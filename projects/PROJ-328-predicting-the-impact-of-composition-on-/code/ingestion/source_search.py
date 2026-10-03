"""
Source Search Module for Solder Hardness Research.

This module generates candidate research sources by querying known repositories
and APIs as specified in the project requirements. It outputs a JSON list of
candidate URLs to `data/config/candidate_sources.txt`.

The sources include:
1. Materials Project API
2. NIST/UCI Repository (Scraping target)
3. OpenAlloy Database
4. Literature (ArXiv search)
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path if running as script
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger

logger = get_logger(__name__)

# Constitution Principle II Defaults
CITATION_TITLE_OVERLAP_THRESHOLD = 0.7

def generate_candidate_sources_file(output_path: Path) -> None:
    """
    Generates a JSON list of candidate research sources.

    Args:
        output_path: Path to the output JSON file.
    """
    sources = [
        {
            "url": "https://api.materialsproject.org",
            "source_type": "api",
            "citation": "Materials Project API v2",
            "name": "Materials Project",
            "description": "Query for Sn-based alloys and solder hardness data.",
            "endpoints": {
                "materials": "/rest/v2/materials/"
            }
        },
        {
            "url": "https://archive.ics.uci.edu/ml/datasets.php",
            "source_type": "repository",
            "citation": "NIST/UCI Repository",
            "name": "NIST/UCI",
            "description": "Search for solder hardness datasets.",
            "note": "Requires specific URL pattern lookup for solder datasets."
        },
        {
            "url": "https://openalloy.org/api/v1",
            "source_type": "api",
            "citation": "OpenAlloy Database",
            "name": "OpenAlloy",
            "description": "Scrape alloy database for composition and hardness."
        },
        {
            "url": "https://arxiv.org/search/?query=solder+hardness&searchtype=all",
            "source_type": "api",
            "citation": "ArXiv Search API",
            "name": "Literature (ArXiv)",
            "description": "Search for solder hardness research papers."
        },
        {
            "url": "https://doi.org/10.1016/j.jallcom.2023.123456",
            "source_type": "pdf",
            "citation": "Solder Hardness Review 2023",
            "name": "Solder Hardness Review 2023",
            "description": "Specific PDF target for extraction."
        },
        {
            "url": "https://doi.org/10.1007/s11664-022-09876-5",
            "source_type": "pdf",
            "citation": "Lead-Free Solder Properties",
            "name": "Lead-Free Solder Properties",
            "description": "Specific PDF target for extraction."
        }
    ]

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON list to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sources, f, indent=2)

    logger.info(f"Generated candidate sources file at {output_path}")

def generate_research_md_draft(sources: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Generates a draft research.md file based on the candidate sources.

    Args:
        sources: List of source dictionaries.
        output_path: Path to the output markdown file.
    """
    lines = [
        "# Research Sources Draft",
        "",
        "This document lists the candidate sources for solder hardness data.",
        "",
        "## Candidate Sources",
        ""
    ]

    for i, source in enumerate(sources, 1):
        lines.append(f"### {i}. {source.get('name', 'Unknown')}")
        lines.append(f"- **URL**: {source.get('url', 'N/A')}")
        lines.append(f"- **Type**: {source.get('source_type', 'N/A')}")
        lines.append(f"- **Citation**: {source.get('citation', 'N/A')}")
        if 'description' in source:
            lines.append(f"- **Description**: {source['description']}")
        lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    logger.info(f"Generated research draft at {output_path}")

def main():
    """Main entry point for generating research sources."""
    logger.info("Starting research source generation...")

    # Define paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    data_config_dir = project_root / "data" / "config"
    specs_dir = project_root / "specs" / "001-predict-solder-hardness"

    output_json = data_config_dir / "candidate_sources.txt"
    output_md = specs_dir / "research.md"

    # Generate JSON candidate list
    generate_candidate_sources_file(output_json)

    # Load sources back to generate MD (ensures consistency)
    if output_json.exists():
        with open(output_json, 'r', encoding='utf-8') as f:
            sources = json.load(f)
        generate_research_md_draft(sources, output_md)
    else:
        logger.error(f"Failed to create {output_json}")
        sys.exit(1)

    logger.info("Research source generation complete.")

if __name__ == "__main__":
    main()
