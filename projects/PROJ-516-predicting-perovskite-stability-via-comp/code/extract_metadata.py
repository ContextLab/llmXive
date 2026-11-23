import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

from utils.uncertainty_parser import parse_temperature_precision
from utils.uncertainty_propagator import calculate_combined_uncertainty
from utils.state_manager import compute_sha256, update_artifact_state

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_merged_perovskites(merged_path: Path) -> pd.DataFrame:
    """Load the merged perovskite dataset."""
    if not merged_path.exists():
        raise FileNotFoundError(f"Merged dataset not found at {merged_path}")
    logger.info(f"Loading merged dataset from {merged_path}")
    df = pd.read_csv(merged_path)
    return df

def parse_source_metadata(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Parse source metadata from the DataFrame to extract TGA model and precision.
    Uses the utils.uncertainty_parser to extract temperature_precision.
    """
    metadata_entries = []
    
    # Ensure we have the necessary columns, or handle missing ones gracefully
    # The merged CSV should contain 'source_metadata' or similar JSON string column
    # based on T012c logic. If not, we attempt to infer from other columns or fail loudly.
    
    if 'source_metadata' in df.columns:
        for idx, row in df.iterrows():
            try:
                raw_meta = row['source_metadata']
                if pd.isna(raw_meta):
                    meta_dict = {}
                else:
                    meta_dict = json.loads(raw_meta) if isinstance(raw_meta, str) else raw_meta
                
                # Extract instrument model (common keys: 'instrument', 'tga_model', 'device')
                tga_model = meta_dict.get('tga_model') or meta_dict.get('instrument') or meta_dict.get('device', 'Unknown')
                
                # Extract temperature precision using the dedicated parser
                # parse_temperature_precision expects a value or string representation
                temp_prec_val = meta_dict.get('temperature_precision')
                precision, source = parse_temperature_precision(temp_prec_val)
                
                metadata_entries.append({
                    "formula": row.get('formula', f"row_{idx}"),
                    "source": row.get('source', 'unknown'),
                    "tga_model": tga_model,
                    "temperature_precision": precision,
                    "precision_source": source,
                    "raw_metadata": meta_dict
                })
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse metadata JSON for row {idx}: {e}")
                continue
            except Exception as e:
                logger.warning(f"Error processing metadata for row {idx}: {e}")
                continue
    else:
        # Fallback: If 'source_metadata' column is missing, we must fail loudly per constraints
        # as we cannot synthesize data.
        raise KeyError("Required column 'source_metadata' not found in merged dataset. "
                       "Cannot parse TGA instrument details without source metadata.")

    return metadata_entries

def process_metadata_entries(entries: List[Dict[str, Any]]) -> tuple[List[Dict], List[Dict]]:
    """
    Process metadata entries to generate structured metadata and uncertainty flags.
    Calculates combined uncertainty sigma using T043 logic.
    """
    structured_metadata = []
    uncertainty_flags = []
    
    for entry in entries:
        # Calculate combined uncertainty (sigma)
        # T043: calculate_combined_uncertainty(temperature_precision, experimental_error)
        # We assume experimental_error might be in raw_metadata if available, else 0
        exp_error = entry['raw_metadata'].get('experimental_error', 0.0)
        sigma = calculate_combined_uncertainty(entry['temperature_precision'], exp_error)
        
        meta_record = {
            "formula": entry["formula"],
            "source": entry["source"],
            "tga_model": entry["tga_model"],
            "temperature_precision": entry["temperature_precision"],
            "experimental_error": exp_error,
            "combined_sigma": sigma,
            "precision_source": entry["precision_source"]
        }
        structured_metadata.append(meta_record)
        
        flag_record = {
            "formula": entry["formula"],
            "has_explicit_precision": entry["precision_source"] == "explicit",
            "sigma": sigma,
            "weight": 1.0 / (sigma ** 2) if sigma > 0 else 0.0
        }
        uncertainty_flags.append(flag_record)
        
    return structured_metadata, uncertainty_flags

def generate_uncertainty_flags(metadata: List[Dict]) -> List[Dict]:
    """
    Generate a specific list of uncertainty flags based on processed metadata.
    This is a helper to ensure the flags file is strictly formatted.
    """
    flags = []
    for meta in metadata:
        flags.append({
            "formula": meta["formula"],
            "sigma": meta["combined_sigma"],
            "weight": 1.0 / (meta["combined_sigma"] ** 2) if meta["combined_sigma"] > 0 else 0.0,
            "precision_source": meta["precision_source"]
        })
    return flags

def validate_metadata_structure(metadata: List[Dict]) -> bool:
    """Validate that metadata entries have required fields."""
    required_keys = {"formula", "tga_model", "temperature_precision", "combined_sigma"}
    for entry in metadata:
        if not required_keys.issubset(entry.keys()):
            logger.error(f"Missing required keys in metadata entry: {entry}")
            return False
    return True

def main():
    """Main entry point for metadata extraction task T013."""
    base_path = Path(__file__).resolve().parent.parent
    data_raw_path = base_path / "data" / "raw"
    merged_file = data_raw_path / "perovskites_merged.csv"
    
    metadata_output = data_raw_path / "metadata.json"
    flags_output = data_raw_path / "uncertainty_flags.json"
    
    if not data_raw_path.exists():
        data_raw_path.mkdir(parents=True, exist_ok=True)
    
    try:
        df = load_merged_perovskites(merged_file)
        logger.info(f"Loaded {len(df)} rows from merged dataset.")
        
        raw_entries = parse_source_metadata(df)
        logger.info(f"Parsed {len(raw_entries)} metadata entries.")
        
        structured_meta, flags = process_metadata_entries(raw_entries)
        
        if not validate_metadata_structure(structured_meta):
            logger.error("Metadata validation failed. Aborting.")
            sys.exit(1)
        
        # Write structured metadata
        with open(metadata_output, 'w') as f:
            json.dump(structured_meta, f, indent=2)
        logger.info(f"Wrote structured metadata to {metadata_output}")
        
        # Write uncertainty flags
        with open(flags_output, 'w') as f:
            json.dump(flags, f, indent=2)
        logger.info(f"Wrote uncertainty flags to {flags_output}")
        
        # Update state
        state_manager_path = base_path / "code" / "utils" / "state_manager.py"
        # We import the function directly to avoid circular imports if state_manager is not in sys.path yet
        from utils.state_manager import update_artifact_state
        
        update_artifact_state(str(metadata_output))
        update_artifact_state(str(flags_output))
        
        logger.info("Task T013 completed successfully.")
        
    except Exception as e:
        logger.error(f"Task T013 failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
