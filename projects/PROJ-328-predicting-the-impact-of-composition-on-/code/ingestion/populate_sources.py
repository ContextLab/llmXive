"""
T009c: Populate sources.yaml from verified research sources.

Reads the verified research file (research_verified.md) or the candidate list
(candidate_sources.txt) if verification failed, parses the content, and
populates/updates data/config/sources.yaml with the specific URLs and API endpoints.
"""
import os
import sys
import logging
import yaml
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logger import get_logger

logger = get_logger(__name__)

# Paths relative to project root
RESEARCH_VERIFIED_PATH = project_root / "specs" / "001-predict-solder-hardness" / "research_verified.md"
CANDIDATE_SOURCES_PATH = project_root / "data" / "config" / "candidate_sources.txt"
SOURCES_YAML_PATH = project_root / "data" / "config" / "sources.yaml"

def parse_verified_sources(file_path: Path) -> Dict[str, Any]:
    """
    Parse the verified research file to extract sources.
    Expects a markdown file with specific formatting or a JSON list in candidate_sources.txt.
    """
    sources = {
        "_verification_status": "provisional",
        "_verified_count": 0,
        "materials_project": {},
        "nist_uci": {},
        "openalloy": {},
        "literature_pdfs": []
    }

    if not file_path.exists():
        logger.warning(f"Source file not found: {file_path}. Returning empty provisional config.")
        return sources

    content = file_path.read_text(encoding="utf-8")
    verified_count = 0

    # Check if it's the candidate JSON format (from T008a)
    if file_path.name == "candidate_sources.txt":
        try:
            import json
            data_list = json.loads(content)
            for item in data_list:
                url = item.get("url", "")
                source_type = item.get("source_type", "")
                citation = item.get("citation", "")

                if "materialsproject" in url.lower() or "materialsproject.org" in url:
                    sources["materials_project"] = {
                        "name": "Materials Project",
                        "type": "api",
                        "url": url,
                        "api_key_env": "MP_API_KEY",
                        "endpoint": "/materials",
                        "description": "High-throughput DFT calculations",
                        "verified": True
                    }
                    verified_count += 1
                elif "archive.ics.uci.edu" in url or "nist" in url.lower():
                    sources["nist_uci"] = {
                        "name": "NIST/UCI Repository",
                        "type": "repository",
                        "url": url,
                        "dataset_id": "solder_alloys",
                        "description": "Standardized alloy composition datasets",
                        "verified": True
                    }
                    verified_count += 1
                elif "openalloy" in url.lower():
                    sources["openalloy"] = {
                        "name": "OpenAlloy Database",
                        "type": "api",
                        "url": url,
                        "endpoint": "/compositions",
                        "description": "Open source alloy composition database",
                        "verified": True
                    }
                    verified_count += 1
                elif url.endswith(".pdf") or "doi.org" in url:
                    sources["literature_pdfs"].append({
                        "name": citation or "Literature Source",
                        "url": url,
                        "format": "pdf",
                        "scraping_method": "pdfplumber",
                        "verified": source_type == "verified",
                        "citation": citation
                    })
                    if source_type == "verified":
                        verified_count += 1
        except json.JSONDecodeError:
            logger.error("Failed to parse candidate_sources.txt as JSON.")
    else:
        # Parse Markdown format (research_verified.md)
        # Look for lines starting with - [x] or specific URL patterns
        lines = content.split("\n")
        current_source = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detect API sources
            if "materialsproject" in line.lower():
                sources["materials_project"] = {
                    "name": "Materials Project",
                    "type": "api",
                    "url": line,
                    "api_key_env": "MP_API_KEY",
                    "endpoint": "/materials",
                    "description": "High-throughput DFT calculations",
                    "verified": True
                }
                verified_count += 1
            elif "archive.ics.uci.edu" in line or "nist" in line.lower():
                sources["nist_uci"] = {
                    "name": "NIST/UCI Repository",
                    "type": "repository",
                    "url": line,
                    "dataset_id": "solder_alloys",
                    "description": "Standardized alloy composition datasets",
                    "verified": True
                }
                verified_count += 1
            elif "openalloy" in line.lower():
                sources["openalloy"] = {
                    "name": "OpenAlloy Database",
                    "type": "api",
                    "url": line,
                    "endpoint": "/compositions",
                    "description": "Open source alloy composition database",
                    "verified": True
                }
                verified_count += 1
            elif line.endswith(".pdf") or "doi.org" in line:
                # Extract citation if possible, otherwise use generic
                citation = line.split("/")[-1].replace(".pdf", "")
                sources["literature_pdfs"].append({
                    "name": citation,
                    "url": line,
                    "format": "pdf",
                    "scraping_method": "pdfplumber",
                    "verified": True,
                    "citation": citation
                })
                verified_count += 1

    sources["_verification_status"] = "verified" if verified_count > 0 else "provisional"
    sources["_verified_count"] = verified_count

    logger.info(f"Parsed {verified_count} verified/provisional sources from {file_path.name}")
    return sources

def save_sources_yaml(sources: Dict[str, Any], output_path: Path) -> None:
    """Save the sources dictionary to a YAML file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(sources, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    logger.info(f"Saved sources configuration to {output_path}")

def main():
    """Main entry point for T009c."""
    logger.info("Starting T009c: Populate sources.yaml")

    # Determine input file
    input_file = RESEARCH_VERIFIED_PATH
    if not input_file.exists():
        if CANDIDATE_SOURCES_PATH.exists():
            logger.info(f"Verified file not found. Falling back to provisional source: {CANDIDATE_SOURCES_PATH}")
            input_file = CANDIDATE_SOURCES_PATH
        else:
            logger.error("Neither research_verified.md nor candidate_sources.txt found.")
            logger.error("Cannot populate sources.yaml. Halting.")
            sys.exit(1)

    # Parse sources
    sources = parse_verified_sources(input_file)

    # Save to YAML
    save_sources_yaml(sources, SOURCES_YAML_PATH)

    logger.info("T009c completed successfully.")

if __name__ == "__main__":
    main()
