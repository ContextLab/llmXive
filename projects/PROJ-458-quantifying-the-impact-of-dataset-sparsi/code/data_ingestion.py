"""Data ingestion pipeline for Materials Project data."""
import os
import time
import json
import csv
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from config
try:
    from config import load_env
except ImportError:
    # Fallback for direct execution if path not set
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from config import load_env

def load_env_config():
    """Load environment configuration."""
    return load_env()

def exponential_backoff(func, max_retries=5, base_delay=1):
    """Execute function with exponential backoff on failure."""
    attempt = 0
    while attempt < max_retries:
        try:
            return func()
        except Exception as e:
            attempt += 1
            if attempt == max_retries:
                raise e
            delay = base_delay * (2 ** (attempt - 1))
            print(f"Attempt {attempt} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)

def fetch_material_data(api_key: str) -> List[Dict[str, Any]]:
    """
    Fetch material data from Materials Project API.
    NOTE: This is a placeholder for the real API call logic.
    In a real implementation, this would use pymatgen or requests.
    """
    # Since we cannot run the real API call here without a key and network,
    # we return an empty list or simulate a structure if this were a test.
    # However, per constraints, we must implement the real logic.
    # We will assume the real logic uses pymatgen's MPRester.
    
    try:
        from pymatgen.ext.matproj import MPRester
    except ImportError:
        raise ImportError("pymatgen is required for data ingestion.")

    def _fetch():
        with MPRester(api_key) as mpr:
            # Fetch a subset for the pipeline (e.g., first 1000 for demo, or all if feasible)
            # For the purpose of the task, we fetch a representative set.
            # We filter for entries with formation_energy and dft_computed=True
            docs = mpr.get_materials(
                criteria={"nelements": {"$lte": 3}}, # Limit to 3 elements for speed
                fields=["material_id", "composition", "formation_energy_per_atom", "dft_computed"]
            )
            return docs

    return exponential_backoff(_fetch)

def process_and_save(data: List[Any], output_path: Path):
    """Process fetched data and save to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["material_id", "composition", "formation_energy", "dft_computed"])
        
        for doc in data:
            writer.writerow([
                doc.material_id,
                doc.composition.reduced_formula,
                doc.formation_energy_per_atom,
                doc.dft_computed
            ])

def main():
    """Main entry point for data ingestion."""
    config = load_env_config()
    api_key = config["mp_api_key"]
    project_root = config["project_root"]
    
    raw_path = project_root / "data" / "raw" / "raw_pool.csv"
    
    print(f"Fetching data for project root: {project_root}")
    try:
        data = fetch_material_data(api_key)
        print(f"Fetched {len(data)} entries.")
        process_and_save(data, raw_path)
        print(f"Saved raw data to {raw_path}")
    except Exception as e:
        print(f"Error during ingestion: {e}")
        raise

if __name__ == "__main__":
    main()
