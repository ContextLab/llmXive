"""Data extraction logic for Materials Project and NIST."""
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import joblib
import pandas as pd
from datasets import load_dataset
from config import get_config

logger = logging.getLogger(__name__)

# Caching setup
config = get_config()
cache_memory = joblib.Memory(location=str(config.cache_dir), verbose=0)

@cache_memory.cache
def fetch_materials_project_data() -> Optional[List[Dict[str, Any]]]:
    """Fetch data from Materials Project API."""
    mp_api_key = os.environ.get("MP_API_KEY")
    if not mp_api_key:
        logger.warning("MP_API_KEY not found in environment. Skipping Materials Project fetch.")
        return None
    
    try:
        from mp_api.client import MPRester
        with MPRester(mp_api_key) as mpr:
            # Query for Al alloys with Poisson's ratio and Young's modulus
            docs = mpr.materials.search(
                elements=["Al"],
                property_ids=["poisson_ratio", "young_modulus"],
                num_chunks=1000  # Limit for safety
            )
            
            records = []
            for doc in docs:
                record = {
                    "material_id": doc.material_id,
                    "poisson_ratio": doc.poisson_ratio,
                    "young_modulus": doc.young_modulus,
                    "composition": doc.composition,
                    "source": "Materials Project",
                    "measurement_method": "Direct"  # MP typically uses DFT
                }
                records.append(record)
            return records
    except Exception as e:
        logger.error(f"Failed to fetch from Materials Project: {e}")
        return None

@cache_memory.cache
def fetch_nist_data() -> Optional[List[Dict[str, Any]]]:
    """Fetch data from NIST materials dataset."""
    try:
        # Try loading the NIST dataset
        dataset = load_dataset("nist_materials_data", split="train")
        
        records = []
        for item in dataset:
            # Map NIST fields to our schema
            record = {
                "material_id": item.get("material_id", f"nist_{item.get('id', '')}"),
                "poisson_ratio": item.get("poisson_ratio"),
                "young_modulus": item.get("young_modulus"),
                "composition": item.get("composition", {}),
                "source": "NIST",
                "measurement_method": item.get("measurement_method", "Ultrasonic")
            }
            # Skip if essential fields are missing
            if record["poisson_ratio"] is None or record["young_modulus"] is None:
                continue
            records.append(record)
        
        return records
    except Exception as e:
        logger.error(f"Failed to fetch from NIST: {e}")
        return None

def run_extraction(output_path: Path) -> Dict[str, Any]:
    """Run the full extraction pipeline from all sources."""
    logger.info("Starting data extraction")
    
    all_records = []
    source_counts = {}
    
    # Try Materials Project first
    mp_data = fetch_materials_project_data()
    if mp_data:
        all_records.extend(mp_data)
        source_counts["Materials Project"] = len(mp_data)
        logger.info(f"Retrieved {len(mp_data)} records from Materials Project")
    else:
        logger.warning("No data from Materials Project")
    
    # Try NIST as fallback/secondary source
    nist_data = fetch_nist_data()
    if nist_data:
        all_records.extend(nist_data)
        source_counts["NIST"] = len(nist_data)
        logger.info(f"Retrieved {len(nist_data)} records from NIST")
    else:
        logger.warning("No data from NIST")
    
    if not all_records:
        raise RuntimeError("CRITICAL: No valid data found in MP or NIST.")
    
    # Convert to DataFrame and save
    df = pd.DataFrame(all_records)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    
    result = {
        "total_records": len(all_records),
        "source_counts": source_counts,
        "output_path": str(output_path)
    }
    
    logger.info(f"Extraction complete. Total records: {len(all_records)}")
    return result

def main():
    """Main entry point for data extraction."""
    config = get_config()
    output_path = config.data_raw_dir / "alloys_raw.parquet"
    result = run_extraction(output_path)
    print(f"Extraction complete: {result}")

if __name__ == "__main__":
    main()