import json
import logging
import time
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from config import get_env, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MIN_VALID_DATASETS = 3
OUTPUT_STATUS_FILE = "output/discovery_status.json"
OUTPUT_RESULTS_FILE = "output/discovery_results.json"
VERIFIED_DATASETS_FILE = "data/verified_datasets.yaml"

def load_verified_datasets(filepath: Optional[str] = None) -> Dict[str, Any]:
    """Load the verified datasets registry."""
    if filepath is None:
        filepath = VERIFIED_DATASETS_FILE
    path = Path(filepath)
    if not path.exists():
        logger.warning(f"Verified datasets file not found: {filepath}. Returning empty registry.")
        return {"verified_accessions": []}
    
    # Simple YAML-like parser for the specific format expected in data/verified_datasets.yaml
    # Expected format:
    # verified_accessions:
    #   - accession: GSE12345
    #     title: "Some Title"
    #   - ...
    verified = []
    try:
        with open(path, 'r') as f:
            content = f.read()
            # Basic parsing logic
            in_list = False
            current_entry = {}
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith("verified_accessions:"):
                    in_list = True
                    continue
                if not in_list:
                    continue
                if line.startswith("- accession:"):
                    if current_entry:
                        verified.append(current_entry)
                    current_entry = {"accession": line.split(":", 1)[1].strip()}
                elif line.startswith("title:") and current_entry:
                    # Remove quotes if present
                    title = line.split(":", 1)[1].strip().strip('"').strip("'")
                    current_entry["title"] = title
            if current_entry:
                verified.append(current_entry)
    except Exception as e:
        logger.error(f"Error parsing verified datasets: {e}")
        return {"verified_accessions": []}
    
    return {"verified_accessions": verified}

def save_verified_dataset(filepath: str, data: Dict[str, Any]) -> None:
    """Save verified datasets to file."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        f.write("verified_accessions:\n")
        for item in data.get("verified_accessions", []):
            f.write(f"  - accession: {item.get('accession', '')}\n")
            f.write(f"    title: \"{item.get('title', '')}\"\n")

def tokenize_title(title: str) -> List[str]:
    """Convert title to lowercase tokens."""
    return re.findall(r'\w+', title.lower())

def calculate_token_overlap(tokens_a: List[str], tokens_b: List[str]) -> float:
    """Calculate Jaccard-like overlap or simple intersection ratio."""
    if not tokens_a or not tokens_b:
        return 0.0
    set_a = set(tokens_a)
    set_b = set(tokens_b)
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    if union == 0:
        return 0.0
    return intersection / union

def validate_reference(accession: str, title: str, threshold: float = 0.7) -> bool:
    """
    Validate a dataset reference against the verified registry.
    Returns True if the title token overlap with any verified entry >= threshold.
    """
    registry = load_verified_datasets()
    tokens_query = tokenize_title(title)
    
    for entry in registry.get("verified_accessions", []):
        if entry.get("accession") == accession:
            # Exact accession match is strong, but we still check title overlap per spec
            title_verified = entry.get("title", "")
            tokens_verified = tokenize_title(title_verified)
            overlap = calculate_token_overlap(tokens_query, tokens_verified)
            if overlap >= threshold:
                return True
    return False

def search_geo(query: str) -> List[Dict[str, Any]]:
    """
    Simulate a GEO search. In a real implementation, this would use GEOparse or requests.
    For this task, we assume the discovery logic has already populated a cache or
    the search function returns a list of candidates found in a local index.
    Since T009 ran search_geo, we assume a local cache exists or we simulate
    the structure of what would be returned.
    
    To satisfy "Real data only", we will attempt to fetch from a real source if possible,
    but for the specific T012 logic, we rely on the input list `datasets` passed to run_discovery.
    Here we provide a stub that returns an empty list if no local cache is found,
    forcing the caller to use the data already discovered.
    """
    # In a full pipeline, this would hit the NCBI E-utilities API.
    # For T012 implementation, we assume the list of datasets is passed in or
    # retrieved from a previous step's output (T009 output).
    return []

def search_encode(query: str) -> List[Dict[str, Any]]:
    """Simulate ENCODE search."""
    return []

def validate_dataset(dataset: Dict[str, Any]) -> bool:
    """
    Check if a dataset has the required keys: accession, title, organism, metadata.
    """
    required = ["accession", "title", "organism", "metadata"]
    return all(k in dataset for k in required)

def filter_by_organism(datasets: List[Dict[str, Any]], organisms: List[str]) -> List[Dict[str, Any]]:
    """Filter datasets by allowed organisms."""
    return [d for d in datasets if d.get("organism", "").lower() in [o.lower() for o in organisms]]

def check_metadata_completeness(dataset: Dict[str, Any]) -> bool:
    """
    Check for metadata completeness: fluctuation timescale and amplitude.
    """
    meta = dataset.get("metadata", {})
    # Check for keys that might indicate fluctuation data
    keys = ["fluctuation_timescale", "fluctuation_period", "env_period", "amplitude"]
    found_keys = [k for k in keys if k in meta]
    return len(found_keys) >= 2  # Heuristic: need at least two indicators

def run_discovery(datasets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Main logic for T012:
    1. Filter datasets by organism and metadata completeness.
    2. Validate references against verified_datasets.yaml.
    3. Flag "Partial Match" datasets (valid organism/metadata but failed title validation).
    4. Count valid datasets.
    5. Write halt_signal to output/discovery_status.json if count < MIN_VALID_DATASETS.
    
    Returns a status dictionary.
    """
    logger.info(f"Running discovery validation on {len(datasets)} datasets.")
    
    allowed_organisms = ["mouse", "c. elegans", "drosophila"]
    valid_datasets = []
    partial_match_datasets = []
    
    for ds in datasets:
        if not validate_dataset(ds):
            continue
        
        # Filter by organism
        if not filter_by_organism([ds], allowed_organisms):
            continue
        
        # Check metadata completeness
        if not check_metadata_completeness(ds):
            continue
        
        # Validate reference (title overlap)
        accession = ds["accession"]
        title = ds["title"]
        is_valid = validate_reference(accession, title, threshold=0.7)
        
        if is_valid:
            valid_datasets.append(ds)
        else:
            # Flag as partial match
            partial_match_datasets.append({
                "accession": accession,
                "title": title,
                "reason": "Title validation failed (token overlap < 0.7)"
            })
    
    valid_count = len(valid_datasets)
    status = {
        "valid_datasets_count": valid_count,
        "valid_datasets": [d["accession"] for d in valid_datasets],
        "partial_match_datasets": partial_match_datasets,
        "partial_match_count": len(partial_match_datasets),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Determine if we need to halt
    if valid_count < MIN_VALID_DATASETS:
        status["halt_signal"] = True
        status["message"] = f"Insufficient valid datasets found ({valid_count} < {MIN_VALID_DATASETS}). Pipeline halted."
        logger.warning(status["message"])
    else:
        status["halt_signal"] = False
        status["message"] = f"Data availability confirmed. Found {valid_count} valid datasets."
        logger.info(status["message"])
    
    # Ensure output directory exists
    ensure_directories()
    
    # Write results to output/discovery_status.json
    output_path = Path(OUTPUT_STATUS_FILE)
    with open(output_path, 'w') as f:
        json.dump(status, f, indent=2)
    
    logger.info(f"Discovery status written to {OUTPUT_STATUS_FILE}")
    
    # Also update the discovery results file to include the partial matches info
    # (Optional, but good for traceability)
    results_path = Path(OUTPUT_RESULTS_FILE)
    if results_path.exists():
        try:
            with open(results_path, 'r') as f:
                existing_results = json.load(f)
            existing_results["discovery_status"] = status
            with open(results_path, 'w') as f:
                json.dump(existing_results, f, indent=2)
        except Exception as e:
            logger.error(f"Could not update discovery results file: {e}")
    
    return status

def main():
    """
    Entry point for T012.
    Since T009, T010, T011 are completed, we assume the datasets are available
    in a local cache or we need to re-run the search logic if no cache exists.
    
    For this implementation, we assume the datasets are passed via a local file
    generated by T009 (e.g., output/discovery_results.json) or we simulate the
    input list if we are running in isolation.
    
    In a real pipeline, T012 would be called after T009/T010/T011.
    Here, we load the results from T009's output if available.
    """
    results_file = Path(OUTPUT_RESULTS_FILE)
    datasets = []
    
    if results_file.exists():
        try:
            with open(results_file, 'r') as f:
                data = json.load(f)
                # The structure might vary, assume 'datasets' key or similar
                # If T009 output format is: {"datasets": [...]}
                if "datasets" in data:
                    datasets = data["datasets"]
                else:
                    # Fallback: try to find a list of dicts
                    for key, val in data.items():
                        if isinstance(val, list) and val and isinstance(val[0], dict):
                            datasets = val
                            break
        except Exception as e:
            logger.error(f"Error loading previous discovery results: {e}")
    else:
        logger.warning(f"Previous discovery results not found at {OUTPUT_RESULTS_FILE}. "
                       "Cannot run T012 validation. Please run T009 first.")
        # Create a status file indicating failure to run
        ensure_directories()
        status = {
            "valid_datasets_count": 0,
            "valid_datasets": [],
            "partial_match_datasets": [],
            "partial_match_count": 0,
            "halt_signal": True,
            "message": "Previous discovery results missing. Pipeline halted.",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(OUTPUT_STATUS_FILE, 'w') as f:
            json.dump(status, f, indent=2)
        return status

    return run_discovery(datasets)

if __name__ == "__main__":
    main()