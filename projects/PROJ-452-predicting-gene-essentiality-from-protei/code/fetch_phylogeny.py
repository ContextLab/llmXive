import os
import logging
from pathlib import Path
import requests
from typing import List, Dict, Any, Optional

from config import load_config, get_organisms, get_path, ensure_dirs

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

OPENTREE_API_BASE = "https://api.opentree.org"
OTOL_TAXONOMY_ENDPOINT = f"{OPENTREE_API_BASE}/v4/taxonomy"
OTOL_SUPERTREE_ENDPOINT = f"{OPENTREE_API_BASE}/v4/supertree"

class PhylogenyFetchError(Exception):
    """Custom exception for phylogeny fetching errors."""
    pass

def get_taxonomic_ids_for_organisms(organism_names: List[str], config: Dict[str, Any]) -> Dict[str, int]:
    """
    Maps organism names from config to their taxonomic IDs.
    
    Args:
        organism_names: List of organism names (e.g., "Saccharomyces cerevisiae")
        config: Configuration dictionary containing taxonomic mappings if defined,
                or fallback logic.
                
    Returns:
        Dict mapping organism name to taxonomic ID (int).
    """
    tax_ids = {}
    # Check if config has explicit mappings (preferred)
    explicit_map = config.get('taxonomic_mappings', {})
    
    for name in organism_names:
        if name in explicit_map:
            tax_ids[name] = explicit_map[name]
            logger.info(f"Found explicit taxonomic ID for {name}: {explicit_map[name]}")
        else:
            # Fallback: attempt to query OpenTree taxonomy API if name is not in explicit map
            # This handles cases where config might be minimal
            query_url = f"{OTOL_TAXONOMY_ENDPOINT}/name_to_id"
            params = {'name': name}
            try:
                resp = requests.get(query_url, params=params, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                if 'ot:ott_id' in data and data['ot:ott_id']:
                    tax_ids[name] = data['ot:ott_id']
                    logger.info(f"Retrieved taxonomic ID for {name} via API: {data['ot:ott_id']}")
                else:
                    logger.warning(f"Could not find taxonomic ID for {name} (API returned empty).")
            except requests.RequestException as e:
                logger.warning(f"Failed to fetch taxonomic ID for {name} from OpenTree: {e}")
    
    return tax_ids

def fetch_supertree(tax_ids: List[int]) -> Optional[Dict[str, Any]]:
    """
    Fetches the supertree containing the given taxonomic IDs from OpenTree.
    
    Args:
        tax_ids: List of taxonomic IDs (OTT IDs) to include in the tree.
                
    Returns:
        The JSON response containing the tree data, or None if fetch fails.
    """
    if not tax_ids:
        logger.warning("No taxonomic IDs provided for supertree fetch.")
        return None

    url = f"{OPENTREE_API_BASE}/v3/supertree"
    payload = {
        "ott_taxa": tax_ids,
        "output_format": "newick"
    }
    
    try:
        logger.info(f"Fetching supertree for {len(tax_ids)} taxa from OpenTree...")
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch supertree from OpenTree: {e}")
        return None
    except ValueError as e:
        logger.error(f"Invalid JSON response from OpenTree: {e}")
        return None

def extract_newick(tree_data: Dict[str, Any]) -> Optional[str]:
    """
    Extracts the Newick string from the API response.
    
    Args:
        tree_data: JSON response from OpenTree supertree endpoint.
                
    Returns:
        The Newick string, or None if extraction fails.
    """
    if not tree_data:
        return None
        
    # OpenTree API v3 usually returns the tree in 'tree' key as a Newick string
    # or sometimes wrapped in 'ott_ids' -> 'tree'.
    # Standard v3 response structure for 'output_format': 'newick' puts the string in 'tree'.
    newick_str = tree_data.get('tree')
    
    if not newick_str:
        # Fallback check for nested structures if API changes
        if 'ott_ids' in tree_data and 'tree' in tree_data['ott_ids']:
            newick_str = tree_data['ott_ids']['tree']
    
    if newick_str:
        logger.info("Successfully extracted Newick string from API response.")
        return newick_str
    else:
        logger.error("Could not locate 'tree' field in OpenTree response.")
        return None

def save_newick_tree(newick_str: str, output_path: Path) -> None:
    """
    Saves the Newick string to a file.
    
    Args:
        newick_str: The Newick string content.
        output_path: Path to the output file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(newick_str)
    logger.info(f"Saved phylogenetic tree to {output_path}")

def main():
    """
    Main entry point for fetching the phylogenetic tree.
    Fetches the tree for organisms defined in config and saves it to data/phylogeny/tree.newick.
    If fetch fails, logs a warning and returns without crashing the build.
    """
    config = load_config()
    organisms = get_organisms(config)
    
    if not organisms:
        logger.warning("No organisms defined in config. Skipping phylogeny fetch.")
        return

    # 1. Get Taxonomic IDs
    tax_id_map = get_taxonomic_ids_for_organisms(organisms, config)
    tax_ids = list(tax_id_map.values())
    
    if not tax_ids:
        logger.warning("Could not determine taxonomic IDs for any organism. Skipping tree fetch.")
        return

    # 2. Fetch Supertree
    tree_data = fetch_supertree(tax_ids)
    
    if tree_data is None:
        logger.warning("Phylogenetic tree fetch failed. The comparative test (PGLS) will be skipped gracefully.")
        return

    # 3. Extract Newick
    newick_str = extract_newick(tree_data)
    
    if not newick_str:
        logger.warning("Phylogenetic tree extraction failed. The comparative test (PGLS) will be skipped gracefully.")
        return

    # 4. Save to file
    output_path = get_path(config, "data/phylogeny/tree.newick")
    ensure_dirs(config, "data/phylogeny")
    save_newick_tree(newick_str, output_path)
    
    logger.info("Phylogeny fetch task completed successfully.")

if __name__ == "__main__":
    main()
