"""
Fetch phylogenetic tree from Open Tree of Life API.

This module implements the strict requirement to fetch a real phylogenetic tree.
If the fetch fails, it halts immediately with a critical error as per FR-010.
No synthetic fallback is implemented.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Optional, Dict, Any

import requests

# Import config for paths
try:
    from config import ensure_directories, get_config_summary
except ImportError:
    # Fallback for direct execution if path not set up correctly in environment
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from config import ensure_directories, get_config_summary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
OPEN_TREE_API_URL = "https://api.opentreeoflife.org/v3"
TAXON_MATCH_URL = f"{OPEN_TREE_API_URL}/taxa/find"
TREES_URL = f"{OPEN_TREE_API_URL}/trees/synthetic"

# Output paths
OUTPUT_DIR = Path("data/derived")
OUTPUT_FILE = OUTPUT_DIR / "phylogenetic_tree.newick"

def get_species_list() -> List[str]:
    """
    Retrieve the list of species IDs from the merged dataset.
    This list is used to query the Open Tree of Life API.
    
    Returns:
        List[str]: List of species scientific names.
    
    Raises:
        FileNotFoundError: If the merged data file does not exist.
        ValueError: If the merged data file is empty or missing the species column.
    """
    merged_data_path = Path("data/derived/merged_data.csv")
    
    if not merged_data_path.exists():
        logger.error(f"Merged data file not found: {merged_data_path}")
        raise FileNotFoundError(f"Merged data file not found: {merged_data_path}")
    
    try:
        import pandas as pd
        df = pd.read_csv(merged_data_path)
        
        # Identify the species column. It might be 'species', 'species_id', or 'species_name'
        # Based on T021/T020, it's likely 'species' or derived from the merge.
        possible_cols = ['species', 'species_id', 'species_name', 'scientific_name']
        species_col = None
        for col in possible_cols:
            if col in df.columns:
                species_col = col
                break
        
        if species_col is None:
            raise ValueError(f"Could not find species column in {merged_data_path}. Columns: {list(df.columns)}")
        
        # Extract unique species names, drop NaNs
        species_list = df[species_col].dropna().unique().tolist()
        
        if not species_list:
            raise ValueError("No species found in merged data.")
        
        logger.info(f"Found {len(species_list)} unique species in merged data.")
        return species_list
        
    except Exception as e:
        logger.error(f"Error reading merged data: {e}")
        raise

def resolve_taxon_ids(species_list: List[str]) -> Optional[Dict[str, str]]:
    """
    Resolve scientific names to Open Tree of Life taxon IDs.
    
    Args:
        species_list (List[str]): List of scientific names.
        
    Returns:
        Optional[Dict[str, str]]: Mapping of name to OTT ID, or None if failed.
    """
    resolved = {}
    failed_names = []
    
    # Open Tree API allows batch matching if we send a list
    # However, the API endpoint `taxa/find` usually takes a single name or a list in the body.
    # Let's try batch first.
    
    payload = {"names": species_list}
    
    try:
        response = requests.post(TAXON_MATCH_URL, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "mapped" in data:
            for item in data["mapped"]:
                name = item.get("name")
                ott_id = item.get("ott_id")
                if name and ott_id:
                    resolved[name] = str(ott_id)
                else:
                    failed_names.append(name)
        else:
            # Fallback: try single lookups if batch structure is unexpected
            logger.warning("Batch response structure unexpected, falling back to single lookups.")
            for name in species_list:
                single_payload = {"name": name}
                try:
                    single_resp = requests.post(TAXON_MATCH_URL, json=single_payload, timeout=10)
                    if single_resp.status_code == 200:
                        single_data = single_resp.json()
                        if "mapped" in single_data and len(single_data["mapped"]) > 0:
                            ott_id = single_data["mapped"][0].get("ott_id")
                            if ott_id:
                                resolved[name] = str(ott_id)
                            else:
                                failed_names.append(name)
                        else:
                            failed_names.append(name)
                    else:
                        failed_names.append(name)
                except Exception as e:
                    logger.error(f"Failed to resolve {name} individually: {e}")
                    failed_names.append(name)
                    
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse API response: {e}")
        return None
    
    if failed_names:
        logger.warning(f"Failed to resolve {len(failed_names)} species: {failed_names[:5]}...")
    
    return resolved

def fetch_phylogenetic_tree(ott_ids: List[str]) -> Optional[str]:
    """
    Fetch the synthetic phylogenetic tree for a list of OTT IDs.
    
    Args:
        ott_ids (List[str]): List of OTT IDs.
        
    Returns:
        Optional[str]: The Newick string, or None if failed.
    """
    if not ott_ids:
        logger.error("No OTT IDs provided to fetch tree.")
        return None
    
    payload = {
        "ott_taxa": ott_ids,
        "include_strict_ancestry": True
    }
    
    try:
        response = requests.post(TREES_URL, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        if "newick" in data:
            return data["newick"]
        else:
            logger.error("API response did not contain 'newick' key.")
            logger.debug(f"Response keys: {data.keys()}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch tree from Open Tree API: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse tree response: {e}")
        return None

def save_tree(newick_string: str, output_path: Path) -> None:
    """
    Save the Newick string to a file.
    
    Args:
        newick_string (str): The Newick formatted tree string.
        output_path (Path): The path to save the file.
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(newick_string)
        logger.info(f"Phylogenetic tree saved to {output_path}")
    except IOError as e:
        logger.error(f"Failed to write tree file: {e}")
        raise

def main() -> None:
    """
    Main execution flow for fetching the phylogenetic tree.
    
    1. Load species list from merged data.
    2. Resolve names to OTT IDs.
    3. Fetch the tree.
    4. Save to data/derived/phylogenetic_tree.newick.
    
    If any step fails, the script halts with a critical error.
    """
    logger.info("Starting phylogenetic tree fetch.")
    
    # Ensure output directory exists
    ensure_directories()
    
    try:
        # Step 1: Get species list
        species_list = get_species_list()
        if not species_list:
            raise ValueError("No species found to fetch tree for.")
        
        # Step 2: Resolve IDs
        resolved = resolve_taxon_ids(species_list)
        if not resolved:
            raise RuntimeError("Failed to resolve any species to OTT IDs.")
        
        ott_ids = list(resolved.values())
        logger.info(f"Resolved {len(ott_ids)} species to OTT IDs.")
        
        # Step 3: Fetch tree
        newick = fetch_phylogenetic_tree(ott_ids)
        
        if newick is None:
            # CRITICAL FAILURE: HALT IMMEDIATELY
            error_msg = "Phylogenetic tree fetch failed. PVR fallback is impossible without a tree. FR-010 violation."
            logger.critical(error_msg)
            raise RuntimeError(error_msg)
        
        # Step 4: Save tree
        save_tree(newick, OUTPUT_FILE)
        
        logger.info("Phylogenetic tree fetch completed successfully.")
        
    except FileNotFoundError as e:
        logger.critical(f"Critical error: {e}")
        sys.exit(1)
    except RuntimeError as e:
        logger.critical(f"Critical error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error during tree fetch: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
