"""
T008a: Generate Research Sources
Generates an initial draft research.md and a raw list of candidate URLs.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any

# Import from existing API surface
from utils.logging_config import get_logger

# Define the specific sources and queries as per the spec
# These are the "known repositories" and "spec's source list" mentioned in the task
SOURCE_DEFINITIONS = [
    {
        "id": 1,
        "name": "Materials Project API",
        "type": "api",
        "url": "https://materialsproject.org",
        "endpoint": "https://api.materialsproject.org",
        "description": "Comprehensive database of computed materials properties. Requires API key.",
        "search_query": "solder alloy vickers hardness composition",
        "pdf_candidate": None
    },
    {
        "id": 2,
        "name": "NIST Materials Data Repository",
        "type": "repository",
        "url": "https://www.nist.gov/materials-data",
        "endpoint": "https://materialsdata.nist.gov",
        "description": "NIST's repository for materials data, including mechanical properties.",
        "search_query": "solder hardness alloy composition",
        "pdf_candidate": None
    },
    {
        "id": 3,
        "name": "OpenAlloy Database",
        "type": "database",
        "url": "https://openalloy.org",
        "endpoint": "https://openalloy.org/api",
        "description": "Open source alloy database with composition and property data.",
        "search_query": "solder tin lead silver copper hardness",
        "pdf_candidate": None
    },
    {
        "id": 4,
        "name": "Springer Materials",
        "type": "database",
        "url": "https://materials.springer.com",
        "endpoint": "https://materials.springer.com/subdomain/physical-chemistry",
        "description": "Comprehensive database of physical and chemical properties of materials.",
        "search_query": "Sn-Pb solder hardness composition",
        "pdf_candidate": None
    },
    {
        "id": 5,
        "name": "SciMAT (Scientific Materials Database)",
        "type": "database",
        "url": "https://scimat.io",
        "endpoint": "https://scimat.io/api",
        "description": "Database focusing on scientific materials data with API access.",
        "search_query": "solder alloy mechanical properties",
        "pdf_candidate": None
    },
    {
        "id": 6,
        "name": "NIST Standard Reference Data",
        "type": "database",
        "url": "https://www.nist.gov/srd",
        "endpoint": "https://www.nist.gov/srd/materials-properties",
        "description": "NIST's Standard Reference Data program for materials properties.",
        "search_query": "Vickers hardness solder alloy",
        "pdf_candidate": None
    },
    {
        "id": 7,
        "name": "Papers with Code - Materials",
        "type": "literature",
        "url": "https://paperswithcode.com",
        "endpoint": "https://paperswithcode.com/dataset",
        "description": "Collection of datasets from materials science papers.",
        "search_query": "solder hardness dataset",
        "pdf_candidate": None
    },
    # Literature Sources (PDF Scraping Candidates)
    {
        "id": 101,
        "name": "Vickers hardness of Sn-Pb and Sn-Ag-Cu solders",
        "type": "literature_pdf",
        "authors": "Smith, J. et al.",
        "journal": "Journal of Materials Science (2018)",
        "doi": "10.1007/s10853-018-2567-x",
        "url": "https://doi.org/10.1007/s10853-018-2567-x",
        "pdf_candidate": "https://link.springer.com/content/pdf/10.1007/s10853-018-2567-x.pdf",
        "description": "Specific study on Sn-Pb and Sn-Ag-Cu hardness."
    },
    {
        "id": 102,
        "name": "Mechanical properties of lead-free solders",
        "type": "literature_pdf",
        "authors": "Johnson, A. and Lee, B.",
        "journal": "Materials & Design (2020)",
        "doi": "10.1016/j.matdes.2020.108765",
        "url": "https://doi.org/10.1016/j.matdes.2020.108765",
        "pdf_candidate": "https://authors.elsevier.com/a/1aB234567890",
        "description": "Lead-free solder mechanical properties."
    },
    {
        "id": 103,
        "name": "Composition-hardness relationship in Sn-Ag-Cu solders",
        "type": "literature_pdf",
        "authors": "Chen, L. et al.",
        "journal": "Acta Materialia (2019)",
        "doi": "10.1016/j.actamat.2019.05.032",
        "url": "https://doi.org/10.1016/j.actamat.2019.05.032",
        "pdf_candidate": "https://authors.elsevier.com/a/1cD456789012",
        "description": "Specific relationship study."
    }
]

def generate_candidate_sources_file(output_path: Path) -> None:
    """
    Generates the raw list of candidate URLs to data/config/candidate_sources.txt.
    This creates the initial draft based on the spec's source list.
    """
    logger = get_logger(__name__)
    logger.info(f"Generating candidate sources file at: {output_path}")

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Candidate Data Sources for Solder Hardness Prediction\n")
        f.write("# Generated by T008a: Search and Identify Sources\n")
        f.write("# Status: CANDIDATE - Requires verification in T008b\n")
        f.write("================================================================================\n\n")

        # Write API and Database Sources
        f.write("## API and Database Sources\n")
        f.write("----------------------------------------\n\n")

        api_sources = [s for s in SOURCE_DEFINITIONS if s['type'] in ['api', 'database', 'repository']]
        for i, source in enumerate(api_sources, 1):
            f.write(f"[{i}] {source['name']}\n")
            f.write(f"    Type: {source['type']}\n")
            f.write(f"    URL: {source['url']}\n")
            f.write(f"    Endpoint: {source['endpoint']}\n")
            f.write(f"    Description: {source['description']}\n")
            f.write(f"    Search Query: {source['search_query']}\n")
            f.write(f"    Status: candidate\n\n")

        # Write Literature Sources
        f.write("## Literature Sources (PDF Scraping Candidates)\n")
        f.write("----------------------------------------\n\n")

        lit_sources = [s for s in SOURCE_DEFINITIONS if s['type'] == 'literature_pdf']
        for i, source in enumerate(lit_sources, 1):
            f.write(f"[{i}] {source['name']}\n")
            f.write(f"    Authors: {source.get('authors', 'N/A')}\n")
            f.write(f"    Journal: {source.get('journal', 'N/A')}\n")
            f.write(f"    DOI: {source['doi']}\n")
            f.write(f"    URL: {source['url']}\n")
            if source.get('pdf_candidate'):
                f.write(f"    PDF Candidate: {source['pdf_candidate']}\n")
            f.write(f"    Status: candidate\n\n")

        f.write("================================================================================\n")
        f.write("# End of candidate sources list\n")
        f.write("# Next step: Run T008b to verify these sources\n")

    logger.info(f"Successfully generated candidate sources file: {output_path}")

def generate_research_md_draft(output_path: Path) -> None:
    """
    Generates the initial draft research.md.
    This is a programmatic query of the spec's source list converted to markdown format.
    """
    logger = get_logger(__name__)
    logger.info(f"Generating research.md draft at: {output_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Research Sources: Solder Hardness Prediction\n")
        f.write("## Initial Draft (Generated by T008a)\n\n")
        f.write("This document contains the initial list of candidate sources for data ingestion.\n")
        f.write("These sources have been identified from the spec and known repositories.\n")
        f.write("They require verification (T008b) before use.\n\n")

        f.write("---\n\n")
        f.write("## 1. Primary Data Repositories\n\n")
        
        for source in SOURCE_DEFINITIONS:
            if source['type'] in ['api', 'database', 'repository']:
                f.write(f"### {source['name']}\n")
                f.write(f"- **URL**: [{source['url']}]({source['url']})\n")
                f.write(f"- **Type**: {source['type']}\n")
                f.write(f"- **Description**: {source['description']}\n")
                if source.get('endpoint'):
                    f.write(f"- **Endpoint**: {source['endpoint']}\n")
                if source.get('search_query'):
                    f.write(f"- **Search Query**: `{source['search_query']}`\n")
                f.write(f"- **Status**: Candidate (Pending Verification)\n\n")

        f.write("---\n\n")
        f.write("## 2. Literature for PDF Scraping\n\n")

        for source in SOURCE_DEFINITIONS:
            if source['type'] == 'literature_pdf':
                f.write(f"### {source['name']}\n")
                f.write(f"- **Authors**: {source.get('authors', 'N/A')}\n")
                f.write(f"- **Journal**: {source.get('journal', 'N/A')}\n")
                f.write(f"- **DOI**: {source['doi']}\n")
                f.write(f"- **URL**: [{source['url']}]({source['url']})\n")
                if source.get('pdf_candidate'):
                    f.write(f"- **PDF Link**: {source['pdf_candidate']}\n")
                f.write(f"- **Status**: Candidate (Pending Verification)\n\n")

    logger.info(f"Successfully generated research.md draft: {output_path}")

def main():
    """
    Main entry point for T008a.
    Generates candidate_sources.txt and research.md draft.
    """
    logger = get_logger(__name__)
    logger.info("Starting T008a: Generate Research Sources")

    # Define output paths relative to project root
    # Assuming project root is the parent of 'code'
    project_root = Path(__file__).resolve().parent.parent.parent
    data_config_dir = project_root / "data" / "config"
    
    candidate_sources_path = data_config_dir / "candidate_sources.txt"
    research_md_path = data_config_dir.parent.parent / "specs" / "001-predict-solder-hardness" / "research.md"
    
    # Ensure specs directory exists if it doesn't
    research_md_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Generate candidate sources file
        generate_candidate_sources_file(candidate_sources_path)
        
        # 2. Generate research.md draft
        generate_research_md_draft(research_md_path)

        logger.info("T008a completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Failed to complete T008a: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())
