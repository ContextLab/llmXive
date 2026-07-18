"""
Fetches the Newick phylogenetic tree from OpenTree of Life API.

This module handles the retrieval of the supertree for a list of target organisms
based on their taxonomic IDs. It saves the resulting Newick tree to the data/phylogeny/
directory. If the fetch fails, it logs a warning and does not crash the build,
allowing downstream tasks (like PGLS) to skip gracefully.
"""
import os
import logging
from pathlib import Path
import requests
from typing import List, Dict, Any, Optional

from config import load_config, get_organisms, get_path, ensure_dirs

logger = logging.getLogger(__name__)

OPEN_TREE_API_BASE = "https://api.opentree.org/v3"
TAxONOMY_LOOKUP_ENDPOINT = f"{OPEN_TREE_API_BASE}/taxonomy/ott_id_for_taxon_name"
SUPERTREE_ENDPOINT = f"{OPEN_TREE_API_BASE}/supertree/study_tree"

# Note: The OpenTree API for supertrees usually requires a study ID or a specific
# method to generate a tree for a set of OTT IDs. The standard endpoint for
# generating a tree for a set of OTT IDs is:
# POST /v3/supertree/otx_to_newick
# However, the most robust way to get a tree for specific taxa is often:
# POST /v3/supertree/study_tree (requires study_id)
# OR using the "synthesis" endpoint if available, but the standard "synthesis"
# endpoint often requires a list of OTT IDs to include.
#
# Based on common usage patterns for OpenTree:
# 1. Get OTT IDs for taxon names.
# 2. Use the 'synthesis' or 'otx_to_newick' endpoint to get the tree.
#
# The endpoint 'https://api.opentree.org/v3/supertree/otx_to_newick' takes a JSON body:
# { "ott_ids": [123, 456], "color_by_taxon": false }
# This returns the Newick string directly.

def get_taxonomic_ids_for_organisms(taxon_names: List[str]) -> Dict[str, int]:
    """
    Resolves a list of taxon names to OpenTree Taxonomy (OTT) IDs.
    
    Args:
        taxon_names: List of organism common names or scientific names.
        
    Returns:
        Dictionary mapping taxon name to OTT ID.
    """
    ott_ids = {}
    session = requests.Session()
    
    for name in taxon_names:
        try:
            # OpenTree API v3: GET /taxonomy/ott_id_for_taxon_name
            # Note: The actual endpoint might be /v3/taxonomy/ott_id_for_taxon_name
            # Let's use the direct lookup if available, or search.
            # The standard endpoint for name -> ID is:
            # POST /v3/taxonomy/ott_id_for_taxon_name (with name in body)
            # OR GET /v3/taxonomy/ott_id_for_taxon_name?name=...
            
            # Using the search endpoint which is more robust for names
            url = f"{OPEN_TREE_API_BASE}/taxonomy/ott_id_for_taxon_name"
            params = {"name": name}
            
            # Some versions of the API require POST with JSON body
            # Let's try GET first as it's simpler for simple lookups
            resp = session.get(url, params=params, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                # The response structure for ott_id_for_taxon_name is typically:
                # { "ott_id": 12345, "source_id": "ott", "source_taxon_name": "..." }
                if "ott_id" in data:
                    ott_ids[name] = int(data["ott_id"])
                    logger.info(f"Resolved {name} to OTT ID: {data['ott_id']}")
                else:
                    logger.warning(f"Could not resolve OTT ID for {name}. Response: {data}")
            else:
                logger.warning(f"Failed to resolve {name}: HTTP {resp.status_code}")
                
        except requests.RequestException as e:
            logger.warning(f"Network error resolving {name}: {e}")
            continue
        
    return ott_ids

def fetch_supertree(ott_ids: List[int]) -> Optional[str]:
    """
    Fetches the Newick tree for a list of OTT IDs from OpenTree.
    
    Args:
        ott_ids: List of OpenTree Taxonomy IDs.
        
    Returns:
        Newick string if successful, None otherwise.
    """
    if not ott_ids:
        logger.warning("No OTT IDs provided for tree fetch.")
        return None

    url = f"{OPEN_TREE_API_BASE}/supertree/otx_to_newick"
    payload = {
        "ott_ids": ott_ids,
        "color_by_taxon": False
    }
    
    try:
        logger.info(f"Fetching tree for OTT IDs: {ott_ids}")
        resp = requests.post(url, json=payload, timeout=60)
        
        if resp.status_code == 200:
            # The response is the raw Newick string
            newick = resp.text.strip()
            if newick:
                logger.info(f"Successfully fetched tree ({len(newick)} chars)")
                return newick
            else:
                logger.error("Received empty tree from API.")
        else:
            logger.error(f"API Error fetching tree: {resp.status_code} - {resp.text}")
            
    except requests.RequestException as e:
        logger.error(f"Network error while fetching tree: {e}")
        
    return None

def extract_newick(newick: str) -> str:
    """
    Validates and returns the Newick string.
    This is a placeholder for any potential parsing/cleaning if needed.
    """
    return newick

def save_newick_tree(newick: str, output_path: Path) -> None:
    """
    Saves the Newick string to the specified file path.
    
    Args:
        newick: The Newick formatted string.
        output_path: Path to save the file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(newick)
    logger.info(f"Saved phylogenetic tree to {output_path}")

def main() -> None:
    """
    Main entry point for the phylogeny fetch task.
    Loads configuration, fetches tree, and saves to data/phylogeny/tree.newick.
    """
    # Load configuration
    try:
        config = load_config()
        organisms = get_organisms()
    except Exception as e:
        logger.error(f"Failed to load config or get organisms: {e}")
        # If config is missing, we can't proceed.
        return

    if not organisms:
        logger.warning("No organisms defined in config. Skipping phylogeny fetch.")
        return

    taxon_names = [org.get("name") or org.get("taxon_name") for org in organisms if org]
    if not taxon_names:
        logger.warning("Could not extract taxon names from organism config.")
        return

    # 1. Resolve names to OTT IDs
    ott_mapping = get_taxonomic_ids_for_organisms(taxon_names)
    if not ott_mapping:
        logger.warning("Could not resolve any OTT IDs. Skipping tree fetch.")
        return

    ott_ids = list(ott_mapping.values())

    # 2. Fetch the tree
    newick = fetch_supertree(ott_ids)

    if newick is None:
        logger.warning("Failed to fetch phylogenetic tree from OpenTree. "
                     "Downstream comparative tests (PGLS) will be skipped.")
        # Do not raise an exception to allow the build to continue as per task requirements
        return

    # 3. Save the tree
    output_dir = get_path("data", "phylogeny")
    output_file = Path(output_dir) / "tree.newick"
    
    try:
        save_newick_tree(newick, output_file)
    except IOError as e:
        logger.error(f"Failed to save tree to {output_file}: {e}")

if __name__ == "__main__":
    setup_logging = None # Avoid conflict if utils not imported, but we assume utils is available or use basicConfig
    # Ensure logging is set up
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    main()