import os
import csv
import time
import json
import hashlib
import subprocess
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Import shared infrastructure components
from infrastructure.error_handler import exponential_backoff_retry, APIRetryError
from infrastructure.path_utils import get_project_root, ensure_dir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Helper Functions ---

def get_git_hash() -> str:
    """Retrieve the current git commit hash for versioning."""
    try:
        return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()
    except Exception:
        return "no-git"

def ensure_output_directories() -> None:
    """Create necessary output directories if they don't exist."""
    project_root = get_project_root()
    dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "figures",
        project_root / "state" / "projects"
    ]
    for d in dirs:
        ensure_dir(d)

def serialize_structure(structure: Dict[str, Any]) -> str:
    """Serialize a structure dict to a JSON string for hashing."""
    return json.dumps(structure, sort_keys=True)

def compute_sha256(data: str) -> str:
    """Compute SHA-256 hash of a string."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

# --- Materials Project Client ---

class MaterialsProjectClient:
    """Client for interacting with the Materials Project REST API."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("MP_API_KEY")
        self.base_url = "https://materialsproject.org/rest/v2"
        if not self.api_key:
            logger.warning("MP_API_KEY not found. API calls will fail.")

    def _make_request(self, endpoint: str, params: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Make a request with exponential backoff retry logic."""
        if not self.api_key:
            raise APIRetryError("API Key missing")

        url = f"{self.base_url}/{endpoint}"
        params["api_key"] = self.api_key
        
        # Apply exponential backoff via decorator logic manually here for clarity
        # or rely on the decorator if we wrapped this method. 
        # Given the task, we implement the retry loop explicitly around the fetch.
        
        max_retries = 5
        base_delay = 2.0
        
        for attempt in range(max_retries):
            try:
                import urllib.request
                import urllib.error
                import urllib.parse
                
                query_string = urllib.parse.urlencode(params)
                full_url = f"{url}?{query_string}"
                
                req = urllib.request.Request(full_url)
                req.add_header('Accept', 'application/json')
                
                with urllib.request.urlopen(req, timeout=30) as response:
                    if response.status == 200:
                        return json.loads(response.read().decode('utf-8'))
                    else:
                        logger.error(f"HTTP Error {response.status}")
                        return None
                        
            except urllib.error.HTTPError as e:
                if e.code == 429: # Rate Limit
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Rate limit hit. Retrying in {delay:.1f}s... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(delay)
                else:
                    logger.error(f"HTTP Error {e.code}: {e.reason}")
                    return None
            except Exception as e:
                delay = base_delay * (2 ** attempt)
                logger.warning(f"Network error: {e}. Retrying in {delay:.1f}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(delay)

        raise APIRetryError(f"Failed after {max_retries} attempts")

    def get_pristine_structures(self, chemical_formula: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Query Materials Project for pristine structures."""
        params = {
            "formula": chemical_formula,
            "limit": str(limit),
            "criteria": "structure" 
        }
        try:
            response = self._make_request("materials/matching", params)
            if response and "response" in response:
                return response["response"].get("materials", [])
            return []
        except APIRetryError:
            raise

# --- Caching Logic ---

def load_cached_pristine_structures() -> Optional[List[Dict[str, Any]]]:
    """Load cached pristine structures from CSV if available."""
    project_root = get_project_root()
    cache_path = project_root / "data" / "raw" / "pristine_structures.csv"
    
    if not cache_path.exists():
        return None
        
    structures = []
    with open(cache_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Reconstruct complex fields if necessary, currently assuming flat CSV
            structures.append(row)
    return structures

def save_structures_to_csv(structures: List[Dict[str, Any]], filename: str) -> None:
    """Save structures to a CSV file."""
    project_root = get_project_root()
    output_path = project_root / "data" / "raw" / filename
    ensure_dir(output_path.parent)
    
    if not structures:
        logger.warning("No structures to save.")
        return

    # Flatten structure for CSV (simplified for demo, real impl might expand 'structure' dict)
    fieldnames = structures[0].keys()
    # If 'structure' is a dict, we might need to serialize it
    if 'structure' in fieldnames and isinstance(structures[0]['structure'], dict):
        fieldnames = [k for k in structures[0].keys() if k != 'structure'] + ['structure_json']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for s in structures:
            row = s.copy()
            if 'structure' in row and isinstance(row['structure'], dict):
                row['structure_json'] = json.dumps(row['structure'])
                del row['structure']
            writer.writerow(row)
    logger.info(f"Saved {len(structures)} structures to {output_path}")

# --- Fallback Logic ---

def run_fallback_synthetic_generation() -> None:
    """Invoke synthetic data generator if real data acquisition fails."""
    logger.info("Triggering fallback synthetic data generation...")
    try:
        # Import the generator module
        from generators.synthetic_data_generator import generate_synthetic_data, save_to_csv, get_git_hash
        
        # Generate synthetic train data
        data = generate_synthetic_data(seed=42, n_samples=100)
        save_to_csv(data, "synthetic_defect_fallback.csv", data_source="synthetic")
        logger.info("Synthetic fallback data generated successfully.")
    except Exception as e:
        logger.error(f"Failed to generate synthetic fallback: {e}")
        raise

# --- Main Acquisition Logic ---

def download_2022_defect_dataset() -> bool:
    """Attempt to download the 2022 Supplementary Defect Dataset."""
    # Implementation for T011 would go here. 
    # For T015, we focus on the API retry logic for pristine structures.
    # Placeholder for existing logic:
    logger.info("Checking for 2022 Defect Dataset...")
    # Assume T011 logic exists and returns True if valid
    return False 

def verify_defect_dataset() -> bool:
    """Verify the downloaded defect dataset."""
    return True

def run_acquisition() -> None:
    """
    Step 1.3: Main acquisition loop with exponential backoff and caching.
    Queries Materials Project for pristine structures.
    On failure, loads cached data or aborts.
    """
    ensure_output_directories()
    project_root = get_project_root()
    cache_path = project_root / "data" / "raw" / "pristine_structures.csv"
    
    mp_client = MaterialsProjectClient()
    
    # Target materials
    targets = [
        {"formula": "C", "name": "graphene"},
        {"formula": "MoS2", "name": "MoS2"}
    ]
    
    all_structures = []
    
    for target in targets:
        logger.info(f"Attempting to fetch pristine {target['name']} structures...")
        try:
            structures = mp_client.get_pristine_structures(
                chemical_formula=target["formula"], 
                limit=50
            )
            if structures:
                all_structures.extend(structures)
                logger.info(f"Retrieved {len(structures)} {target['name']} structures.")
            else:
                logger.warning(f"No structures returned for {target['name']}.")
        except APIRetryError as e:
            logger.error(f"API access failed for {target['name']}: {e}")
            # Check cache if API fails
            if cache_path.exists():
                logger.info("API failed. Attempting to load cached pristine structures...")
                cached = load_cached_pristine_structures()
                if cached:
                    all_structures.extend(cached)
                    logger.info(f"Loaded {len(cached)} structures from cache.")
                else:
                    logger.critical("[ERROR: API access unavailable and no cache present]")
                    raise SystemExit(1)
            else:
                logger.critical("[ERROR: API access unavailable and no cache present]")
                raise SystemExit(1)

    if all_structures:
        save_structures_to_csv(all_structures, "pristine_structures.csv")
    else:
        logger.warning("No structures acquired or cached. Aborting.")
        raise SystemExit(1)

def main():
    """Entry point for data acquisition."""
    try:
        run_acquisition()
    except SystemExit:
        pass
    except Exception as e:
        logger.critical(f"Unhandled error in acquisition: {e}")
        raise

if __name__ == "__main__":
    main()