"""
Module to query NCBI GEO and Metabolomics Workbench for Arabidopsis thaliana stress studies.
Falls back to synthetic data generation if no valid paired samples are found.
"""
import os
import sys
import json
import time
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

from generators.synthetic_data import main as generate_synthetic_main

# Constants
NCBI_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
NCBI_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
METABOLOMICS_WORKBENCH_API = "https://www.metabolomicsworkbench.org/studies/rest/v1/study"

SEARCH_QUERY = '("Arabidopsis thaliana"[Title/Abstract] OR "Arabidopsis thaliana"[Organism]) AND ("VOC" OR "volatile"[Title/Abstract]) AND ("RNA-seq"[Title/Abstract]) AND ("stress"[Title/Abstract])'

def search_ncbi_geo(query: str, retmax: int = 100) -> List[Dict[str, Any]]:
    """Search NCBI GEO for studies matching the query."""
    params = {
        "db": "gds",
        "term": query,
        "retmax": retmax,
        "retmode": "json",
        "usehistory": "y"
    }
    results = []
    try:
        response = requests.get(NCBI_ESEARCH_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "result" in data and "ids" in data["result"]:
            for study_id in data["result"]["ids"]:
                if study_id == "total":
                    continue
                # Fetch details for each study
                fetch_params = {
                    "db": "gds",
                    "uid": study_id,
                    "retmode": "json"
                }
                fetch_resp = requests.get(NCBI_EFETCH_URL, params=fetch_params, timeout=30)
                fetch_resp.raise_for_status()
                fetch_data = fetch_resp.json()
                
                if "result" in fetch_data and study_id in fetch_data["result"]:
                    study_info = fetch_data["result"][study_id]
                    results.append({
                        "source": "NCBI_GEO",
                        "id": study_id,
                        "title": study_info.get("title", ""),
                        "summary": study_info.get("summary", ""),
                        "organism": study_info.get("organism", ""),
                        "platform": study_info.get("platform", ""),
                        "samples": study_info.get("samples", []),
                        "url": f"https://www.ncbi.nlm.nih.gov/gds/?term={study_id}"
                    })
        return results
    except Exception as e:
        print(f"Error searching NCBI GEO: {e}")
        return []

def search_metabolomics_workbench() -> List[Dict[str, Any]]:
    """Search Metabolomics Workbench for Arabidopsis VOC studies."""
    results = []
    try:
        # MW API is less structured for complex queries, we fetch recent plant studies
        # and filter client-side for VOC/Arabidopsis
        params = {
            "keyword": "Arabidopsis volatile VOC stress RNA",
            "limit": 100
        }
        # MW doesn't have a direct search API for complex queries, so we use a broader search
        # and filter. In a real production system, we would use their full-text search endpoint
        # or scrape their web interface.
        
        # Since MW's REST API is limited for complex text search, we'll simulate a fetch
        # In a real scenario, this would hit their specific search endpoint
        url = "https://www.metabolomicsworkbench.org/studies/rest/v1/study/search"
        params = {"keyword": "Arabidopsis"}
        
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if "result" in data:
                for study in data["result"]:
                    title = study.get("STUDY_TITLE", "").lower()
                    abstract = study.get("STUDY_ABSTRACT", "").lower()
                    
                    # Filter for VOC and stress related
                    if ("volatile" in title or "voc" in title or "volatile" in abstract or "voc" in abstract) and \
                       ("stress" in title or "stress" in abstract):
                        results.append({
                            "source": "Metabolomics_Workbench",
                            "id": study.get("STUDY_ID", ""),
                            "title": study.get("STUDY_TITLE", ""),
                            "summary": study.get("STUDY_ABSTRACT", ""),
                            "organism": study.get("ORGANISM", ""),
                            "url": f"https://www.metabolomicsworkbench.org/Studies/StudyView.php?STUDY_ID={study.get('STUDY_ID', '')}"
                        })
    except Exception as e:
        print(f"Error searching Metabolomics Workbench: {e}")
        # MW API often has rate limits or is down, continue gracefully
        pass
    return results

def has_valid_pairing(study: Dict[str, Any]) -> bool:
    """Check if a study has both genomic (RNA-seq) and VOC data."""
    # For NCBI GEO, check if it mentions both RNA-seq and VOC in summary/title
    title = study.get("title", "").lower()
    summary = study.get("summary", "").lower()
    
    has_genomic = "rna-seq" in title or "rna-seq" in summary or "transcriptome" in summary
    has_voc = "volatile" in title or "volatile" in summary or "voc" in title or "voc" in summary
    
    return has_genomic and has_voc

def query_sources(log_path: Path) -> Dict[str, Any]:
    """
    Query both NCBI GEO and Metabolomics Workbench.
    Returns a summary of found studies and whether valid paired samples exist.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("Starting data source queries...")
    print(f"Query: {SEARCH_QUERY}")
    
    all_studies = []
    
    # Query NCBI GEO
    print("Querying NCBI GEO...")
    ncbi_studies = search_ncbi_geo(SEARCH_QUERY)
    all_studies.extend(ncbi_studies)
    print(f"Found {len(ncbi_studies)} studies from NCBI GEO.")
    
    # Query Metabolomics Workbench
    print("Querying Metabolomics Workbench...")
    mw_studies = search_metabolomics_workbench()
    all_studies.extend(mw_studies)
    print(f"Found {len(mw_studies)} studies from Metabolomics Workbench.")
    
    # Filter for valid pairings
    valid_studies = [s for s in all_studies if has_valid_pairing(s)]
    
    log_data = {
        "query": SEARCH_QUERY,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sources": {
            "NCBI_GEO": len(ncbi_studies),
            "Metabolomics_Workbench": len(mw_studies)
        },
        "total_studies_found": len(all_studies),
        "valid_paired_studies": len(valid_studies),
        "studies": all_studies,
        "valid_studies": valid_studies
    }
    
    with open(log_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    print(f"Query log written to {log_path}")
    print(f"Total studies found: {len(all_studies)}")
    print(f"Valid paired studies: {len(valid_studies)}")
    
    return log_data

def main():
    """Main entry point for the query script."""
    # Determine project root
    project_root = Path(__file__).parent.parent
    log_path = project_root / "data" / "raw" / "query_log.json"
    
    log_data = query_sources(log_path)
    
    # Check if we have valid paired samples
    if log_data["valid_paired_studies"] == 0:
        print("No valid paired samples found in real sources.")
        print("Triggering synthetic data generation (T005)...")
        generate_synthetic_main()
        print("Synthetic data generation complete.")
    else:
        print(f"Found {log_data['valid_paired_studies']} valid paired studies. Proceeding with real data.")

if __name__ == "__main__":
    main()