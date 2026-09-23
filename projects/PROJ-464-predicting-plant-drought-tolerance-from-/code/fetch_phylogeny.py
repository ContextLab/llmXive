"""
Fetch phylogenetic tree from Open Tree of Life API.

This module implements T024a:
- Fetches a phylogenetic tree for species found in the merged dataset.
- Writes the tree to `data/derived/phylogenetic_tree.newick`.
- Halts immediately with a critical error if the fetch fails (no fallback).
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import requests
import yaml

# Configure logging to match project standards
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import config for paths
try:
    from config import ensure_directories, get_config_summary
except ImportError:
    # Fallback for direct execution without package context
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from config import ensure_directories, get_config_summary

# Open Tree of Life API endpoints
OTOL_TAXON_RESOLVE_URL = "https://api.opentreeoflife.org/v3/taxon/resolve"
OTOL_TAXONOMY_URL = "https://api.opentreeoflife.org/v3/phylogeny/ot_tree_for_taxa"

def get_species_list() -> List[str]:
    """
    Extract unique species names from the merged dataset (data/derived/merged_data.csv).
    
    Returns:
        List[str]: List of species names to fetch phylogeny for.
    
    Raises:
        FileNotFoundError: If merged data file does not exist.
        ValueError: If no species found in the data.
    """
    merged_path = Path("data/derived/merged_data.csv")
    if not merged_path.exists():
        logger.error(f"Merged data file not found at {merged_path}.")
        raise FileNotFoundError(f"Merged data file not found: {merged_path}")

    try:
        import pandas as pd
        df = pd.read_csv(merged_path)
    except Exception as e:
        logger.error(f"Failed to read merged data: {e}")
        raise

    # Identify species column - typically 'species' or 'species_id'
    # Based on T015 and T021, the column is likely 'species' or 'species_id'
    species_col = None
    candidates = ['species', 'species_id', 'Species', 'Species_id']
    for col in candidates:
        if col in df.columns:
            species_col = col
            break
    
    if species_col is None:
        logger.error(f"Could not find species column in {merged_path}. Available columns: {list(df.columns)}")
        raise ValueError(f"Species column not found in {merged_path}")

    species_list = df[species_col].dropna().unique().tolist()
    
    if not species_list:
        logger.error("No species found in the merged dataset.")
        raise ValueError("No species found in the merged dataset.")

    logger.info(f"Found {len(species_list)} unique species in merged data.")
    return species_list

def resolve_taxon_ids(species_names: List[str]) -> Dict[str, Any]:
    """
    Resolve species names to Open Tree of Life taxon IDs.
    
    Args:
        species_names: List of species names to resolve.
    
    Returns:
        Dict containing 'resolved_ids' (list of tax_ids) and 'unresolved' (list of names).
    """
    logger.info(f"Resolving {len(species_names)} taxon names via Open Tree of Life API...")
    
    resolved_ids = []
    unresolved_names = []
    
    # Process in batches if needed, but OTOL resolve handles lists well
    payload = {
        "names": species_names
    }
    
    try:
        response = requests.post(OTOL_TAXON_RESOLVE_URL, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to Open Tree of Life resolve API: {e}")
        raise RuntimeError(f"Taxon resolve API failed: {e}")
    except ValueError as e:
        logger.error(f"Invalid JSON response from taxon resolve API: {e}")
        raise RuntimeError(f"Invalid JSON from taxon resolve API: {e}")

    # Parse response: expected format { "resolved": [{"name": "...", "ot:ot_id": "..."}, ...], "unresolved": [...] }
    resolved_items = result.get("resolved", [])
    unresolved_items = result.get("unresolved", [])

    for item in resolved_items:
        # The ID might be in different keys depending on API version
        tax_id = item.get("ot:ott_id") or item.get("ott_id") or item.get("id")
        if tax_id:
            resolved_ids.append(str(tax_id))
        else:
            # Fallback to name if ID missing but resolved
            unresolved_names.append(item.get("name", "unknown"))

    for item in unresolved_items:
        unresolved_names.append(item)

    logger.info(f"Resolved {len(resolved_ids)} taxa. Unresolved: {len(unresolved_names)}")
    if unresolved_names:
        logger.warning(f"Unresolved taxa: {unresolved_names[:10]}... (showing first 10)")

    return {
        "resolved_ids": resolved_ids,
        "unresolved": unresolved_names
    }

def fetch_phylogenetic_tree(tax_ids: List[str]) -> Optional[str]:
    """
    Fetch the phylogenetic tree (Newick format) for a list of taxon IDs.
    
    Args:
        tax_ids: List of Open Tree of Life taxon IDs (strings).
    
    Returns:
        str: Newick formatted tree string.
    
    Raises:
        RuntimeError: If the fetch fails or returns no tree.
    """
    if not tax_ids:
        logger.error("No taxon IDs provided to fetch tree.")
        return None

    logger.info(f"Fetching phylogenetic tree for {len(tax_ids)} taxa...")

    payload = {
        "tax_ids": tax_ids,
        "include_branch_lengths": True
    }

    try:
        response = requests.post(OTOL_TAXONOMY_URL, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch phylogenetic tree from OTOL API: {e}")
        raise RuntimeError(f"Phylogenetic tree fetch failed: {e}")
    except ValueError as e:
        logger.error(f"Invalid JSON response from tree API: {e}")
        raise RuntimeError(f"Invalid JSON from tree API: {e}")

    # Check for tree in response
    # Expected keys: 'ot:tree', 'tree', 'newick'
    newick_str = None
    possible_keys = ['ot:tree', 'tree', 'newick', 'newick_string']
    for key in possible_keys:
        if key in result:
            newick_str = result[key]
            break
    
    if not newick_str:
        # Check for error messages in response
        error_msg = result.get("error", result.get("message", "Unknown error"))
        logger.error(f"API returned no tree. Response keys: {list(result.keys())}. Error: {error_msg}")
        raise RuntimeError(f"Phylogenetic tree fetch failed: No tree found in API response. {error_msg}")

    # Basic validation: Newick should contain parentheses and semicolon
    if '(' not in newick_str or ';' not in newick_str:
        logger.error(f"Invalid Newick format detected. Length: {len(newick_str)}")
        raise RuntimeError("Phylogenetic tree fetch failed: Invalid Newick format returned.")

    logger.info(f"Successfully fetched tree. Length: {len(newick_str)} chars.")
    return newick_str

def save_tree(newick_str: str, output_path: Path) -> None:
    """
    Save the Newick tree string to a file.
    
    Args:
        newick_str: The Newick formatted tree string.
        output_path: Path to save the file.
    
    Raises:
        IOError: If file writing fails.
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(newick_str)
        logger.info(f"Phylogenetic tree saved to {output_path}")
    except IOError as e:
        logger.error(f"Failed to write tree file: {e}")
        raise

def main():
    """
    Main entry point for T024a.
    
    1. Load species list from merged data.
    2. Resolve names to OTOL tax IDs.
    3. Fetch tree.
    4. Save to data/derived/phylogenetic_tree.newick.
    5. HALT on any failure (no fallback).
    """
    logger.info("Starting T024a: Fetch Phylogenetic Tree")
    
    # Ensure output directory exists
    ensure_directories()
    output_path = Path("data/derived/phylogenetic_tree.newick")
    
    try:
        # Step 1: Get species list
        species_list = get_species_list()
        if not species_list:
            logger.critical("No species found in merged data. Cannot proceed.")
            sys.exit(1)
        
        # Step 2: Resolve tax IDs
        resolution_result = resolve_taxon_ids(species_list)
        resolved_ids = resolution_result["resolved_ids"]
        
        if not resolved_ids:
            logger.critical("No taxa could be resolved to OTOL IDs. Cannot fetch tree.")
            sys.exit(1)
        
        # Step 3: Fetch tree
        newick_tree = fetch_phylogenetic_tree(resolved_ids)
        
        if not newick_tree:
            logger.critical("Phylogenetic tree fetch failed. PVR fallback is impossible without a tree. FR-010 violation.")
            sys.exit(1)
        
        # Step 4: Save tree
        save_tree(newick_tree, output_path)
        
        logger.info("T024a completed successfully.")
        
    except FileNotFoundError as e:
        logger.critical(f"Critical file error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.critical(f"Critical validation error: {e}")
        sys.exit(1)
    except RuntimeError as e:
        # This catches the "HALT" conditions explicitly
        logger.critical(f"CRITICAL: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error during T024a: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
