import os
import sys
import json
import time
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import get_config

def search_ncbi_geo(query: str, max_results: int = 50) -> List[Dict[str, Any]]:
    """
    Search NCBI GEO for studies matching the query.
    Uses the E-utilities API (esearch).
    """
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "gds",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
        "usehistory": "y"
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "result" not in data or "ids" not in data["result"]:
            return []
        
        ids = data["result"]["ids"]
        results = []
        
        # Fetch details for each ID using esummary
        summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        for gds_id in ids:
            summary_params = {
                "db": "gds",
                "id": gds_id,
                "retmode": "json"
            }
            try:
                summary_resp = requests.get(summary_url, params=summary_params, timeout=30)
                summary_resp.raise_for_status()
                summary_data = summary_resp.json()
                
                if "result" in summary_data and gds_id in summary_data["result"]:
                    item = summary_data["result"][gds_id]
                    results.append({
                        "source": "NCBI_GEO",
                        "id": gds_id,
                        "title": item.get("title", ""),
                        "organism": item.get("organism", ""),
                        "platforms": item.get("platforms", []),
                        "samples": item.get("samples", 0),
                        "url": f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={gds_id}",
                        "has_rna_seq": "RNA-seq" in item.get("title", "").lower() or "RNA-seq" in item.get("summary", "").lower(),
                        "retrieved_at": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
            except Exception as e:
                print(f"Warning: Failed to fetch summary for GDS {gds_id}: {e}")
                continue
        
        return results
    except Exception as e:
        print(f"Error searching NCBI GEO: {e}")
        return []

def search_metabolomics_workbench(query: str, max_results: int = 50) -> List[Dict[str, Any]]:
    """
    Search Metabolomics Workbench for studies.
    Note: MW API is less standardized for text search; we simulate a search via
    their project listing or a specific endpoint if available. 
    For this implementation, we attempt to fetch projects and filter locally 
    as the MW API does not have a simple keyword search endpoint like GEO.
    We will fetch the first batch of projects and filter.
    """
    # MW API endpoint for project search is limited. 
    # We will try to use their 'studies' endpoint with a filter if possible, 
    # or fetch a list and filter.
    # Given constraints, we will attempt to fetch recent studies and filter.
    base_url = "https://www.metabolomicsworkbench.org/data/study_api.php"
    params = {
        "function": "get_studies",
        "limit": max_results
    }
    
    results = []
    try:
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "STUDIES" not in data:
            return []
        
        for study in data["STUDIES"]:
            # Check if keywords match (case insensitive)
            title = study.get("STUDY_TITLE", "").lower()
            abstract = study.get("ABSTRACT", "").lower()
            organism = study.get("ORGANISM", "").lower()
            
            # Simple keyword matching
            if (organism in ["arabidopsis thaliana", "arabidopsis"] and 
                ("volatile" in title or "voc" in title or "volatile" in abstract or "voc" in abstract)):
                results.append({
                    "source": "METABOLOMICS_WORKBENCH",
                    "id": study.get("STUDY_ID", ""),
                    "title": study.get("STUDY_TITLE", ""),
                    "organism": study.get("ORGANISM", ""),
                    "samples": study.get("SAMPLE_COUNT", 0),
                    "url": f"https://www.metabolomicsworkbench.org/data/study.php?STUDY_ID={study.get('STUDY_ID')}",
                    "has_rna_seq": "RNA-seq" in study.get("STUDY_TITLE", "") or "RNA-seq" in study.get("ABSTRACT", ""),
                    "retrieved_at": time.strftime("%Y-%m-%d %H:%M:%S")
                })
    except Exception as e:
        print(f"Error searching Metabolomics Workbench: {e}")
    
    return results

def has_valid_pairing(study: Dict[str, Any]) -> bool:
    """
    Check if a study has valid paired samples (both RNA-seq and VOC data).
    For GEO: Check if the study has RNA-seq data.
    For MW: Check if it has VOC data (implied by search) and potential for pairing.
    This is a heuristic check based on available metadata.
    """
    if study.get("source") == "NCBI_GEO":
        return study.get("has_rna_seq", False) and study.get("samples", 0) > 0
    elif study.get("source") == "METABOLOMICS_WORKBENCH":
        # MW studies often have metabolomics, we need to ensure they are linked to genomic data
        # Since we can't easily verify pairing without deep inspection, we assume potential
        # if it's Arabidopsis and mentions VOC.
        return study.get("samples", 0) > 0
    return False

def query_sources(query: str = "Arabidopsis thaliana AND (VOC OR volatile) AND RNA-seq AND stress", 
                  output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Execute queries against NCBI GEO and Metabolomics Workbench.
    Logs results to a JSON file.
    Triggers synthetic data generation if no valid paired samples are found.
    """
    if output_path is None:
        config = get_config()
        output_path = config.get("data.raw_query_log", "data/raw/query_log.json")
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Searching for: {query}")
    
    geo_results = search_ncbi_geo(query)
    mw_results = search_metabolomics_workbench(query)
    
    all_results = geo_results + mw_results
    
    valid_pairs = [r for r in all_results if has_valid_pairing(r)]
    
    log_entry = {
        "query": query,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_studies_found": len(all_results),
        "geo_count": len(geo_results),
        "mw_count": len(mw_results),
        "valid_paired_samples": len(valid_pairs),
        "results": all_results
    }
    
    with open(output_path, "w") as f:
        json.dump(log_entry, f, indent=2)
    
    print(f"Logged {len(all_results)} studies to {output_path}")
    print(f"Found {len(valid_pairs)} valid paired samples.")
    
    if len(valid_pairs) == 0:
        print("No valid paired samples found. Triggering synthetic data generation (T005).")
        # Trigger T005
        from generators.synthetic_data import main as generate_synthetic_main
        try:
            generate_synthetic_main()
            print("Synthetic data generation completed.")
        except Exception as e:
            print(f"Error generating synthetic data: {e}")
            raise RuntimeError("Failed to find real data and failed to generate synthetic data.")
    
    return log_entry

def main():
    """Main entry point for running the query."""
    config = get_config()
    query = config.get("search.query", "Arabidopsis thaliana AND (VOC OR volatile) AND RNA-seq AND stress")
    output_path = config.get("data.raw_query_log", "data/raw/query_log.json")
    
    query_sources(query=query, output_path=output_path)

if __name__ == "__main__":
    main()
