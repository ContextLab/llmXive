"""
Task T013: Search Metabolomics Workbench for defense metabolite experiments.

Searches for experiments containing terpenoids, alkaloids, and phenylpropanoids.
Outputs a JSON file with experiment metadata to data/raw/metabolomics_search_results.json.
"""
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path to import sibling modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.data_download import create_session
from code.exceptions import raise_dataset_error

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(PROJECT_ROOT / 'logs' / 'metabolomics_search.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Metabolomics Workbench API endpoints
MW_API_BASE = "https://www.metabolomicsworkbench.org/rest"
STUDY_SEARCH_URL = f"{MW_API_BASE}/study"
ANALYSIS_SEARCH_URL = f"{MW_API_BASE}/analysis"

# Keywords for defense compounds
DEFENSE_KEYWORDS = [
    "terpenoid", "terpene",
    "alkaloid", "alkaloids",
    "phenylpropanoid", "phenylpropanoids",
    "defense", "herbivore", "stress", "insect"
]

def search_metabolomics_workbench(
    keywords: List[str],
    organism: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search Metabolomics Workbench for studies matching keywords.
    
    Args:
        keywords: List of search terms (defense compound classes)
        organism: Optional organism filter (e.g., 'Arabidopsis', 'Solanum')
        
    Returns:
        List of study metadata dictionaries
    """
    session = create_session()
    found_studies = []
    seen_ids = set()

    # Construct search query
    query_terms = " ".join(keywords)
    if organism:
        query_terms = f"{query_terms} {organism}"

    logger.info(f"Searching MW for: '{query_terms}'")

    try:
        # MW REST API search endpoint
        params = {
            "STUDY_TITLE": query_terms,
            "FORMAT": "JSON"
        }
        
        response = session.get(STUDY_SEARCH_URL, params=params, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        
        # Parse results
        if isinstance(data, list):
            for study in data:
                study_id = study.get("STUDY_ID") or study.get("studies", [{}])[0].get("STUDY_ID")
                if not study_id:
                    continue
                
                if study_id in seen_ids:
                    continue
                seen_ids.add(study_id)
                
                # Extract relevant metadata
                study_meta = {
                    "study_id": study_id,
                    "title": study.get("STUDY_TITLE", "Unknown"),
                    "organism": study.get("ORGANISM", "Unknown"),
                    "treatment": study.get("TREATMENT", "Unknown"),
                    "sample_count": study.get("SAMPLE_COUNT", 0),
                    "metabolite_count": study.get("METABOLITE_COUNT", 0),
                    "database": "Metabolomics Workbench",
                    "source_url": f"https://www.metabolomicsworkbench.org/studies/study.php?STUDY_ID={study_id}"
                }
                
                # Check if it contains defense-related terms in title/treatment
                combined_text = f"{study_meta['title']} {study_meta['treatment']}".lower()
                if any(kw in combined_text for kw in ["terpen", "alkaloid", "phenylprop", "defense", "herbivore", "stress"]):
                    found_studies.append(study_meta)
                    logger.info(f"Found study: {study_id} - {study_meta['title']}")
                    
    except Exception as e:
        logger.error(f"Error searching Metabolomics Workbench: {e}")
        raise_dataset_error(f"Failed to search Metabolomics Workbench: {e}")

    return found_studies

def search_by_analysis_type(keywords: List[str]) -> List[Dict[str, Any]]:
    """
    Search by analysis type to find specific metabolite profiles.
    """
    session = create_session()
    found_analyses = []
    
    for keyword in keywords:
        try:
            params = {
                "ANALYSIS_TYPE": keyword,
                "FORMAT": "JSON"
            }
            response = session.get(ANALYSIS_SEARCH_URL, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, list):
                for analysis in data:
                    analysis_id = analysis.get("ANALYSIS_ID")
                    if analysis_id:
                        found_analyses.append({
                            "analysis_id": analysis_id,
                            "type": keyword,
                            "source": "Metabolomics Workbench Analysis"
                        })
        except Exception as e:
            logger.warning(f"Error searching analysis type {keyword}: {e}")
            continue
            
    return found_analyses

def save_search_results(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save search results to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    search_metadata = {
        "search_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "query_terms": DEFENSE_KEYWORDS,
        "total_results": len(results),
        "results": results
    }
    
    with open(output_path, 'w') as f:
        json.dump(search_metadata, f, indent=2)
    
    logger.info(f"Saved {len(results)} results to {output_path}")

def main():
    """
    Main entry point for T013: Search Metabolomics Workbench.
    """
    logger.info("Starting Metabolomics Workbench search (Task T013)")
    
    # Define output path
    output_path = PROJECT_ROOT / "data" / "raw" / "metabolomics_search_results.json"
    
    # Perform search
    try:
        # Search for general defense compound studies
        studies = search_metabolomics_workbench(DEFENSE_KEYWORDS)
        
        # Also search for specific plant organisms if needed
        arabidopsis_studies = search_metabolomics_workbench(DEFENSE_KEYWORDS, organism="Arabidopsis")
        solanum_studies = search_metabolomics_workbench(DEFENSE_KEYWORDS, organism="Solanum")
        
        # Combine and deduplicate
        all_results = {s["study_id"]: s for s in studies + arabidopsis_studies + solanum_studies}
        combined_results = list(all_results.values())
        
        if not combined_results:
            logger.warning("No relevant studies found in Metabolomics Workbench.")
            # Create empty result file to indicate search was performed
            save_search_results([], output_path)
            return
        
        logger.info(f"Found {len(combined_results)} relevant studies")
        save_search_results(combined_results, output_path)
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise_dataset_error(f"Task T013 failed: {e}")

if __name__ == "__main__":
    main()
