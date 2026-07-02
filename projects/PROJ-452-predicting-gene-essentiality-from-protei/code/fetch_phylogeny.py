"""
Fetch phylogenetic tree from OpenTree of Life API.

Retrieves the minimal supertree containing the target organisms defined in config,
saves it as a Newick file, and handles failures gracefully by logging warnings.
"""
import os
import logging
from pathlib import Path
import requests
from typing import List, Dict, Any, Optional

from config import load_config, get_organisms, get_path, ensure_dirs
from utils import setup_logging, exponential_backoff

# OpenTree API endpoint for tree synthesis
OPENTREE_SYNTHESIS_URL = "https://api.opentree.org/v3/ot/supertree"
OPENTREE_TAXONOMY_URL = "https://api.opentree.org/v3/ot/taxonomy"

def get_taxonomic_ids_for_organisms(organism_names: List[str]) -> Dict[str, str]:
    """
    Resolve organism names to OpenTree OTT (Open Tree Taxonomy) IDs.
    Returns a mapping of organism name -> ott_id.
    """
    resolved = {}
    for name in organism_names:
        try:
            # Query taxonomy API to find the OTT ID
            params = {"label": name, "limit": 1}
            response = requests.get(OPENTREE_TAXONOMY_URL + "/search", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("results"):
                ott_id = data["results"][0].get("ott_id")
                resolved[name] = ott_id
                logging.info(f"Resolved {name} to OTT ID: {ott_id}")
            else:
                logging.warning(f"Could not resolve organism name: {name}")
        except Exception as e:
            logging.error(f"Failed to resolve {name}: {e}")
    return resolved

def fetch_supertree(ott_ids: List[str]) -> Optional[Dict[str, Any]]:
    """
    Fetch the minimal supertree containing the given OTT IDs from OpenTree.
    Returns the JSON response containing the Newick tree string, or None on failure.
    """
    if not ott_ids:
        logging.warning("No OTT IDs provided for supertree synthesis.")
        return None

    payload = {
        "ott_taxon_ids": ott_ids,
        "include_tax_labels": True
    }

    try:
        response = requests.post(OPENTREE_SYNTHESIS_URL, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch supertree from OpenTree API: {e}")
        return None

def extract_newick(tree_json: Dict[str, Any]) -> Optional[str]:
    """
    Extract the Newick string from the OpenTree synthesis response.
    The tree is typically under 'data -> tree'.
    """
    try:
        # OpenTree v3 response structure
        return tree_json.get("data", {}).get("tree")
    except (KeyError, AttributeError):
        logging.error("Could not extract tree from OpenTree response.")
        return None

def save_newick_tree(newick_str: str, output_path: Path) -> None:
    """
    Save the Newick string to a file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(newick_str)
    logging.info(f"Saved phylogenetic tree to {output_path}")

def main():
    """
    Main entry point for T009.
    1. Load config to get target organisms.
    2. Resolve names to OTT IDs.
    3. Fetch supertree from OpenTree.
    4. Save to data/phylogeny/tree.newick.
    5. If any step fails, log warning and exit cleanly (do not crash).
    """
    setup_logging()
    logger = logging.getLogger(__name__)

    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return

    # Get target organisms from config
    organisms = get_organisms(config)
    if not organisms:
        logger.warning("No target organisms defined in config. Skipping phylogeny fetch.")
        return

    logger.info(f"Target organisms: {organisms}")

    # Resolve to OTT IDs
    ott_map = get_taxonomic_ids_for_organisms(organisms)
    if not ott_map:
        logger.warning("Could not resolve any organism names to OTT IDs. Skipping tree fetch.")
        return

    ott_ids = list(ott_map.values())
    logger.info(f"Fetching supertree for OTT IDs: {ott_ids}")

    # Fetch tree
    tree_json = fetch_supertree(ott_ids)
    if not tree_json:
        logger.warning("Failed to fetch phylogenetic tree. PGLS analysis will be skipped.")
        return

    # Extract Newick
    newick_str = extract_newick(tree_json)
    if not newick_str:
        logger.warning("Tree response did not contain a valid Newick string. PGLS analysis will be skipped.")
        return

    # Save to disk
    output_path = get_path(config, "data", "phylogeny", "tree.newick")
    ensure_dirs(config, "data", "phylogeny")
    save_newick_tree(newick_str, output_path)

    logger.info("Phylogeny fetch completed successfully.")

if __name__ == "__main__":
    main()
