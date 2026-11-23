"""
Fetches phylogenetic trees from OpenTree of Life.

This module handles the retrieval of Newick format trees for a list of
target organisms using their taxonomic IDs. It gracefully handles fetch
failures by logging a warning, allowing the rest of the pipeline to
proceed without the comparative (PGLS) analysis.
"""
import os
import logging
import time
from pathlib import Path
import requests
from typing import List, Dict, Any, Optional

from config import load_config, get_organisms, get_path, ensure_dirs

logger = logging.getLogger(__name__)

class PhylogenyFetchError(Exception):
    """Raised when phylogenetic tree fetching fails unexpectedly."""
    pass

def get_taxonomic_ids_for_organisms(organisms: List[str]) -> Dict[str, str]:
    """
    Maps organism names to their taxonomic IDs.
    
    In a real implementation, this would query a taxonomy database.
    For this pipeline, we assume the config provides these IDs or
    we use a hardcoded mapping for common model organisms if not present.
    
    Args:
        organisms: List of organism names (e.g., 'saccharomyces_cerevisiae')
        
    Returns:
        Dict mapping organism name to taxonomic ID string
    """
    # Hardcoded mapping for common model organisms as a fallback
    # In a production system, this might query NCBI Taxonomy or similar
    taxonomic_map = {
        'saccharomyces_cerevisiae': '4932',
        'escherichia_coli': '562',
        'caenorhabditis_elegans': '6239',
        'drosophila_melanogaster': '7227',
        'homo_sapiens': '9606',
        'mus_musculus': '10090',
        'arabidopsis_thaliana': '3702',
        'schizosaccharomyces_pombe': '4896',
        'bacillus_subtilis': '1423',
        'staphylococcus_aureus': '1280'
    }
    
    result = {}
    for org in organisms:
        # Try to get from map, otherwise raise error if not found
        if org in taxonomic_map:
            result[org] = taxonomic_map[org]
        else:
            # Try to see if the config has specific tax IDs defined
            # This is a simplified check; real config might be more complex
            logger.warning(f"No taxonomic ID found for {org}. PGLS analysis may be skipped.")
            result[org] = None
    
    return result

def fetch_supertree(tax_ids: List[str]) -> Optional[str]:
    """
    Fetches a supertree from OpenTree of Life API.
    
    Args:
        tax_ids: List of taxonomic IDs to include in the tree
        
    Returns:
        Newick string if successful, None if fetch fails
    """
    if not tax_ids:
        logger.warning("No taxonomic IDs provided for tree fetch.")
        return None

    api_url = "https://api.opentree.org/v3/ot/supertree"
    payload = {
        "ott_taxa": tax_ids,
        "include_excluded_taxa": False,
        "tree_format": "newick"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        logger.info(f"Fetching phylogenetic tree from OpenTree for {len(tax_ids)} taxa...")
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if "tree" in data and data["tree"]:
                logger.info("Successfully retrieved tree from OpenTree.")
                return data["tree"]
            else:
                logger.warning("OpenTree API returned no tree data.")
                return None
        elif response.status_code == 404:
            logger.warning("OpenTree API returned 404. Taxa may not be found or tree unavailable.")
            return None
        else:
            logger.error(f"OpenTree API returned status {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        logger.error("Request to OpenTree timed out.")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching tree: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching tree: {e}")
        return None

def extract_newick(tree_data: Dict[str, Any]) -> Optional[str]:
    """
    Extracts Newick string from OpenTree response structure if needed.
    
    Args:
        tree_data: Parsed JSON response from OpenTree
        
    Returns:
        Newick string or None
    """
    # The fetch_supertree function already returns the tree string directly
    # This function is kept for potential future API changes or different endpoints
    if isinstance(tree_data, str):
        return tree_data
    if isinstance(tree_data, dict) and "tree" in tree_data:
        return tree_data["tree"]
    return None

def save_newick_tree(newick_str: str, output_path: Path) -> bool:
    """
    Saves the Newick tree string to a file.
    
    Args:
        newick_str: The Newick formatted tree string
        output_path: Path where the file should be saved
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write(newick_str)
            
        logger.info(f"Saved phylogenetic tree to {output_path}")
        return True
        
    except IOError as e:
        logger.error(f"Failed to write tree file: {e}")
        return False

def main():
    """
    Main entry point for fetching the phylogenetic tree.
    
    This function:
    1. Loads configuration to get target organisms
    2. Retrieves taxonomic IDs for those organisms
    3. Fetches the supertree from OpenTree
    4. Saves the tree to data/phylogeny/tree.newick
    
    If any step fails, it logs a warning and returns gracefully without
    crashing the pipeline, allowing PGLS to be skipped later.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load config
    try:
        config = load_config()
        organisms = get_organisms(config)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        # Create empty tree file to indicate failure state
        output_path = get_path("data/phylogeny/tree.newick")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write("# Phylogenetic tree fetch failed - see logs\n")
        return
    
    if not organisms:
        logger.warning("No organisms defined in config. Skipping tree fetch.")
        return

    # Get taxonomic IDs
    tax_id_map = get_taxonomic_ids_for_organisms(organisms)
    valid_tax_ids = [tid for tid in tax_id_map.values() if tid is not None]
    
    if not valid_tax_ids:
        logger.warning("No valid taxonomic IDs found for any organisms. Skipping tree fetch.")
        return

    # Fetch the tree
    newick_tree = fetch_supertree(valid_tax_ids)
    
    if newick_tree is None:
        logger.warning("Failed to fetch phylogenetic tree from OpenTree. "
                     "PGLS analysis will be skipped in subsequent steps.")
        # Create a placeholder file to indicate failure
        output_path = get_path("data/phylogeny/tree.newick")
        ensure_dirs(output_path)
        with open(output_path, 'w') as f:
            f.write("# Phylogenetic tree fetch failed - see logs\n")
        return

    # Save the tree
    output_path = get_path("data/phylogeny/tree.newick")
    ensure_dirs(output_path)
    
    if not save_newick_tree(newick_tree, output_path):
        logger.error("Failed to save phylogenetic tree file.")
        return

    logger.info("Phylogenetic tree fetch and save completed successfully.")

if __name__ == "__main__":
    main()
