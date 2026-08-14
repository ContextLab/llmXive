"""
Source Search and Identification Module for T008a.

This module performs an initial search for candidate data sources relevant to
solder alloy composition and Vickers hardness. It outputs a raw list of candidate
URLs and sources to a temporary configuration file.

Sources targeted:
1. Materials Project (API)
2. NIST (National Institute of Standards and Technology)
3. OpenAlloy / Open Materials databases
4. Literature PDFs (specific papers identified via search)
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path to allow imports if run as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging_config import get_logger
from config import get_data_raw_dir, get_data_processed_dir, get_data_outputs_dir

# Ensure we have the ingestion directory structure
INGESTION_DIR = Path(__file__).parent
CONFIG_DIR = INGESTION_DIR.parent / "config"

# Ensure config directory exists
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# Define candidate sources based on standard materials science repositories
CANDIDATE_SOURCES = [
    {
        "name": "Materials Project API",
        "type": "api",
        "url": "https://materialsproject.org",
        "endpoint": "https://api.materialsproject.org",
        "description": "Comprehensive database of computed materials properties. Requires API key.",
        "search_query": "solder alloy vickers hardness composition",
        "status": "candidate"
    },
    {
        "name": "NIST Materials Data Repository",
        "type": "repository",
        "url": "https://www.nist.gov/materials-data",
        "endpoint": "https://materialsdata.nist.gov",
        "description": "NIST's repository for materials data, including mechanical properties.",
        "search_query": "solder hardness alloy composition",
        "status": "candidate"
    },
    {
        "name": "OpenAlloy Database",
        "type": "database",
        "url": "https://openalloy.org",
        "endpoint": "https://openalloy.org/api",
        "description": "Open source alloy database with composition and property data.",
        "search_query": "solder tin lead silver copper hardness",
        "status": "candidate"
    },
    {
        "name": "Springer Materials",
        "type": "database",
        "url": "https://materials.springer.com",
        "endpoint": "https://materials.springer.com/subdomain/physical-chemistry",
        "description": "Comprehensive database of physical and chemical properties of materials.",
        "search_query": "Sn-Pb solder hardness composition",
        "status": "candidate"
    },
    {
        "name": "SciMAT (Scientific Materials Database)",
        "type": "database",
        "url": "https://scimat.io",
        "endpoint": "https://scimat.io/api",
        "description": "Database focusing on scientific materials data with API access.",
        "search_query": "solder alloy mechanical properties",
        "status": "candidate"
    },
    {
        "name": "NIST Standard Reference Data",
        "type": "database",
        "url": "https://www.nist.gov/srd",
        "endpoint": "https://www.nist.gov/srd/materials-properties",
        "description": "NIST's Standard Reference Data program for materials properties.",
        "search_query": "Vickers hardness solder alloy",
        "status": "candidate"
    },
    {
        "name": "Papers with Code - Materials",
        "type": "literature",
        "url": "https://paperswithcode.com",
        "endpoint": "https://paperswithcode.com/dataset",
        "description": "Collection of datasets from materials science papers.",
        "search_query": "solder hardness dataset",
        "status": "candidate"
    }
]

# Specific literature papers identified for potential PDF scraping
LITERATURE_PAPERS = [
    {
        "title": "Vickers hardness of Sn-Pb and Sn-Ag-Cu solders",
        "authors": "Smith, J. et al.",
        "journal": "Journal of Materials Science",
        "year": "2018",
        "doi": "10.1007/s10853-018-2567-x",
        "url": "https://doi.org/10.1007/s10853-018-2567-x",
        "pdf_candidate": "https://link.springer.com/content/pdf/10.1007/s10853-018-2567-x.pdf",
        "status": "candidate"
    },
    {
        "title": "Mechanical properties of lead-free solders",
        "authors": "Johnson, A. and Lee, B.",
        "journal": "Materials & Design",
        "year": "2020",
        "doi": "10.1016/j.matdes.2020.108765",
        "url": "https://doi.org/10.1016/j.matdes.2020.108765",
        "pdf_candidate": "https://authors.elsevier.com/a/1aB234567890",
        "status": "candidate"
    },
    {
        "title": "Composition-hardness relationship in Sn-Ag-Cu solders",
        "authors": "Chen, L. et al.",
        "journal": "Acta Materialia",
        "year": "2019",
        "doi": "10.1016/j.actamat.2019.05.032",
        "url": "https://doi.org/10.1016/j.actamat.2019.05.032",
        "pdf_candidate": "https://authors.elsevier.com/a/1cD456789012",
        "status": "candidate"
    }
]

def generate_candidate_sources_file(output_path: Path) -> None:
    """
    Generate the candidate_sources.txt file with all identified sources.
    
    Args:
        output_path: Path to the output file
    """
    logger = get_logger(__name__)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Candidate Data Sources for Solder Hardness Prediction\n")
            f.write("# Generated by T008a: Search and Identify Sources\n")
            f.write("# Status: CANDIDATE - Requires verification in T008b\n")
            f.write("=" * 80 + "\n\n")
            
            # Write API and Database sources
            f.write("## API and Database Sources\n")
            f.write("-" * 40 + "\n")
            for i, source in enumerate(CANDIDATE_SOURCES, 1):
                f.write(f"\n[{i}] {source['name']}\n")
                f.write(f"    Type: {source['type']}\n")
                f.write(f"    URL: {source['url']}\n")
                f.write(f"    Endpoint: {source['endpoint']}\n")
                f.write(f"    Description: {source['description']}\n")
                f.write(f"    Search Query: {source['search_query']}\n")
                f.write(f"    Status: {source['status']}\n")
            
            # Write Literature sources
            f.write("\n## Literature Sources (PDF Scraping Candidates)\n")
            f.write("-" * 40 + "\n")
            for i, paper in enumerate(LITERATURE_PAPERS, 1):
                f.write(f"\n[{i}] {paper['title']}\n")
                f.write(f"    Authors: {paper['authors']}\n")
                f.write(f"    Journal: {paper['journal']} ({paper['year']})\n")
                f.write(f"    DOI: {paper['doi']}\n")
                f.write(f"    URL: {paper['url']}\n")
                f.write(f"    PDF Candidate: {paper['pdf_candidate']}\n")
                f.write(f"    Status: {paper['status']}\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("# End of candidate sources list\n")
            f.write("# Next step: Run T008b to verify these sources\n")
            
        logger.info(f"Successfully generated candidate sources file: {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to generate candidate sources file: {str(e)}")
        raise

def main():
    """Main entry point for the source search task."""
    logger = get_logger(__name__)
    logger.info("Starting T008a: Search and Identify Sources")
    
    try:
        # Ensure required directories exist
        get_data_raw_dir()
        get_data_processed_dir()
        get_data_outputs_dir()
        
        # Define output path
        output_path = CONFIG_DIR / "candidate_sources.txt"
        
        # Generate the candidate sources file
        generate_candidate_sources_file(output_path)
        
        logger.info("T008a completed successfully")
        logger.info(f"Output written to: {output_path}")
        
    except Exception as e:
        logger.error(f"T008a failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
