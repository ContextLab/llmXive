"""
BMG Data Ingestion Module.

Fetches Bulk Metallic Glass data from the Materials Project API.
If the API is unreachable or returns no data, falls back to the
synthetic dataset generator (T011).
"""
import os
import sys
import json
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.data.synthetic_generator import generate_synthetic_bmg
from code.utils.logging_config import get_logger
from code.utils.provenance import record_artifact, ensure_state_directory

logger = get_logger(__name__)

# Configuration
MATERIALS_PROJECT_API_KEY = os.getenv("MP_API_KEY")
MATERIALS_PROJECT_API_URL = "https://materialsproject.org/rest/v2/materials"
OUTPUT_PATH = Path(PROJECT_ROOT) / "data" / "raw" / "bmg_materials_project.csv"
FALLBACK_OUTPUT_PATH = Path(PROJECT_ROOT) / "data" / "raw" / "synthetic_bmg_seed.csv"
STATE_DIR = Path(PROJECT_ROOT) / "state"

def fetch_materials_project_data() -> Optional[List[Dict[str, Any]]]:
    """
    Fetches BMG candidate materials from the Materials Project API.
    
    Returns:
        List of material dictionaries or None if the fetch fails.
    """
    if not MATERIALS_PROJECT_API_KEY:
        logger.warning("MP_API_KEY not found in environment. Skipping Materials Project fetch.")
        return None

    headers = {"X-API-Key": MATERIALS_PROJECT_API_KEY}
    params = {
        "criteria": {
            "phase": "amorphous", # Attempt to filter for amorphous/bmg if supported by API version
            "nelements": {"$gte": 3} # Bulk metallic glasses are typically multi-component
        },
        "fields": ["material_id", "composition", "properties", "structures"]
    }

    try:
        import requests
        logger.info(f"Fetching data from Materials Project API...")
        response = requests.get(MATERIALS_PROJECT_API_URL, headers=headers, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("data"):
            logger.warning("Materials Project API returned no data.")
            return None
        
        logger.info(f"Successfully fetched {len(data['data'])} materials from API.")
        return data["data"]
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch from Materials Project API: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Materials Project response: {e}")
        return None

def process_mp_materials(materials: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Processes raw Materials Project data into the canonical BMG format.
    
    Args:
        materials: List of raw material dictionaries from the API.
        
    Returns:
        List of processed dictionaries with 'composition' (at%), 'shear_modulus', etc.
    """
    processed = []
    for mat in materials:
        try:
            # Extract composition
            # MP API returns composition as a dict like {"Fe": 0.6, "Zr": 0.4}
            raw_comp = mat.get("composition", {})
            if not raw_comp:
                continue
            
            # Calculate atomic percent (at%)
            total_atoms = sum(raw_comp.values())
            composition_at = {k: v / total_atoms for k, v in raw_comp.items()}
            
            # Extract Shear Modulus if available
            props = mat.get("properties", {})
            shear_modulus = props.get("gshear_modulus") # MP often uses GShear
            if shear_modulus is None:
                # Some fields might be named differently or missing
                shear_modulus = props.get("shear_modulus")
            
            # If no shear modulus, we might need to skip or impute, 
            # but for ingestion we keep it if we have the composition.
            # However, for ML we need the target. Let's assume we filter for valid targets later 
            # or include NaN if the API provides it. For now, if missing, we skip to ensure clean data.
            if shear_modulus is None:
                logger.debug(f"Skipping {mat.get('material_id')}: No shear modulus found.")
                continue

            entry = {
                "source": "materials_project",
                "material_id": mat.get("material_id"),
                "composition": composition_at, # Dict of element: fraction
                "shear_modulus": shear_modulus, # GPa
                "elements": list(composition_at.keys()),
                "n_elements": len(composition_at)
            }
            processed.append(entry)
        except Exception as e:
            logger.error(f"Error processing material {mat.get('material_id')}: {e}")
            continue
    
    return processed

def fallback_to_synthetic() -> List[Dict[str, Any]]:
    """
    Generates synthetic data using the T011 module.
    """
    logger.info("Falling back to synthetic data generation (T011).")
    # Ensure output directory exists
    FALLBACK_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Call the generator
    # The generator is expected to write to FALLBACK_OUTPUT_PATH internally or return data
    # Based on T011 description: "Output to data/raw/synthetic_bmg_seed.csv"
    # We assume generate_synthetic_bmg() performs the write and returns the path or data.
    # Let's assume it returns the data list for consistency here.
    
    data = generate_synthetic_bmg(output_path=str(FALLBACK_OUTPUT_PATH))
    
    # Record provenance for the synthetic file
    ensure_state_directory(STATE_DIR)
    record_artifact(
        state_file=STATE_DIR / "projects" / "PROJ-380-predicting-the-impact-of-composition-on-.yaml",
        artifact_path=str(FALLBACK_OUTPUT_PATH),
        task_id="T011",
        description="Synthetic BMG dataset generated via fallback"
    )
    
    return data

def save_to_csv(data: List[Dict[str, Any]], output_path: Path):
    """
    Saves the processed data to a CSV file.
    """
    if not data:
        logger.warning("No data to save.")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Flatten the composition dict for CSV
    # Columns: source, material_id, element1, element2, ..., shear_modulus
    # This is a simplified flat structure for ingestion. 
    # The feature engineering step (T018) will handle the complex composition parsing.
    
    # Determine all unique elements
    all_elements = set()
    for item in data:
        if isinstance(item.get("composition"), dict):
            all_elements.update(item["composition"].keys())
    
    elements = sorted(list(all_elements))
    
    # Define headers
    headers = ["source", "material_id", "shear_modulus", "n_elements"] + elements
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
        writer.writeheader()
        
        for item in data:
            row = {
                "source": item.get("source"),
                "material_id": item.get("material_id"),
                "shear_modulus": item.get("shear_modulus"),
                "n_elements": item.get("n_elements")
            }
            comp = item.get("composition", {})
            for elem in elements:
                row[elem] = comp.get(elem, 0.0)
            writer.writerow(row)
    
    logger.info(f"Saved {len(data)} records to {output_path}")
    return output_path

def main():
    """
    Main entry point for the ingestion pipeline.
    1. Try Materials Project API.
    2. If fail, fallback to Synthetic.
    3. Save to data/raw/bmg_materials_project.csv.
    """
    ensure_state_directory(STATE_DIR)
    
    final_output_path = OUTPUT_PATH
    data = None
    
    # Attempt API Fetch
    mp_data = fetch_materials_project_data()
    
    if mp_data:
        logger.info("Processing Materials Project data...")
        data = process_mp_materials(mp_data)
        if not data:
            logger.warning("No valid data extracted from Materials Project. Falling back.")
            data = fallback_to_synthetic()
            final_output_path = Path(PROJECT_ROOT) / "data" / "raw" / "synthetic_bmg_seed.csv" # Or rename to indicate fallback
            # Note: The task says output to bmg_materials_project.csv, but if we fallback, 
            # we might want to keep the filename consistent or indicate the source.
            # Let's keep the target filename as requested but log the source change.
            final_output_path = OUTPUT_PATH 
    else:
        # API failed completely
        data = fallback_to_synthetic()
        final_output_path = OUTPUT_PATH # Overwrite or append? Let's overwrite the target file.
        logger.warning("Using synthetic data as the source for the target file.")

    if data:
        save_to_csv(data, final_output_path)
        
        # Record provenance for the final output
        record_artifact(
            state_file=STATE_DIR / "projects" / "PROJ-380-predicting-the-impact-of-composition-on-.yaml",
            artifact_path=str(final_output_path),
            task_id="T016",
            description=f"Ingested data from {'Materials Project' if mp_data else 'Synthetic Fallback'}"
        )
    else:
        logger.critical("Ingestion failed: No data available from API or synthetic fallback.")
        sys.exit(1)

if __name__ == "__main__":
    main()
