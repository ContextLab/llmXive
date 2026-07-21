"""
T013f: Generate Real Family-Based Split.

Creates a stratified train/test split based on chemical prototype/family.
Ensures no family overlap between training and test sets (SC-002).
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Set

import numpy as np
import pandas as pd
from pymatgen.core import Composition
from sklearn.model_selection import train_test_split

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def load_graphs_from_parquet(input_path: Path) -> pd.DataFrame:
    """Load the processed graphs parquet file."""
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    try:
        df = pd.read_parquet(input_path)
        logger.info(f"Loaded {len(df)} entries from {input_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load parquet file: {e}")
        sys.exit(1)

def derive_family_id(composition_str: str) -> str:
    """
    Derive a chemical family ID from a composition string using pymatgen.

    Groups by 'chemical prototype' logic:
    - Identify the dominant structural motif or stoichiometry class.
    - For this implementation, we group by the set of elements and their
      primary stoichiometric ratios (simplified to element set + count).
    - Specific known families (MXene, TMD, Graphene) are handled if identifiable
      by element composition patterns.
    """
    if not composition_str:
        return "Unknown"

    try:
        comp = Composition(composition_str)
        elements = set(comp.elements)
        element_symbols = sorted([el.symbol for el in elements])

        # Heuristic 1: Specific known families based on element composition
        # Graphene-like: Only Carbon
        if element_symbols == ["C"] and comp.num_atoms == 1:
            return "Graphene"

        # MXene-like: Transition metals + C/N (e.g., Ti2C, Mo2C)
        # Simplified: Contains C or N + Transition Metal
        transition_metals = {
            "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn",
            "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd",
            "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg"
        }
        if "C" in element_symbols or "N" in element_symbols:
            if any(el in transition_metals for el in element_symbols):
                # Check for specific stoichiometry patterns if needed,
                # but element set is a strong proxy for prototype in this context.
                return "MXene"

        # TMD-like: Transition Metal + Chalcogen (S, Se, Te)
        chalcogens = {"S", "Se", "Te"}
        if any(el in chalcogens for el in element_symbols):
            if any(el in transition_metals for el in element_symbols):
                return "TMD"

        # Heuristic 2: General stoichiometry class (e.g., AB, AB2, A2B3)
        # Normalize formula to smallest integer ratio to group by prototype
        formula_dict = comp.get_el_amt_dict()
        # Get the reduced formula string (e.g., "Ti2C" -> "Ti2C")
        # We use the string representation of the reduced composition
        reduced_formula = comp.reduced_formula

        # If specific family detection failed, use the reduced formula as the family ID
        # This groups materials with the same stoichiometry (e.g., all "MoS2" together)
        return reduced_formula

    except Exception as e:
        logger.warning(f"Could not parse composition '{composition_str}': {e}")
        return "Unknown"

def generate_family_split(df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42) -> Dict[str, List[int]]:
    """
    Generate a stratified split based on family_id.

    Requirement: Ensure no training family appears in the test set.
    This is achieved by stratifying on the family_id, which groups all
    instances of a family together in either train or test.
    """
    logger.info("Deriving family IDs from chemical compositions...")

    # Derive family_id for each row
    # Assuming 'composition' column exists in the dataframe (standard from pipeline)
    if 'composition' not in df.columns:
        logger.error("Column 'composition' not found in dataframe. Cannot derive family IDs.")
        sys.exit(1)

    df = df.copy()
    df['family_id'] = df['composition'].apply(derive_family_id)

    # Check for sufficient families
    unique_families = df['family_id'].nunique()
    logger.info(f"Identified {unique_families} unique chemical families.")

    if unique_families < 2:
        logger.error("Not enough unique families to perform a train/test split.")
        sys.exit(1)

    # Stratified split
    # sklearn's train_test_split with stratify ensures that the distribution
    # of family_ids is preserved, but more importantly, if we treat family_id
    # as the label, it tries to keep the ratio.
    # However, to strictly ensure NO family overlap, we must split by unique families.
    # Standard train_test_split does NOT guarantee that all instances of a class
    # go to one side unless we manually group them.
    #
    # Strategy:
    # 1. Get unique families.
    # 2. Split the list of unique families into train_families and test_families.
    # 3. Assign indices based on which family they belong to.

    families = df['family_id'].unique()
    logger.info(f"Splitting {len(families)} families into train/test sets...")

    train_families, test_families = train_test_split(
        families,
        test_size=test_size,
        random_state=random_state,
        shuffle=True
    )

    logger.info(f"Training families: {len(train_families)}, Test families: {len(test_families)}")

    # Verify disjoint
    if set(train_families) & set(test_families):
        logger.error("CRITICAL: Family overlap detected between train and test sets.")
        sys.exit(1)

    # Map indices
    train_indices = df[df['family_id'].isin(train_families)].index.tolist()
    test_indices = df[df['family_id'].isin(test_families)].index.tolist()

    logger.info(f"Generated split: {len(train_indices)} train, {len(test_indices)} test")

    return {
        "train_indices": train_indices,
        "test_indices": test_indices,
        "train_families": list(train_families),
        "test_families": list(test_families),
        "random_state": random_state
    }

def verify_family_separation(split_data: Dict[str, Any], df: pd.DataFrame) -> bool:
    """
    Runtime assertion: Verify no family is present in both train and test.
    """
    train_indices = split_data['train_indices']
    test_indices = split_data['test_indices']

    train_families = set(df.loc[train_indices, 'family_id'].unique())
    test_families = set(df.loc[test_indices, 'family_id'].unique())

    intersection = train_families & test_families

    if intersection:
        logger.error(f"VERIFICATION FAILED: The following families appear in BOTH train and test sets: {intersection}")
        return False

    logger.info("VERIFICATION PASSED: No family overlap between train and test sets.")
    return True

def save_split(split_data: Dict[str, Any], output_path: Path) -> None:
    """Save the split indices and metadata to a JSON file."""
    if output_path.exists():
        logger.warning(f"Overwriting existing split file: {output_path}")

    try:
        with open(output_path, 'w') as f:
            json.dump(split_data, f, indent=2)
        logger.info(f"Split saved to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save split file: {e}")
        sys.exit(1)

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a family-based stratified split for 2D materials."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the input parquet file (e.g., data/processed/graphs_v1.parquet)"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to the output JSON split file (e.g., data/processed/split_indices.json)"
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Proportion of families to use for testing (default: 0.2)"
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load data
    df = load_graphs_from_parquet(input_path)

    # Generate split
    split_data = generate_family_split(df, test_size=args.test_size, random_state=args.random_state)

    # Verify separation
    if not verify_family_separation(split_data, df):
        logger.error("Family separation verification failed. Aborting.")
        sys.exit(1)

    # Save split
    save_split(split_data, output_path)

    logger.info("Task T013f completed successfully.")

if __name__ == "__main__":
    main()