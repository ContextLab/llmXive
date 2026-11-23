"""
Fetch perovskite crystal structures from Materials Project API.

This module implements T013: Download perovskite crystal structures from
Materials Project API with ABX₃ filtering, exponential backoff, error
handling, and deterministic retry behavior via --seed argument.

Requirements:
- FR-001: API key management and error handling
- FR-002: Schema compliance for output data
- Deterministic retries via seed argument
"""

import os
import sys
import time
import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import requests
import pandas as pd
import numpy as np
from pymatgen.core import Structure
from pymatgen.analysis.structure_analyzer import oxide_type

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config.env import load_api_key, setup_logger
from src.utils.seed_manager import init_seed, get_seed

# Constants
MP_API_BASE_URL = "https://api.materialsproject.org"
MAX_RETRIES = 5
INITIAL_BACKOFF = 1.0
BACKOFF_MULTIPLIER = 2.0
PEROVSKITE_STOICHIOMETRY = "ABX3"
OUTPUT_PATH = Path("data/raw/structures_raw.csv")
logger = setup_logger("fetch_structures")


def load_api_key() -> str:
    """Load Materials Project API key from environment."""
    api_key = os.getenv("MP_API_KEY")
    if not api_key:
        logger.error("MP_API_KEY not set in environment")
        sys.exit(1)
    return api_key


def fetch_with_backoff(
    url: str,
    params: Dict[str, Any],
    headers: Dict[str, str],
    max_retries: int = MAX_RETRIES,
    seed: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    Fetch data from URL with exponential backoff and deterministic jitter.

    Args:
        url: API endpoint URL
        params: Query parameters
        headers: Request headers
        max_retries: Maximum number of retry attempts
        seed: Random seed for deterministic jitter (optional)

    Returns:
        JSON response dict or None if all retries exhausted

    Raises:
        SystemExit: If API key is invalid or rate limit exceeded after retries
    """
    backoff = INITIAL_BACKOFF
    last_error = None

    # Initialize seed for deterministic jitter if provided
    if seed is not None:
        np.random.seed(seed)

    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                # Rate limited - exponential backoff
                jitter = np.random.uniform(0.5, 1.5) if seed is not None else 1.0
                wait_time = backoff * jitter
                logger.warning(f"Rate limited. Waiting {wait_time:.2f}s before retry {attempt + 1}/{max_retries}")
                time.sleep(wait_time)
                backoff *= BACKOFF_MULTIPLIER
            elif response.status_code == 401:
                logger.error("Authentication failed. Check MP_API_KEY.")
                sys.exit(1)
            elif response.status_code == 404:
                logger.warning(f"Resource not found: {url}")
                return None
            else:
                last_error = f"HTTP {response.status_code}: {response.text}"
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {last_error}")
                time.sleep(backoff)
                backoff *= BACKOFF_MULTIPLIER

        except requests.exceptions.Timeout:
            last_error = "Request timeout"
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {last_error}")
            time.sleep(backoff)
            backoff *= BACKOFF_MULTIPLIER
        except requests.exceptions.RequestException as e:
            last_error = str(e)
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {last_error}")
            time.sleep(backoff)
            backoff *= BACKOFF_MULTIPLIER

    logger.error(f"All {max_retries} retries exhausted. Last error: {last_error}")
    return None


def is_perovskite(structure: Structure) -> bool:
    """
    Check if a structure matches ABX₃ perovskite stoichiometry.

    Args:
        structure: pymatgen Structure object

    Returns:
        True if structure matches ABX₃ stoichiometry, False otherwise
    """
    composition = structure.composition
    elements = list(composition.elements)
    num_elements = len(elements)

    # Perovskite should have exactly 3 distinct elements (A, B, X)
    if num_elements != 3:
        return False

    # Get elemental fractions
    fractions = {el.symbol: comp for el, comp in composition.items()}

    # Sort by fraction to identify A, B, X roles
    # A is typically largest cation, B is smaller cation, X is anion
    sorted_elements = sorted(fractions.items(), key=lambda x: x[1], reverse=True)

    # ABX₃ pattern: one element at ~1/5, one at ~1/5, one at ~3/5
    # Allow some tolerance for mixed occupancies
    target_fractions = [0.2, 0.2, 0.6]
    tolerance = 0.1

    actual_fractions = [f for _, f in sorted_elements]

    # Check if fractions match ABX₃ pattern within tolerance
    matches = True
    for actual, target in zip(actual_fractions, target_fractions):
        if abs(actual - target) > tolerance:
            matches = False
            break

    return matches


def fetch_perovskite_structures(
    api_key: str,
    output_path: Path,
    seed: Optional[int] = None,
    max_structures: Optional[int] = None
) -> Tuple[int, int]:
    """
    Fetch perovskite structures from Materials Project API.

    Args:
        api_key: Materials Project API key
        output_path: Path to save output CSV
        seed: Random seed for deterministic behavior
        max_structures: Maximum number of structures to fetch (optional)

    Returns:
        Tuple of (total_fetched, perovskite_count)
    """
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }

    # Query for oxide perovskites first (most common)
    # We'll iterate through known perovskite-forming elements
    perovskite_elements = [
        # Common A-site: alkali, alkaline earth, rare earth
        "Li", "Na", "K", "Rb", "Cs", "Mg", "Ca", "Sr", "Ba", "La", "Ce",
        # Common B-site: transition metals
        "Ti", "Zr", "Hf", "V", "Nb", "Ta", "Cr", "Mo", "W", "Mn", "Fe",
        "Co", "Ni", "Cu", "Zn", "Al", "Ga", "In", "Sc", "Y",
        # X-site: O, F, Cl, Br, I
        "O", "F", "Cl", "Br", "I"
    ]

    all_structures = []
    total_fetched = 0
    perovskite_count = 0

    # Use Materials Project's materials endpoint with composition filter
    # We'll use the /materials endpoint with formula pattern matching
    base_url = f"{MP_API_BASE_URL}/materials"

    # Fetch materials with perovskite-like formulas
    # MP API supports formula pattern matching
    formula_patterns = [
        # Oxide perovskites: ABO3
        "ABO3",
        # Halide perovskites: ABX3
        "ABX3",
    ]

    # Alternative: fetch all materials and filter by composition
    # This is more reliable but slower
    logger.info("Fetching materials from Materials Project API...")

    # Use the materials endpoint with pagination
    params = {
        "pretty": "false",
        "fields": "material_id,structure,formula_pretty,nsites,nelements",
        "num_chunks": 100,
    }

    # We need to iterate through materials - MP API doesn't have a simple
    # perovskite filter, so we fetch and filter
    # For efficiency, we'll fetch a representative sample

    # Strategy: Fetch materials and filter for ABX3 stoichiometry
    cursor = None
    fetched = 0
    max_fetch = max_structures if max_structures else 10000

    while fetched < max_fetch:
        if cursor:
            params["cursor"] = cursor

        result = fetch_with_backoff(
            base_url,
            params,
            headers,
            seed=seed
        )

        if not result or "data" not in result:
            logger.warning("No more data or error fetching materials")
            break

        materials = result.get("data", [])
        if not materials:
            break

        cursor = result.get("next_cursor")

        for material in materials:
            if fetched >= max_fetch:
                break

            try:
                # Parse structure from API response
                structure_dict = material.get("structure", {})
                if not structure_dict:
                    continue

                # Convert to pymatgen Structure
                structure = Structure.from_dict(structure_dict)

                # Check if it's a perovskite
                if is_perovskite(structure):
                    perovskite_count += 1
                    total_fetched += 1

                    # Extract relevant data
                    structure_data = {
                        "structure_id": material.get("material_id"),
                        "formula_pretty": material.get("formula_pretty"),
                        "nsites": material.get("nsites"),
                        "nelements": material.get("nelements"),
                        "elements": [el.symbol for el in structure.composition.elements],
                        "lattice_a": structure.lattice.a,
                        "lattice_b": structure.lattice.b,
                        "lattice_c": structure.lattice.c,
                        "lattice_alpha": structure.lattice.alpha,
                        "lattice_beta": structure.lattice.beta,
                        "lattice_gamma": structure.lattice.gamma,
                        "volume": structure.volume,
                        "density": structure.density,
                        "is_perovskite": True,
                        "source": "Materials Project",
                    }
                    all_structures.append(structure_data)

                    logger.debug(f"Fetched perovskite: {material.get('material_id')}")

                fetched += 1

            except Exception as e:
                logger.warning(f"Error processing material {material.get('material_id')}: {e}")
                continue

        if not cursor:
            break

    logger.info(f"Total materials fetched: {fetched}, Perovskites found: {perovskite_count}")

    # Save to CSV
    if all_structures:
        df = pd.DataFrame(all_structures)
        df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(all_structures)} perovskite structures to {output_path}")
    else:
        logger.warning("No perovskite structures found in fetched data")
        # Create empty file with headers
        pd.DataFrame(columns=[
            "structure_id", "formula_pretty", "nsites", "nelements",
            "elements", "lattice_a", "lattice_b", "lattice_c",
            "lattice_alpha", "lattice_beta", "lattice_gamma",
            "volume", "density", "is_perovskite", "source"
        ]).to_csv(output_path, index=False)

    return total_fetched, perovskite_count


def main():
    """Main entry point for fetching perovskite structures."""
    parser = argparse.ArgumentParser(
        description="Fetch perovskite crystal structures from Materials Project API"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic retry behavior (default: 42)"
    )
    parser.add_argument(
        "--max-structures",
        type=int,
        default=None,
        help="Maximum number of structures to fetch (optional)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(OUTPUT_PATH),
        help=f"Output CSV path (default: {OUTPUT_PATH})"
    )

    args = parser.parse_args()

    # Initialize seed
    init_seed(args.seed)
    logger.info(f"Initialized with seed: {args.seed}")

    # Load API key
    api_key = load_api_key()
    logger.info("API key loaded successfully")

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Fetch structures
    try:
        total, perovskite_count = fetch_perovskite_structures(
            api_key=api_key,
            output_path=output_path,
            seed=args.seed,
            max_structures=args.max_structures
        )

        logger.info(f"Fetch complete: {total} total, {perovskite_count} perovskites")

        # Verify output
        if output_path.exists():
            df = pd.read_csv(output_path)
            logger.info(f"Output verification: {len(df)} rows in {output_path}")

            # Check for required columns
            required_cols = ["structure_id", "formula_pretty", "is_perovskite"]
            missing = [col for col in required_cols if col not in df.columns]
            if missing:
                logger.error(f"Missing required columns: {missing}")
                sys.exit(1)

            # Filter for perovskites only
            perovskites = df[df["is_perovskite"] == True]
            logger.info(f"Perovskite count in output: {len(perovskites)}")

            if len(perovskites) == 0:
                logger.warning("No perovskites found in output - check API connectivity and stoichiometry filter")

        else:
            logger.error(f"Output file not created: {output_path}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error during fetch: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
