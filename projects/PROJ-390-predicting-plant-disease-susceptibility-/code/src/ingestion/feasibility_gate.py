"""
Task T001a: Phase 0 - Data Discovery & Feasibility Gate.

Searches NCBI BioProject/BioSample for SRA studies with linked phenotypic
disease labels for wheat, rice, maize, tomato, and soybean.
Generates data/processed/feasibility_report.md.
Generates data/processed/feasibility_gate_status.yaml.
Exits with code 1 if no studies found, 0 otherwise.
"""
import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger, setup_logging_for_task, close_logging
from src.utils.config import get_species_accession, get_species_info

# Constants
NCBI_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
NCBI_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
NCBI_EMAIL = "research@example.com"  # Replace with actual email in production
TOOL_NAME = "llmXive_feasibility_gate"
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds

# Target species and keywords
TARGET_SPECIES = ["wheat", "rice", "maize", "tomato", "soybean"]
DISEASE_KEYWORDS = ["disease", "pathogen", "susceptibility", "resistance", "infection", "blight", "rust", "mildew"]

logger = get_logger(__name__)

def make_ncbi_request(url: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Make a request to NCBI E-utilities with retry logic."""
    params['email'] = NCBI_EMAIL
    params['tool'] = TOOL_NAME

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            # NCBI returns XML by default, but we can request JSON
            if 'retmode=json' in url or params.get('retmode') == 'json':
                return response.json()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                logger.error(f"Failed after {MAX_RETRIES} attempts")
                return None

def search_biosample_for_species(species: str) -> List[Dict[str, Any]]:
    """Search BioSample for samples of a specific species with disease-related metadata."""
    studies_found = []
    
    # Construct search query
    # Look for BioSample entries with organism name and disease-related attributes
    disease_query = " OR ".join([f'"{kw}"[All Fields]' for kw in DISEASE_KEYWORDS])
    search_query = f'organism:"{species}" AND ({disease_query}) AND biosample'
    
    params = {
        'db': 'biosample',
        'term': search_query,
        'retmode': 'json',
        'retmax': 100  # Fetch up to 100 records per species
    }

    logger.info(f"Searching BioSample for {species} with disease keywords...")
    result = make_ncbi_request(NCBI_ESEARCH_URL, params)

    if not result or 'ids' not in result:
        logger.warning(f"No results found for {species} in BioSample")
        return studies_found

    ids = result.get('ids', [])
    if not ids:
        logger.info(f"No BioSample IDs found for {species}")
        return studies_found

    # Fetch details for each ID
    for bio_id in ids[:10]:  # Limit to first 10 to avoid rate limiting
        fetch_params = {
            'db': 'biosample',
            'id': bio_id,
            'retmode': 'json'
        }
        details = make_ncbi_request(NCBI_EFETCH_URL, fetch_params)
        
        if details and 'result' in details:
            record = details['result'].get(bio_id, {})
            # Check if it has disease-related attributes
            attributes = record.get('attributes', [])
            disease_related = False
            for attr in attributes:
                attr_name = attr.get('attribute_name', '').lower()
                attr_value = attr.get('value', '').lower()
                for kw in DISEASE_KEYWORDS:
                    if kw in attr_name or kw in attr_value:
                        disease_related = True
                        break
                if disease_related:
                    break

            if disease_related:
                studies_found.append({
                    'species': species,
                    'biosample_id': bio_id,
                    'title': record.get('description', 'No title'),
                    'accession': record.get('accession', 'N/A'),
                    'attributes': {a['attribute_name']: a['value'] for a in attributes}
                })
                logger.info(f"Found disease-related sample: {bio_id} for {species}")

    return studies_found

def search_bioproject_for_species(species: str) -> List[Dict[str, Any]]:
    """Search BioProject for projects related to disease studies of a specific species."""
    projects_found = []
    
    disease_query = " OR ".join([f'"{kw}"[All Fields]' for kw in DISEASE_KEYWORDS])
    search_query = f'organism:"{species}" AND ({disease_query}) AND bioproject'
    
    params = {
        'db': 'bioproject',
        'term': search_query,
        'retmode': 'json',
        'retmax': 50
    }

    logger.info(f"Searching BioProject for {species} with disease keywords...")
    result = make_ncbi_request(NCBI_ESEARCH_URL, params)

    if not result or 'ids' not in result:
        logger.warning(f"No results found for {species} in BioProject")
        return projects_found

    ids = result.get('ids', [])
    
    for proj_id in ids[:5]:  # Limit to first 5
        fetch_params = {
            'db': 'bioproject',
            'id': proj_id,
            'retmode': 'json'
        }
        details = make_ncbi_request(NCBI_EFETCH_URL, fetch_params)
        
        if details and 'result' in details:
            record = details['result'].get(proj_id, {})
            projects_found.append({
                'species': species,
                'bioproject_id': proj_id,
                'title': record.get('description', 'No title'),
                'accession': record.get('accession', 'N/A')
            })
            logger.info(f"Found disease-related project: {proj_id} for {species}")

    return projects_found

def generate_feasibility_report(studies: List[Dict], projects: List[Dict], output_path: Path):
    """Generate the feasibility report markdown file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report_lines = [
        "# Feasibility Report: Plant Disease Susceptibility Data Discovery",
        "",
        f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Target Species:** {', '.join(TARGET_SPECIES)}",
        "",
        "## Summary",
        "",
        f"- Total BioSample studies found: {len(studies)}",
        f"- Total BioProject studies found: {len(projects)}",
        "",
        "## Detailed Findings",
        ""
    ]

    if studies:
        report_lines.append("### BioSample Studies")
        report_lines.append("")
        report_lines.append("| Species | BioSample ID | Accession | Description | Disease Attributes |")
        report_lines.append("|---------|--------------|-----------|-------------|---------------------|")
        for study in studies:
            attrs = ", ".join([f"{k}: {v}" for k, v in list(study['attributes'].items())[:3]])
            report_lines.append(
                f"| {study['species']} | {study['biosample_id']} | {study['accession']} | "
                f"{study['title'][:50]}... | {attrs} |"
            )
        report_lines.append("")

    if projects:
        report_lines.append("### BioProject Studies")
        report_lines.append("")
        report_lines.append("| Species | BioProject ID | Accession | Description |")
        report_lines.append("|---------|---------------|-----------|-------------|")
        for proj in projects:
            report_lines.append(
                f"| {proj['species']} | {proj['bioproject_id']} | {proj['accession']} | "
                f"{proj['title'][:50]}... |"
            )
        report_lines.append("")

    if not studies and not projects:
        report_lines.append("## Status: FAIL")
        report_lines.append("")
        report_lines.append("No disease-related genomic studies found for any target species.")
        report_lines.append("The pipeline will halt.")
    else:
        report_lines.append("## Status: PASS")
        report_lines.append("")
        report_lines.append("Disease-related genomic studies found. Pipeline can proceed.")

    report_content = "\n".join(report_lines)
    output_path.write_text(report_content)
    logger.info(f"Feasibility report written to {output_path}")

def generate_gate_status(passed: bool, output_path: Path):
    """Generate the feasibility gate status YAML file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    status = "PASS" if passed else "FAIL"
    yaml_content = f"""status: {status}
timestamp: {time.strftime('%Y-%m-%dT%H:%M:%SZ')}
message: "Feasibility gate {'passed' if passed else 'failed'}."
"""
    output_path.write_text(yaml_content)
    logger.info(f"Gate status written to {output_path}")

def main():
    """Main entry point for the feasibility gate task."""
    # Setup logging
    task_name = "T001a_feasibility_gate"
    setup_logging_for_task(task_name)
    
    try:
        logger.info("Starting Phase 0: Data Discovery & Feasibility Gate")
        
        # Ensure output directories exist
        data_processed_dir = Path("data/processed")
        data_processed_dir.mkdir(parents=True, exist_ok=True)
        
        all_studies = []
        all_projects = []
        
        # Search for each target species
        for species in TARGET_SPECIES:
            logger.info(f"Processing species: {species}")
            studies = search_biosample_for_species(species)
            projects = search_bioproject_for_species(species)
            all_studies.extend(studies)
            all_projects.extend(projects)
            time.sleep(0.5)  # Be polite to NCBI servers

        # Generate outputs
        report_path = data_processed_dir / "feasibility_report.md"
        status_path = data_processed_dir / "feasibility_gate_status.yaml"
        
        passed = len(all_studies) > 0 or len(all_projects) > 0
        
        generate_feasibility_report(all_studies, all_projects, report_path)
        generate_gate_status(passed, status_path)
        
        if passed:
            logger.info("Feasibility Gate PASSED. Proceeding to next phase.")
            sys.exit(0)
        else:
            logger.error("Feasibility Gate FAILED. No suitable data found.")
            sys.exit(1)
            
    except Exception as e:
        logger.exception(f"Fatal error in feasibility gate: {e}")
        # Even on error, try to write a FAIL status
        try:
            generate_gate_status(False, Path("data/processed/feasibility_gate_status.yaml"))
        except:
            pass
        sys.exit(1)
    finally:
        close_logging()

if __name__ == "__main__":
    main()