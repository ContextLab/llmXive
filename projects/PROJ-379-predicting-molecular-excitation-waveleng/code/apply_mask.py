import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json_file(filepath: Path) -> Any:
    """Load a JSON file and return its contents."""
    if not filepath.exists():
        raise FileNotFoundError(f"Required file not found: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(filepath: Path, data: Any) -> None:
    """Save data to a JSON file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)
    logger.info(f"Saved output to: {filepath}")

def apply_masks_to_attribution(
    raw_attribution: Dict[str, List[float]],
    masks: Dict[str, List[int]]
) -> Dict[str, List[float]]:
    """
    Apply redundancy masks to raw attribution weights.
    
    Args:
        raw_attribution: Dictionary mapping molecule_id to list of raw weights.
        masks: Dictionary mapping molecule_id to list of mask values (0 or 1).
    
    Returns:
        Dictionary mapping molecule_id to list of masked weights.
    """
    masked_attribution = {}
    for mol_id, weights in raw_attribution.items():
        if mol_id not in masks:
            logger.warning(f"No mask found for molecule {mol_id}, keeping raw weights.")
            masked_attribution[mol_id] = weights
            continue
        
        mask = masks[mol_id]
        if len(weights) != len(mask):
            raise ValueError(
                f"Length mismatch for molecule {mol_id}: "
                f"weights={len(weights)}, mask={len(mask)}"
            )
        
        # Apply mask: weight * mask (0 masks out the weight)
        masked_weights = [w * m for w, m in zip(weights, mask)]
        masked_attribution[mol_id] = masked_weights
    
    return masked_attribution

def verify_masking_effect(
    raw_attribution: Dict[str, List[float]],
    masked_attribution: Dict[str, List[float]]
) -> Dict[str, Dict[str, Any]]:
    """
    Verify that masking actually changed the values where expected.
    
    Returns a summary of changes per molecule.
    """
    summary = {}
    for mol_id in raw_attribution:
        raw = raw_attribution[mol_id]
        masked = masked_attribution.get(mol_id, raw)
        
        # Count how many weights were zeroed out
        zeroed_count = sum(1 for r, m in zip(raw, masked) if r != 0 and m == 0)
        changed_count = sum(1 for r, m in zip(raw, masked) if r != m)
        
        summary[mol_id] = {
            "total_features": len(raw),
            "zeroed_out": zeroed_count,
            "changed": changed_count,
            "unchanged": len(raw) - changed_count
        }
    return summary

def main():
    parser = argparse.ArgumentParser(description="Apply redundancy masks to raw attribution.")
    parser.add_argument(
        "--raw-attribution",
        type=str,
        default="data/processed/raw_attribution.json",
        help="Path to raw attribution JSON"
    )
    parser.add_argument(
        "--masks",
        type=str,
        default="data/processed/redundancy_masks.json",
        help="Path to redundancy masks JSON"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/masked_attribution.json",
        help="Path for output masked attribution JSON"
    )
    parser.add_argument(
        "--verification-report",
        type=str,
        default="data/processed/masking_verification.json",
        help="Path for verification report JSON"
    )
    
    args = parser.parse_args()
    
    logger.info(f"Loading raw attribution from: {args.raw_attribution}")
    raw_data = load_json_file(Path(args.raw_attribution))
    
    logger.info(f"Loading redundancy masks from: {args.masks}")
    mask_data = load_json_file(Path(args.masks))
    
    logger.info("Applying masks to raw attribution...")
    masked_data = apply_masks_to_attribution(raw_data, mask_data)
    
    logger.info("Verifying masking effect...")
    verification = verify_masking_effect(raw_data, masked_data)
    
    # Save masked attribution
    save_json_file(Path(args.output), masked_data)
    
    # Save verification report
    save_json_file(Path(args.verification_report), verification)
    
    # Print summary stats
    total_molecules = len(verification)
    total_zeroed = sum(v["zeroed_out"] for v in verification.values())
    total_features = sum(v["total_features"] for v in verification.values())
    
    logger.info(f"Processing complete.")
    logger.info(f"  Molecules processed: {total_molecules}")
    logger.info(f"  Total features masked: {total_zeroed} / {total_features}")
    
    if total_zeroed == 0:
        logger.warning("No features were masked. Check if redundancy masks are all 1s.")
    else:
        logger.info(f"Successfully masked {total_zeroed} feature attributions.")

if __name__ == "__main__":
    main()