import logging
import json
import time
import sys
import re
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure project root is in path for imports if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from error_handler import raise_dataset_error, handle_error
from logging_utils import log_data_pairing_mismatch

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / 'logs' / 'data_download.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
METABOLOMICS_WORKBENCH_API = "https://www.metabolomicsworkbench.org/rest/study"
METABOLOMICS_WORKBENCH_STUDY_URL = "https://www.metabolomicsworkbench.org/rest/study/study_summary/STUDY_ID"
METABOLOMICS_WORKBENCH_SAMPLE_URL = "https://www.metabolomicsworkbench.org/rest/study/sample_summary/STUDY_ID"
METABOLOMICS_WORKBENCH_DATA_URL = "https://www.metabolomicsworkbench.org/rest/study/data_download/STUDY_ID"

# Keywords for defense compounds
DEFENSE_KEYWORDS = [
    "terpenoid", "terpene", "alkaloid", "phenylpropanoid", "phenolic",
    "glucosinolate", "defense", "herbivore", "stress", "jasmonate",
    "salicylate", "camalexin", "capsaicin", "nicotine", "caffeine"
]

def create_session() -> requests.Session:
    """Create a requests session with standard headers."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'llmXive-Research-Agent/1.0 (Plant Defense Project)',
        'Accept': 'application/json'
    })
    return session

def search_metabolomics_workbench(session: requests.Session, keywords: List[str]) -> List[Dict[str, Any]]:
    """
    Search Metabolomics Workbench for studies related to plant defense compounds.
    
    Args:
        session: Requests session
        keywords: List of keywords to search for (e.g., terpenoid, alkaloid)
        
    Returns:
        List of matching study metadata dictionaries
    """
    logger.info(f"Searching Metabolomics Workbench for keywords: {keywords}")
    
    matched_studies = []
    
    # We will iterate through known plant-related studies or search by title/abstract
    # Since MW API search is limited, we fetch a broader set and filter locally
    # or search by specific terms if the API supports query parameters.
    # The MW REST API 'study' endpoint allows filtering by 'title' or 'abstract' via query params.
    
    base_url = METABOLOMICS_WORKBENCH_API
    
    for keyword in keywords:
        try:
            # Try searching by title first
            params = {'title': keyword}
            response = session.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # MW API returns a list of studies or a specific structure depending on version
            # Often it returns a list of dictionaries under a key or directly
            studies = data if isinstance(data, list) else data.get('studies', [])
            
            for study in studies:
                study_id = study.get('STUDY_ID') or study.get('study_id')
                title = study.get('TITLE') or study.get('title', '')
                abstract = study.get('ABSTRACT') or study.get('abstract', '')
                
                # Check if it's plant-related (simple heuristic)
                is_plant = any(term in (title + abstract).lower() for term in ['plant', 'arabidopsis', 'solanum', 'tobacco', 'tomato', 'maize'])
                
                if is_plant and study_id and study_id not in [s.get('STUDY_ID') for s in matched_studies]:
                    matched_studies.append({
                        'study_id': study_id,
                        'title': title,
                        'abstract': abstract,
                        'source': 'Metabolomics Workbench',
                        'keywords_matched': [keyword]
                    })
                    
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error searching for keyword '{keyword}': {e}")
            continue
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error for keyword '{keyword}': {e}")
            continue
        
        # Rate limiting
        time.sleep(1)
    
    logger.info(f"Found {len(matched_studies)} potential studies from Metabolomics Workbench.")
    return matched_studies

def validate_studies(session: requests.Session, studies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validate that studies contain sample-level data suitable for pairing.
    
    Args:
        session: Requests session
        studies: List of study metadata
        
    Returns:
        Filtered list of studies with valid sample data
    """
    valid_studies = []
    
    for study in studies:
        study_id = study.get('study_id')
        if not study_id:
            continue
            
        try:
            # Fetch sample summary to check if samples exist
            sample_url = METABOLOMICS_WORKBENCH_SAMPLE_URL.replace("STUDY_ID", study_id)
            response = session.get(sample_url, timeout=30)
            
            if response.status_code == 200:
                sample_data = response.json()
                samples = sample_data if isinstance(sample_data, list) else sample_data.get('samples', [])
                
                if len(samples) > 0:
                    study['sample_count'] = len(samples)
                    study['samples'] = samples # Store sample metadata for later pairing
                    valid_studies.append(study)
                    logger.info(f"Validated study {study_id} with {len(samples)} samples.")
                else:
                    logger.warning(f"Study {study_id} has no samples.")
            else:
                logger.warning(f"Could not retrieve samples for study {study_id}: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"Error validating study {study_id}: {e}")
            continue
            
    return valid_studies

def save_search_results(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save search results to a JSON file.
    
    Args:
        results: List of study dictionaries
        output_path: Path to output file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved search results to {output_path}")

def main():
    """Main entry point for searching Metabolomics Workbench."""
    logger.info("Starting Metabolomics Workbench search for defense metabolites.")
    
    try:
        session = create_session()
        
        # Search for relevant studies
        results = search_metabolomics_workbench(session, DEFENSE_KEYWORDS)
        
        # Validate results
        valid_results = validate_studies(session, results)
        
        if not valid_results:
            logger.warning("No valid plant defense metabolite studies found on Metabolomics Workbench.")
            # Save empty results or a specific marker
            save_search_results([], PROJECT_ROOT / 'data' / 'raw' / 'metabolomics_search_results.json')
            return
        
        # Save valid results
        output_file = PROJECT_ROOT / 'data' / 'raw' / 'metabolomics_search_results.json'
        save_search_results(valid_results, output_file)
        
        logger.info(f"Successfully identified {len(valid_results)} studies for further processing.")
        
    except Exception as e:
        logger.error(f"Critical error in Metabolomics Workbench search: {e}")
        raise_dataset_error(f"Failed to search Metabolomics Workbench: {e}")

if __name__ == "__main__":
    main()
