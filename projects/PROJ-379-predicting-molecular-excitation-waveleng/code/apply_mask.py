import os
import sys
import json
import logging
import argparse
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def load_json_file(path: Path) -> dict:
    """Load a JSON file and return its contents as a dictionary."""
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json_file(path: Path, data: dict) -> None:
    """Save a dictionary to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved output to {path}")

def apply_masks_to_attribution(
    raw_attribution: dict,
    redundancy_masks: dict
) -> dict:
    """
    Apply redundancy masks to raw attribution results.

    For each molecule entry in raw_attribution:
      - Check if its subgraph_id is flagged as redundant in redundancy_masks.
      - If redundant, set all attribution weights to 0.0.
      - Otherwise, keep the original weights.

    Args:
        raw_attribution (dict): Dictionary of raw attribution results.
        redundancy_masks (dict): Dictionary mapping subgraph_id to boolean (True = redundant).

    Returns:
        dict: Masked attribution results.
    """
    masked_results = {}

    for mol_id, mol_data in raw_attribution.items():
        subgraph_id = mol_data.get("subgraph_id")
        original_weights = mol_data.get("weights", {})

        if subgraph_id is None:
            logger.warning(f"Missing subgraph_id for molecule {mol_id}, skipping masking.")
            masked_results[mol_id] = mol_data
            continue

        is_redundant = redundancy_masks.get(subgraph_id, False)

        if is_redundant:
            # Zero out weights for redundant subgraphs
            masked_weights = {k: 0.0 for k in original_weights}
            logger.info(f"Molecule {mol_id} (subgraph {subgraph_id}) marked redundant. Weights zeroed.")
        else:
            # Keep original weights
            masked_weights = original_weights
            logger.debug(f"Molecule {mol_id} (subgraph {subgraph_id}) not redundant. Weights preserved.")

        masked_results[mol_id] = {
            "subgraph_id": subgraph_id,
            "weights": masked_weights,
            "is_redundant": is_redundant
        }

    return masked_results

def verify_masking_effect(masked_attribution: dict, redundancy_masks: dict) -> bool:
    """
    Verify that all flagged redundant subgraphs have zeroed weights in the masked attribution.

    Args:
        masked_attribution (dict): The masked attribution results.
        redundancy_masks (dict): The redundancy masks (subgraph_id -> bool).

    Returns:
        bool: True if all redundant subgraphs have zeroed weights, False otherwise.
    """
    all_valid = True
    for mol_id, mol_data in masked_attribution.items():
        subgraph_id = mol_data.get("subgraph_id")
        weights = mol_data.get("weights", {})
        is_redundant = mol_data.get("is_redundant", False)

        if is_redundant and subgraph_id in redundancy_masks and redundancy_masks[subgraph_id]:
            # Check if all weights are zero
            if not all(w == 0.0 for w in weights.values()):
                logger.error(f"Masking verification failed for {mol_id}: redundant subgraph has non-zero weights.")
                all_valid = False
        else:
            # Ensure non-redundant subgraphs are not zeroed (unless they were naturally zero)
            # This is a soft check; we mostly care that redundant ones ARE zeroed.
            pass

    return all_valid

def main():
    """Main entry point for T025: Apply and verify masking."""
    parser = argparse.ArgumentParser(description="Apply redundancy masks to attribution results.")
    parser.add_argument(
        "--raw-attribution",
        type=str,
        default="data/processed/raw_attribution.json",
        help="Path to raw attribution JSON"
    )
    parser.add_argument(
        "--redundancy-masks",
        type=str,
        default="data/processed/redundancy_masks.json",
        help="Path to redundancy masks JSON"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/masked_attribution.json",
        help="Path to output masked attribution JSON"
    )
    args = parser.parse_args()

    raw_path = Path(args.raw_attribution)
    masks_path = Path(args.redundancy_masks)
    output_path = Path(args.output)

    try:
        logger.info(f"Loading raw attribution from {raw_path}")
        raw_attribution = load_json_file(raw_path)

        logger.info(f"Loading redundancy masks from {masks_path}")
        redundancy_masks = load_json_file(masks_path)

        logger.info("Applying masks to attribution...")
        masked_attribution = apply_masks_to_attribution(raw_attribution, redundancy_masks)

        logger.info(f"Saving masked attribution to {output_path}")
        save_json_file(output_path, masked_attribution)

        logger.info("Verifying masking effect...")
        is_valid = verify_masking_effect(masked_attribution, redundancy_masks)

        if is_valid:
            logger.info("Masking verification PASSED: All redundant subgraphs have zeroed weights.")
        else:
            logger.error("Masking verification FAILED: Some redundant subgraphs have non-zero weights.")
            sys.exit(1)

    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format in input file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during masking: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
