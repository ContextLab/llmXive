"""
Phylogeny Fetcher for Open Tree of Life.

Fetches and parses the phylogenetic tree for target species identified in
data/processed/post_qc_species_list.json using the Open Tree of Life API.

If the tree cannot be fetched for all species, generates a star phylogeny
and logs a warning.
"""

import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Project imports
from src.utils.config import get_data_path
from src.utils.logger import get_logger

# Constants
OPEN_TREE_API_BASE = "https://api.tree.opentreeoflife.org/v2"
TIMEOUT_SECONDS = 30
MAX_RETRIES = 3
BACKOFF_FACTOR = 0.5

# Output paths
PHYLOGENY_TREE_PATH = "data/processed/phylogenetic_tree.tre"
PHYLOGENY_STATUS_PATH = "data/manifests/phylogeny_status.json"

logger = get_logger(__name__)


def create_retry_session() -> requests.Session:
    """Create a requests session with retry logic."""
    session = requests.Session()
    retry = Retry(
        total=MAX_RETRIES,
        read=MAX_RETRIES,
        connect=MAX_RETRIES,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def load_target_species_list() -> List[str]:
    """
    Load the list of target species from the post-QC species list.

    Returns:
        List of species names (strings).

    Raises:
        FileNotFoundError: If the species list file does not exist.
        ValueError: If the file format is invalid.
    """
    data_path = get_data_path()
    species_list_path = data_path / "processed" / "post_qc_species_list.json"

    if not species_list_path.exists():
        raise FileNotFoundError(
            f"Target species list not found at {species_list_path}. "
            "Ensure T014 (QC) has completed successfully."
        )

    with open(species_list_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict) or "species" not in data:
        raise ValueError(
            f"Invalid format in {species_list_path}. Expected a dict with 'species' key."
        )

    # Handle both list of strings and list of dicts with 'species' key
    species_list = data["species"]
    if isinstance(species_list, list):
        if all(isinstance(s, str) for s in species_list):
            return species_list
        elif all(isinstance(s, dict) and "name" in s for s in species_list):
            return [s["name"] for s in species_list]

    raise ValueError(
        f"Invalid species list format in {species_list_path}. Expected list of strings or dicts."
    )


def resolve_species_to_ott_id(session: requests.Session, species_name: str) -> Optional[str]:
    """
    Resolve a species name to an OTT (Open Tree Taxonomy) ID.

    Args:
        session: Requests session with retry logic.
        species_name: Scientific name of the species.

    Returns:
        OTT ID string if found, None otherwise.
    """
    url = f"{OPEN_TREE_API_BASE}/taxonomy/search"
    params = {
        "query": species_name,
        "limit": 1,
        "rank": "species",
        "exact": True,
    }

    try:
        response = session.get(url, params=params, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()

        if "results" in data and len(data["results"]) > 0:
            ott_id = data["results"][0].get("ott_id")
            if ott_id:
                logger.debug(f"Resolved {species_name} to OTT ID: {ott_id}")
                return str(ott_id)
        logger.warning(f"Could not resolve species name to OTT ID: {species_name}")
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed for {species_name}: {e}")
        return None


def fetch_tree_for_ott_ids(
    session: requests.Session, ott_ids: List[str]
) -> Optional[Dict[str, Any]]:
    """
    Fetch the phylogenetic tree for a list of OTT IDs.

    Args:
        session: Requests session with retry logic.
        ott_ids: List of OTT IDs.

    Returns:
        Tree data dict if successful, None otherwise.
    """
    url = f"{OPEN_TREE_API_BASE}/tree/ottol"
    payload = {
        "ott_ids": ott_ids,
        "type": "phyloref",
    }

    try:
        response = session.post(url, json=payload, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()

        if "tree" in data:
            return data
        else:
            logger.warning("API returned no tree data in response.")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch tree: {e}")
        return None


def extract_newick_from_tree_data(tree_data: Dict[str, Any]) -> Optional[str]:
    """
    Extract Newick string from the API response.

    Args:
        tree_data: Raw tree data from API.

    Returns:
        Newick string if found, None otherwise.
    """
    if "tree" in tree_data:
        newick = tree_data["tree"].get("newick")
        if newick:
            logger.debug("Successfully extracted Newick string from API response.")
            return newick
    return None


def generate_star_phylogeny(species_names: List[str]) -> str:
    """
    Generate a star phylogeny Newick string.

    All species are direct children of a single root node with uniform branch lengths.

    Args:
        species_names: List of species names to include.

    Returns:
        Newick string representing the star phylogeny.
    """
    if not species_names:
        raise ValueError("Cannot generate star phylogeny for empty species list.")

    # Format species names for Newick (handle spaces by quoting if necessary)
    formatted_names = []
    for name in species_names:
        # Simple escaping: quote if contains spaces or special chars
        if any(c in name for c in " ,;():"):
            formatted_names.append(f'"{name}"')
        else:
            formatted_names.append(name)

    # Create Newick string: (SpeciesA:1.0, SpeciesB:1.0, ...);
    newick_body = ",".join(f"{name}:1.0" for name in formatted_names)
    newick_str = f"({newick_body});"

    logger.warning(
        "Generated star phylogeny. Bootstrap support threshold >=70% not met. "
        "Phylogenetic validation (FR-017) will be skipped or marked as 'not phylogenetically informed'."
    )

    return newick_str


def save_phylogeny_tree(newick_str: str, output_path: Path) -> None:
    """
    Save the Newick tree string to a file.

    Args:
        newick_str: Newick format string.
        output_path: Path to save the file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(newick_str)
    logger.info(f"Phylogenetic tree saved to {output_path}")


def save_phylogeny_status(tree_type: str, phylogenetic_informed: bool) -> None:
    """
    Save the phylogeny status to a JSON file.

    Args:
        tree_type: Type of tree generated ("real" or "star").
        phylogenetic_informed: Whether the tree is phylogenetically informed.
    """
    data_path = get_data_path()
    status_path = data_path.parent / PHYLOGENY_STATUS_PATH

    status_path.parent.mkdir(parents=True, exist_ok=True)

    status_data = {
        "tree_type": tree_type,
        "phylogenetic_informed": phylogenetic_informed,
    }

    with open(status_path, "w", encoding="utf-8") as f:
        json.dump(status_data, f, indent=2)

    logger.info(f"Phylogeny status saved to {status_path}")


def main() -> int:
    """
    Main entry point for the phylogeny fetcher.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        logger.info("Starting phylogeny fetcher (T028a)...")

        # Load target species
        species_list = load_target_species_list()
        logger.info(f"Loaded {len(species_list)} target species.")

        if not species_list:
            logger.warning("No target species found. Generating star phylogeny.")
            newick_str = generate_star_phylogeny(species_list)
            save_phylogeny_tree(newick_str, Path(PHYLOGENY_TREE_PATH))
            save_phylogeny_status("star", False)
            return 0

        # Create session with retry logic
        session = create_retry_session()

        # Resolve species to OTT IDs
        ott_ids = []
        missing_species = []

        for species in species_list:
            ott_id = resolve_species_to_ott_id(session, species)
            if ott_id:
                ott_ids.append(ott_id)
            else:
                missing_species.append(species)

        logger.info(f"Resolved {len(ott_ids)}/{len(species_list)} species to OTT IDs.")

        if not ott_ids:
            logger.error("No species could be resolved to OTT IDs. Generating star phylogeny.")
            newick_str = generate_star_phylogeny(species_list)
            save_phylogeny_tree(newick_str, Path(PHYLOGENY_TREE_PATH))
            save_phylogeny_status("star", False)
            return 0

        # Fetch tree
        tree_data = fetch_tree_for_ott_ids(session, ott_ids)

        if tree_data:
            newick_str = extract_newick_from_tree_data(tree_data)
            if newick_str:
                save_phylogeny_tree(newick_str, Path(PHYLOGENY_TREE_PATH))
                save_phylogeny_status("real", True)
                logger.info("Successfully fetched and saved phylogenetic tree.")
                return 0
            else:
                logger.warning("Tree data fetched but Newick string not found. Generating star phylogeny.")
                newick_str = generate_star_phylogeny(species_list)
                save_phylogeny_tree(newick_str, Path(PHYLOGENY_TREE_PATH))
                save_phylogeny_status("star", False)
                return 0
        else:
            logger.warning("Failed to fetch tree from API. Generating star phylogeny.")
            newick_str = generate_star_phylogeny(species_list)
            save_phylogeny_tree(newick_str, Path(PHYLOGENY_TREE_PATH))
            save_phylogeny_status("star", False)
            return 0

    except FileNotFoundError as e:
        logger.error(f"Missing input file: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Invalid data format: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during phylogeny fetch: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
