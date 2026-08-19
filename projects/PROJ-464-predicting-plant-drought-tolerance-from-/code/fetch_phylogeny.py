"""
Fetch phylogenetic tree from Open Tree of Life API.

This module implements the strict requirement for phylogenetic data
to support Phylogenetic Generalized Least Squares (PGLS) modeling.

Logic:
1. Extract unique species from merged data (rsametrics.csv + physiological data).
2. Query Open Tree of Life API for the supertree containing these species.
3. If fetch fails (no tree found, API error), HALT immediately with critical error.
4. Save the tree to data/derived/phylogenetic_tree.newick.

No fallback to synthetic or equivalent trees is permitted.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import requests
import pandas as pd
from config import ensure_directories, Hyperparameters

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
OPEN_TREE_API_URL = "https://api.opentreeoflife.org/v3"
OTOL_TAXONOMY_URL = f"{OPEN_TREE_API_URL}/taxo/name_to_id"
OTOL_SUPERTREE_URL = f"{OPEN_TREE_API_URL}/tree/otol_supertree"

# Output path (relative to project root)
OUTPUT_DIR = Path("data/derived")
OUTPUT_FILE = OUTPUT_DIR / "phylogenetic_tree.newick"

# Input data paths
RSA_METRICS_PATH = Path("data/derived/rsametrics.csv")
PHYSIO_TRAITS_PATH = Path("data/derived/physiological_traits.csv")
MERGED_PATH = Path("data/derived/merged_dataset.csv")

def get_species_list() -> List[str]:
    """
    Extract unique species IDs from the merged dataset.
    
    Tries to load from merged_dataset.csv first (preferred, as it contains
    the intersection of RSA and physiological data). Falls back to rsametrics.csv
    if merged dataset doesn't exist yet (though T021 should have created it).
    
    Returns:
        List of unique species IDs (scientific names).
        
    Raises:
        FileNotFoundError: If no input data files are found.
        ValueError: If no species are found in the data.
    """
    species_set = set()
    
    # Prefer merged dataset as it represents the actual analysis population
    if MERGED_PATH.exists():
        logger.info(f"Loading species from merged dataset: {MERGED_PATH}")
        df = pd.read_csv(MERGED_PATH)
        if 'species_id' in df.columns:
            species_set.update(df['species_id'].dropna().astype(str).unique())
        elif 'species' in df.columns:
            species_set.update(df['species'].dropna().astype(str).unique())
    elif RSA_METRICS_PATH.exists():
        logger.warning(f"Merged dataset not found. Falling back to RSA metrics: {RSA_METRICS_PATH}")
        df = pd.read_csv(RSA_METRICS_PATH)
        if 'species_id' in df.columns:
            species_set.update(df['species_id'].dropna().astype(str).unique())
    else:
        raise FileNotFoundError(
            f"No input data found. Expected {MERGED_PATH} or {RSA_METRICS_PATH}"
        )
    
    if not species_set:
        raise ValueError("No species found in input data. Cannot fetch phylogeny.")
    
    logger.info(f"Found {len(species_set)} unique species for phylogeny fetch")
    return sorted(list(species_set))

def resolve_taxon_ids(species_list: List[str]) -> Dict[str, str]:
    """
    Resolve species names to Open Tree of Life OTU IDs.
    
    Args:
        species_list: List of scientific names (species IDs).
        
    Returns:
        Dictionary mapping species name to OTU ID.
        
    Raises:
        RuntimeError: If API call fails.
    """
    if not species_list:
        return {}
    
    # Open Tree API expects a list of names
    payload = {
        "names": species_list
    }
    
    try:
        response = requests.post(
            OTOL_TAXONOMY_URL,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        name_to_id = {}
        
        # Process results - the API returns a list of matches
        if "mapped" in result:
            for item in result["mapped"]:
                name = item.get("name")
                otu_id = item.get("otol_id")
                if name and otu_id:
                    name_to_id[name] = str(otu_id)
        
        logger.info(f"Resolved {len(name_to_id)}/{len(species_list)} species to OTU IDs")
        
        # Check for unresolved species
        unresolved = set(species_list) - set(name_to_id.keys())
        if unresolved:
            logger.warning(f"Could not resolve {len(unresolved)} species: {unresolved}")
        
        return name_to_id
        
    except requests.RequestException as e:
        logger.error(f"Failed to resolve taxon IDs from Open Tree API: {e}")
        raise RuntimeError(f"Taxonomy resolution failed: {e}") from e

def fetch_phylogenetic_tree(otu_ids: List[str]) -> Optional[str]:
    """
    Fetch the phylogenetic tree from Open Tree of Life for the given OTU IDs.
    
    Args:
        otu_ids: List of Open Tree OTU IDs.
        
    Returns:
        Newick format tree string, or None if no tree found.
        
    Raises:
        RuntimeError: If API call fails or tree cannot be fetched.
    """
    if not otu_ids:
        return None
    
    # Use the 'tree_of_life' method to get a supertree for these taxa
    # We request the tree in Newick format
    payload = {
        "otu_ids": otu_ids,
        "output_format": "newick"
    }
    
    try:
        # The Open Tree API endpoint for getting a tree for specific OTUs
        # We use the 'synthesis' endpoint which attempts to find a tree
        # containing the specified taxa
        synthesis_url = f"{OPEN_TREE_API_URL}/tree/synthesis"
        
        response = requests.post(
            synthesis_url,
            json=payload,
            timeout=60  # Trees can take longer to generate
        )
        
        if response.status_code == 404:
            # No tree found for these taxa
            logger.warning("No phylogenetic tree found in Open Tree of Life for the requested taxa.")
            return None
        
        response.raise_for_status()
        
        result = response.json()
        
        # The tree is typically in the 'tree' field as a Newick string
        if "tree" in result:
            newick_tree = result["tree"]
            if newick_tree and len(newick_tree) > 10:  # Basic sanity check
                logger.info("Successfully fetched phylogenetic tree")
                return newick_tree
        
        logger.warning("Response received but no valid tree found in payload")
        return None
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch phylogenetic tree from Open Tree API: {e}")
        raise RuntimeError(f"Tree fetch failed: {e}") from e

def save_tree(tree_string: str, output_path: Path) -> None:
    """
    Save the phylogenetic tree to a Newick file.
    
    Args:
        tree_string: Newick format tree string.
        output_path: Path to save the tree file.
        
    Raises:
        IOError: If file cannot be written.
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(tree_string)
        logger.info(f"Phylogenetic tree saved to {output_path}")
    except IOError as e:
        logger.error(f"Failed to save phylogenetic tree: {e}")
        raise

def main() -> None:
    """
    Main entry point for fetching phylogenetic tree.
    
    Workflow:
    1. Load species from merged data.
    2. Resolve species names to OTU IDs.
    3. Fetch phylogenetic tree from Open Tree of Life.
    4. If fetch fails, HALT with critical error.
    5. Save tree to data/derived/phylogenetic_tree.newick.
    """
    logger.info("Starting phylogenetic tree fetch (T024a)")
    
    # Ensure output directory exists
    ensure_directories()
    
    try:
        # Step 1: Get species list
        species_list = get_species_list()
        logger.info(f"Species list: {species_list[:10]}... ({len(species_list)} total)")
        
        # Step 2: Resolve to OTU IDs
        name_to_id = resolve_taxon_ids(species_list)
        
        if not name_to_id:
            raise RuntimeError(
                "Failed to resolve any species to OTU IDs. "
                "Cannot proceed with phylogeny fetch."
            )
        
        otu_ids = list(name_to_id.values())
        logger.info(f"Resolved {len(otu_ids)} OTU IDs")
        
        # Step 3: Fetch tree
        logger.info("Fetching phylogenetic tree from Open Tree of Life...")
        tree_string = fetch_phylogenetic_tree(otu_ids)
        
        # Step 4: Critical check - if no tree, HALT immediately
        if tree_string is None:
            error_msg = (
                "Phylogenetic tree fetch failed. PVR fallback is impossible without a tree. "
                "FR-010 violation."
            )
            logger.critical(error_msg)
            logger.critical(
                f"Species attempted: {len(name_to_id)} ({list(name_to_id.keys())[:5]}...)"
            )
            raise RuntimeError(error_msg)
        
        # Step 5: Save tree
        save_tree(tree_string, OUTPUT_FILE)
        
        logger.info("Phylogenetic tree fetch completed successfully")
        
    except FileNotFoundError as e:
        logger.critical(f"Input data not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.critical(f"Data validation error: {e}")
        sys.exit(1)
    except RuntimeError as e:
        # This includes the critical HALT condition for missing tree
        logger.critical(f"Critical error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error during phylogeny fetch: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
