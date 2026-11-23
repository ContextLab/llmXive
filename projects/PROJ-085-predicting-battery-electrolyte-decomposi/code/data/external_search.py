import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Import project utilities
from config import get_project_root, get_validation_dir, get_config
from utils.logging_config import get_logger

# Setup logger
logger = get_logger(__name__)

def get_data_status_path() -> Path:
    """Return the path to the data status JSON file."""
    val_dir = get_validation_dir()
    return val_dir / "data_status.json"

def load_existing_status() -> Dict[str, Any]:
    """Load existing status file if it exists, otherwise return a default structure."""
    path = get_data_status_path()
    if path.exists():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load existing status file {path}: {e}. Starting fresh.")
    
    return {
        "external_data_available": False,
        "sources_checked": [],
        "last_checked": None,
        "found_urls": [],
        "error_details": [],
        "validation_mode": "pending"
    }

def save_status(status: Dict[str, Any]) -> None:
    """Save the status dictionary to the JSON file."""
    path = get_data_status_path()
    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2)
    logger.info(f"Saved data status to {path}")

def search_nomad_api() -> Tuple[bool, List[str], Optional[str]]:
    """
    Search NOMAD API for experimental onset potentials.
    
    Returns:
        Tuple of (found: bool, urls: List[str], error: Optional[str])
    """
    import requests
    
    found_urls = []
    error = None
    
    # Keywords for search
    keywords = [
        "electrolyte onset potential",
        "electrolyte cyclic voltammetry",
        "EC decomposition potential",
        "DMC decomposition potential"
    ]
    
    # NOMAD API endpoint (public read-only)
    base_url = "https://nomad-lab.eu/prod/rae/api/v1/entries"
    
    for keyword in keywords:
        try:
            params = {
                "filter": f'archive.data.general.keywords contains "{keyword}"',
                "page_size": 5,
                "include": "meta,archive.data.general"
            }
            
            response = requests.get(base_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                entries = data.get('data', [])
                
                if entries:
                    logger.info(f"NOMAD search for '{keyword}' found {len(entries)} entries.")
                    for entry in entries[:3]:  # Limit to top 3
                        entry_id = entry.get('entry_id', 'unknown')
                        url = f"https://nomad-lab.eu/prod/rae/entry/{entry_id}"
                        found_urls.append(url)
            else:
                logger.warning(f"NOMAD API returned status {response.status_code} for '{keyword}'")
                
        except requests.exceptions.RequestException as e:
            error = f"NOMAD API request failed: {str(e)}"
            logger.warning(error)
            # Continue to next keyword
        except Exception as e:
            error = f"NOMAD search error for '{keyword}': {str(e)}"
            logger.warning(error)
    
    return (len(found_urls) > 0, found_urls, error)

def search_pubchem() -> Tuple[bool, List[str], Optional[str]]:
    """
    Search PubChem for electrolyte properties and onset potentials.
    
    Returns:
        Tuple of (found: bool, urls: List[str], error: Optional[str])
    """
    import requests
    
    found_urls = []
    error = None
    
    # Electrolyte compounds to search
    compounds = [
        ("Ethylene Carbonate", "EC"),
        ("Dimethyl Carbonate", "DMC"),
        ("Lithium Hexafluorophosphate", "LiPF6")
    ]
    
    base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/search"
    
    for compound_name, abbreviation in compounds:
        try:
            # Search by name
            search_url = f"{base_url}/compound/name/{compound_name}/cids/JSON"
            response = requests.get(search_url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                cids = data.get('IdentifierList', {}).get('CID', [])
                
                if cids:
                    cid = cids[0]
                    # Get property summary
                    prop_url = f"{base_url}/compound/cid/{cid}/property/OnsetPotential,ReductionPotential/JSON"
                    prop_response = requests.get(prop_url, timeout=30)
                    
                    if prop_response.status_code == 200:
                        prop_data = prop_response.json()
                        # If we found property data, add URL
                        url = f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}"
                        found_urls.append(url)
                        logger.info(f"Found PubChem data for {compound_name} (CID: {cid})")
                    else:
                        # Even without specific property, the compound page is a valid resource
                        url = f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}"
                        found_urls.append(url)
                        logger.info(f"Found PubChem entry for {compound_name} (CID: {cid})")
                else:
                    logger.warning(f"No CID found for {compound_name} in PubChem")
            else:
                logger.warning(f"PubChem returned status {response.status_code} for {compound_name}")
                
        except requests.exceptions.RequestException as e:
            error = f"PubChem request failed: {str(e)}"
            logger.warning(error)
        except Exception as e:
            error = f"PubChem search error for {compound_name}: {str(e)}"
            logger.warning(error)
    
    return (len(found_urls) > 0, found_urls, error)

def check_research_md_dois() -> Tuple[bool, List[str], Optional[str]]:
    """
    Check DOIs cited in research.md for experimental data.
    
    Returns:
        Tuple of (found: bool, urls: List[str], error: Optional[str])
    """
    import requests
    from urllib.parse import urlparse
    
    found_urls = []
    error = None
    
    # Read research.md to find DOIs
    root = get_project_root()
    research_path = root / "docs" / "research.md"
    
    if not research_path.exists():
        logger.warning("research.md not found. Skipping DOI check.")
        return False, [], "research.md not found"
    
    try:
        with open(research_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except IOError as e:
        return False, [], f"Failed to read research.md: {e}"
    
    # Simple regex to find DOIs (pattern: 10.xxxx/xxxxx)
    import re
    doi_pattern = r'10\.\d{4,9}/[-._;()/:A-Z0-9]+'
    dois = re.findall(doi_pattern, content, re.IGNORECASE)
    
    if not dois:
        logger.info("No DOIs found in research.md")
        return False, [], "No DOIs found in research.md"
    
    logger.info(f"Found {len(dois)} DOI(s) in research.md: {dois}")
    
    # Check each DOI via Crossref API
    for doi in dois:
        try:
            url = f"https://api.crossref.org/works/{doi}"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                item = data.get('message', {})
                
                # Check if it's a journal article with experimental data
                title = item.get('title', [''])[0].lower()
                if any(term in title for term in ['electrolyte', 'battery', 'decomposition', 'potential', 'voltammetry']):
                    found_urls.append(f"https://doi.org/{doi}")
                    logger.info(f"Validated experimental DOI: {doi}")
                else:
                    logger.info(f"DOI {doi} found but not clearly experimental electrolyte data")
            else:
                logger.warning(f"Crossref API returned status {response.status_code} for DOI {doi}")
                
        except requests.exceptions.RequestException as e:
            error = f"Crossref request failed for DOI {doi}: {str(e)}"
            logger.warning(error)
        except Exception as e:
            error = f"DOI check error for {doi}: {str(e)}"
            logger.warning(error)
    
    return (len(found_urls) > 0, found_urls, error)

def run_external_search() -> Dict[str, Any]:
    """
    Run all external data search methods and compile results.
    
    Returns:
        Dictionary containing search results and status.
    """
    import datetime
    
    logger.info("Starting external data search for experimental onset potentials...")
    
    status = load_existing_status()
    status["sources_checked"] = []
    status["found_urls"] = []
    status["error_details"] = []
    status["last_checked"] = datetime.datetime.now().isoformat()
    
    # 1. Search NOMAD API
    nomad_found, nomad_urls, nomad_error = search_nomad_api()
    status["sources_checked"].append("NOMAD API")
    status["found_urls"].extend(nomad_urls)
    if nomad_error:
        status["error_details"].append(f"NOMAD: {nomad_error}")
    logger.info(f"NOMAD search result: found={nomad_found}, urls={len(nomad_urls)}")
    
    # 2. Search PubChem
    pubchem_found, pubchem_urls, pubchem_error = search_pubchem()
    status["sources_checked"].append("PubChem")
    status["found_urls"].extend(pubchem_urls)
    if pubchem_error:
        status["error_details"].append(f"PubChem: {pubchem_error}")
    logger.info(f"PubChem search result: found={pubchem_found}, urls={len(pubchem_urls)}")
    
    # 3. Check research.md DOIs
    doi_found, doi_urls, doi_error = check_research_md_dois()
    status["sources_checked"].append("research.md DOIs")
    status["found_urls"].extend(doi_urls)
    if doi_error:
        status["error_details"].append(f"DOIs: {doi_error}")
    logger.info(f"DOI check result: found={doi_found}, urls={len(doi_urls)}")
    
    # Determine overall availability
    total_urls = len(status["found_urls"])
    status["external_data_available"] = (total_urls > 0)
    
    if status["external_data_available"]:
        logger.info(f"External data sources found: {total_urls} valid URLs")
        status["validation_mode"] = "external"
    else:
        logger.warning("No external experimental data sources found.")
        status["validation_mode"] = "internal_fallback"
        status["error_details"].append("No external data sources found after checking all methods.")
    
    # Save the status
    save_status(status)
    
    return status

def main():
    """Main entry point for the external search script."""
    logger.info("Running external data search pipeline...")
    
    try:
        status = run_external_search()
        
        # Print summary
        print("\n=== External Data Search Results ===")
        print(f"External data available: {status['external_data_available']}")
        print(f"Validation mode: {status['validation_mode']}")
        print(f"Sources checked: {', '.join(status['sources_checked'])}")
        print(f"URLs found: {len(status['found_urls'])}")
        
        if status['found_urls']:
            print("Found URLs:")
            for url in status['found_urls']:
                print(f"  - {url}")
        
        if status['error_details']:
            print("\nErrors/Warnings:")
            for err in status['error_details']:
                print(f"  - {err}")
        
        print(f"\nStatus saved to: {get_data_status_path()}")
        
    except Exception as e:
        logger.error(f"External search pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
