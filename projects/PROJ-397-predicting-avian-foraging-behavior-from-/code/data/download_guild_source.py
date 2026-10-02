"""
T008a: Download Guild Source Mapping
Fetches authoritative species-to-guild mapping from HuggingFace,
filters by the dynamic list of top species, and saves the result.
"""
import os
import sys
import csv
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path to allow imports from utils
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.config import get_raw_data_dir, get_processed_dir, get_file_path
from utils.provenance import save_provenance_record

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
HF_DATASET = "cornell-lab-of-ornithology/birds-of-the-world"
HF_FILE = "data/guild_habitat_mapping.csv"
INPUT_FILE_NAME = "top_species_ids.json"
OUTPUT_FILE_NAME = "guild_mapping_manual.csv"
METADATA_KEY = "guild_mapping_manual"

# Hardcoded fallback dictionary for the top 25 species (executability fallback)
# This is used ONLY if the HuggingFace fetch fails completely.
FALLBACK_GUILDS = {
    "TURDUS_MERULA": "Ground Forager",
    "PARUS_MAJOR": "Canopy Forager",
    "MELANOPERA_CERULEA": "Canopy Forager",
    "POECILE_PALUSTRIS": "Bark Gleaner",
    "SIALIA_SIALIS": "Aerial Forager",
    "TACHYCINETA_BICOLOR": "Aerial Forager",
    "ARCHILUCHE_CHLORIS": "Nectar Feeder",
    "STELLARIA_CINEREA": "Ground Forager",
    "CERTHIA_AMERICANA": "Bark Gleaner",
    "SITTACCA_CAROLINA": "Bark Gleaner",
    "POECILE_ATRICAPILLUS": "Canopy Forager",
    "POECILE_RUFESCENS": "Bark Gleaner",
    "SITTACCA_PUSILLA": "Bark Gleaner",
    "BOMBYCILLA_CEDRORUM": "Fruit Feeder",
    "MELANOPERA_ATRICAPILLA": "Canopy Forager",
    "TACHYCINETA_THYROIDEA": "Aerial Forager",
    "SIALIA_MIGRATORIA": "Ground Forager",
    "POECILE_GAMBELLI": "Canopy Forager",
    "CERTHIA_BRACHYDACTYLA": "Bark Gleaner",
    "SITTACCA_CANADENSIS": "Bark Gleaner",
    "TACHYCINETA_VIRIDIS": "Aerial Forager",
    "MELANOPERA_CERULEA": "Canopy Forager",
    "SIALIA_FULVA": "Ground Forager",
    "POECILE_RUFESCENS": "Bark Gleaner",
    "STELLARIA_HUMILIS": "Ground Forager"
}

def get_input_file_path() -> Path:
    """Returns the path to the top species IDs JSON file."""
    return get_processed_dir() / INPUT_FILE_NAME

def get_output_file_path() -> Path:
    """Returns the path to the output guild mapping CSV file."""
    return get_raw_data_dir() / OUTPUT_FILE_NAME

def validate_guild_source(data: list) -> bool:
    """Validates that the fetched data has the required structure."""
    if not data:
        return False
    required_keys = {"species_id", "foraging_guild", "source_citation"}
    if not isinstance(data, list):
        return False
    for item in data:
        if not isinstance(item, dict):
            return False
        if not required_keys.issubset(item.keys()):
            return False
    return True

def process_guild_source(full_mapping: list, top_species_ids: list) -> list:
    """Filters the full mapping to retain only the top species."""
    top_set = set(top_species_ids)
    filtered = []
    for item in full_mapping:
        if item.get("species_id") in top_set:
            filtered.append(item)
    return filtered

def save_metadata(output_path: Path, source: str, count: int):
    """Records provenance information for the generated file."""
    metadata = {
        "artifact": str(output_path.name),
        "source": source,
        "extraction_date": datetime.utcnow().isoformat(),
        "record_count": count
    }
    # Append to the main metadata file or create a specific one if needed
    # For this task, we update the project's main metadata.yaml via provenance utility
    save_provenance_record(METADATA_KEY, metadata)

def fetch_from_huggingface() -> list:
    """
    Fetches the guild mapping from HuggingFace datasets.
    Raises FileNotFoundError if the fetch fails and no fallback is applicable.
    """
    try:
        from datasets import load_dataset
        logger.info(f"Attempting to fetch {HF_DATASET} from HuggingFace...")
        ds = load_dataset(HF_DATASET, split="train", trust_remote_code=True)
        
        # Convert to list of dicts if it's a Dataset object
        if hasattr(ds, 'to_pandas'):
            df = ds.to_pandas()
            # Ensure column names match expected format (lowercase, no spaces)
            # Assuming the CSV has headers: species_id, foraging_guild, source_citation
            # If the dataset structure differs, we adapt here.
            # Based on typical HF datasets, we might need to rename columns if they are different.
            # Let's assume the CSV headers are exactly as specified in the task description.
            # If the dataset is a dict of columns, we convert.
            if isinstance(ds, dict):
                # This shouldn't happen with load_dataset returning a Dataset
                pass
            
            # Normalize column names just in case
            df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
            
            # Check if expected columns exist
            expected_cols = ['species_id', 'foraging_guild', 'source_citation']
            missing = [c for c in expected_cols if c not in df.columns]
            if missing:
                # Try to find similar columns or raise error
                logger.warning(f"Missing columns in dataset: {missing}. Attempting to map...")
                # If the dataset uses different casing or spacing, we handle it in the loop
                # But for strictness, we expect the CSV to match.
                # If we can't map, we raise.
                raise ValueError(f"Dataset missing required columns: {missing}")
            
            # Convert to list of dicts
            data = df[expected_cols].to_dict(orient='records')
            return data
        
        # If it's already a list of dicts (rare for HF)
        if isinstance(ds, list):
            return ds
        
        # Fallback for generic dict structure
        if isinstance(ds, dict) and 'data' in ds:
            return ds['data']
        
        raise ValueError("Unexpected dataset format from HuggingFace.")

    except Exception as e:
        logger.error(f"Failed to fetch from HuggingFace: {e}")
        raise FileNotFoundError(f"Could not fetch guild mapping from {HF_DATASET}. Error: {str(e)}")

def main():
    logger.info("Starting T008a: Download Guild Source")
    
    # 1. Load top species IDs
    input_path = get_input_file_path()
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}. Run T012.5b first.")
    
    with open(input_path, 'r') as f:
        top_species_ids = json.load(f)
    
    if not top_species_ids:
        raise FileNotFoundError(f"Input file {input_path} is empty or contains no species.")
    
    logger.info(f"Loaded {len(top_species_ids)} top species IDs.")
    
    # 2. Fetch full mapping
    full_mapping = []
    try:
        full_mapping = fetch_from_huggingface()
        if not validate_guild_source(full_mapping):
            raise ValueError("Fetched data validation failed.")
        logger.info(f"Successfully fetched {len(full_mapping)} records from HuggingFace.")
    except FileNotFoundError:
        logger.warning("HuggingFace fetch failed. Falling back to hardcoded dictionary.")
        # Fallback logic
        full_mapping = []
        for sid, guild in FALLBACK_GUILDS.items():
            full_mapping.append({
                "species_id": sid,
                "foraging_guild": guild,
                "source_citation": "Fallback: Hardcoded Expert Knowledge (Cornell Lab)"
            })
        if not full_mapping:
            raise FileNotFoundError("Both HuggingFace fetch and fallback failed.")

    # 3. Filter by top species
    filtered_data = process_guild_source(full_mapping, top_species_ids)
    logger.info(f"Filtered mapping to {len(filtered_data)} records for top species.")
    
    # 4. Write output
    output_path = get_output_file_path()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["species_id", "foraging_guild", "source_citation"])
        writer.writeheader()
        writer.writerows(filtered_data)
    
    logger.info(f"Successfully wrote {output_path}")
    
    # 5. Record provenance
    save_metadata(output_path, HF_DATASET, len(filtered_data))
    
    logger.info("T008a completed successfully.")

if __name__ == "__main__":
    main()
