import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import logging utilities from the project's existing API surface
from src.utils.logger import get_logger, log_info, log_error, log_warning, setup_logging_for_task

# Constants
TARGET_SPECIES = ["wheat", "rice", "maize", "tomato", "soybean"]
MAX_RETRIES = 3
RETRY_DELAY = 2.0  # seconds
NCBI_EUTILS_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
OUTPUT_DIR = Path("data/processed")
REPORT_FILE = OUTPUT_DIR / "feasibility_report.md"
GATE_STATUS_FILE = OUTPUT_DIR / "feasibility_gate_status.yaml"

logger = get_logger(__name__)

def make_ncbi_request(term: str, db: str = "biosample") -> Optional[Dict[str, Any]]:
    """
    Make a request to NCBI E-utilities with retry logic and exponential backoff.
    Returns parsed JSON result or None if all retries fail.
    """
    import urllib.request
    import urllib.parse
    import urllib.error
    import xml.etree.ElementTree as ET

    base_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": db,
        "term": term,
        "retmode": "json",
        "retmax": 100,
        "usehistory": "y"
    }
    query_string = urllib.parse.urlencode(params)
    full_url = f"{base_url}?{query_string}"

    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            log_info(f"Attempting NCBI request (attempt {attempt + 1}/{MAX_RETRIES}): {term}")
            with urllib.request.urlopen(full_url, timeout=30) as response:
                data = response.read().decode('utf-8')
                result = json.loads(data)
                if "esearchresult" in result:
                    count = int(result["esearchresult"].get("count", 0))
                    ids = result["esearchresult"].get("idlist", [])
                    log_info(f"Found {count} records for '{term}'. IDs: {ids[:5]}...")
                    return {
                        "count": count,
                        "ids": ids,
                        "term": term
                    }
                else:
                    log_warning(f"Unexpected response structure for '{term}': {result}")
                    return None
        except urllib.error.URLError as e:
            attempt += 1
            if attempt < MAX_RETRIES:
                wait_time = RETRY_DELAY * (2 ** (attempt - 1))
                log_warning(f"Network error for '{term}': {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                log_error(f"Failed to fetch data for '{term}' after {MAX_RETRIES} attempts: {e}")
                return None
        except json.JSONDecodeError as e:
            log_error(f"JSON decode error for '{term}': {e}")
            return None
        except Exception as e:
            log_error(f"Unexpected error for '{term}': {e}")
            return None
    return None

def search_biosample_for_species(species: str) -> Dict[str, Any]:
    """
    Search NCBI BioSample for records linked to phenotypic disease labels for a specific species.
    Constructs a query that looks for disease susceptibility or resistance phenotypes.
    """
    # Query strategy: Combine species name with disease/phenotype terms
    # Using common disease terms for crop plants
    disease_terms = [
        "disease susceptibility", "disease resistance", "pathogen response",
        "blight", "rust", "mildew", "virus", "fungus", "bacteria"
    ]
    
    results = []
    for disease_term in disease_terms:
        query = f"{species}[Organism] AND ({disease_term})[Properties]"
        result = make_ncbi_request(query, db="biosample")
        if result and result["count"] > 0:
            results.append({
                "query": query,
                "count": result["count"],
                "sample_ids": result["ids"][:10]  # Store first 10 IDs as examples
            })
            log_info(f"Found {result['count']} BioSample records for {species} with '{disease_term}'")
    
    return {
        "species": species,
        "total_studies": sum(r["count"] for r in results),
        "detailed_results": results
    }

def search_bioproject_for_species(species: str) -> Dict[str, Any]:
    """
    Search NCBI BioProject for studies with linked phenotypic disease labels.
    """
    disease_terms = [
        "disease susceptibility", "disease resistance", "pathogen response",
        "blight", "rust", "mildew", "virus", "fungus", "bacteria"
    ]
    
    results = []
    for disease_term in disease_terms:
        query = f"{species}[Organism] AND ({disease_term})[Project Title]"
        result = make_ncbi_request(query, db="bioproject")
        if result and result["count"] > 0:
            results.append({
                "query": query,
                "count": result["count"],
                "project_ids": result["ids"][:10]
            })
            log_info(f"Found {result['count']} BioProject records for {species} with '{disease_term}'")
    
    return {
        "species": species,
        "total_studies": sum(r["count"] for r in results),
        "detailed_results": results
    }

def generate_feasibility_report(all_results: Dict[str, Any]) -> None:
    """
    Generate a markdown report summarizing the feasibility findings.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write("# Feasibility Report: Plant Disease Susceptibility Data\n\n")
        f.write("## Search Parameters\n")
        f.write(f"- Species: {', '.join(TARGET_SPECIES)}\n")
        f.write(f"- Databases: NCBI BioSample, NCBI BioProject\n")
        f.write(f"- Search Terms: Disease susceptibility, resistance, pathogen response, etc.\n\n")
        
        total_found = 0
        for species in TARGET_SPECIES:
            bio_sample_data = all_results.get("biosample", {}).get(species, {})
            bio_project_data = all_results.get("bioproject", {}).get(species, {})
            
            bio_sample_count = bio_sample_data.get("total_studies", 0)
            bio_project_count = bio_project_data.get("total_studies", 0)
            species_total = bio_sample_count + bio_project_count
            total_found += species_total
            
            f.write(f"## {species.capitalize()}\n")
            f.write(f"- BioSample Records: {bio_sample_count}\n")
            f.write(f"- BioProject Records: {bio_project_count}\n")
            f.write(f"- **Total Found**: {species_total}\n\n")
            
            if bio_sample_data.get("detailed_results"):
                f.write("### BioSample Details\n")
                for res in bio_sample_data["detailed_results"]:
                    f.write(f"- Query: `{res['query']}` -> {res['count']} records\n")
                f.write("\n")
            
            if bio_project_data.get("detailed_results"):
                f.write("### BioProject Details\n")
                for res in bio_project_data["detailed_results"]:
                    f.write(f"- Query: `{res['query']}` -> {res['count']} records\n")
                f.write("\n")
        
        f.write("## Summary\n")
        f.write(f"**Total Studies Found**: {total_found}\n")
        if total_found > 0:
            f.write("\n**Status**: PASS - Data sources identified.\n")
        else:
            f.write("\n**Status**: FAIL - No suitable data sources found.\n")

def generate_gate_status(total_found: int) -> None:
    """
    Generate the feasibility gate status YAML file.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    status = "PASS" if total_found > 0 else "FAIL"
    content = f"""status: {status}
timestamp: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
total_studies_found: {total_found}
species_searched: {', '.join(TARGET_SPECIES)}
"""
    with open(GATE_STATUS_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    
    log_info(f"Feasibility gate status generated: {status}")

def main() -> int:
    """
    Main entry point for the feasibility gate task.
    Returns 0 on success (PASS), 1 on failure (FAIL).
    """
    setup_logging_for_task("T001a")
    log_info("Starting Phase 0: Data Discovery & Feasibility Gate")
    
    all_results = {
        "biosample": {},
        "bioproject": {}
    }
    
    for species in TARGET_SPECIES:
        log_info(f"Searching for {species}...")
        all_results["biosample"][species] = search_biosample_for_species(species)
        all_results["bioproject"][species] = search_bioproject_for_species(species)
    
    # Calculate total
    total_found = 0
    for species in TARGET_SPECIES:
        total_found += all_results["biosample"][species].get("total_studies", 0)
        total_found += all_results["bioproject"][species].get("total_studies", 0)
    
    # Generate reports
    generate_feasibility_report(all_results)
    generate_gate_status(total_found)
    
    log_info(f"Feasibility check complete. Total studies found: {total_found}")
    
    if total_found == 0:
        log_error("Feasibility Gate Failed: No suitable data sources found.")
        return 1
    
    log_info("Feasibility Gate Passed: Data sources identified.")
    return 0

if __name__ == "__main__":
    sys.exit(main())