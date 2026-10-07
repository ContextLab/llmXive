"""
T032c: Verify strict nesting of all sparsity subsets.

Input: All sparsity_<level>pct.csv files in data/processed/
Output: data/metadata/nesting_verification.json with boolean is_strictly_nested
"""
import os
import sys
import json
import argparse
from pathlib import Path
import pandas as pd
from utils.logging import get_logger

logger = get_logger()

def load_subset_indices(
    data_dir: Path,
    sparsity_levels: list[int]
) -> dict[int, set]:
    """
    Load the 'material_id' column from each sparsity subset file.
    
    Args:
        data_dir: Path to data/processed/
        sparsity_levels: List of percentage levels to check (e.g., [1, 2, 5, 10, ...])
        
    Returns:
        Dict mapping level -> set of material_ids
    """
    indices_map = {}
    for level in sparsity_levels:
        filename = f"sparsity_{level}pct.csv"
        filepath = data_dir / filename
        
        if not filepath.exists():
            logger.error(f"Required file missing: {filepath}")
            raise FileNotFoundError(f"Missing sparsity subset: {filename}")
        
        try:
            df = pd.read_csv(filepath)
            # Assume the primary key is 'material_id' based on T024/T031 flow
            if 'material_id' not in df.columns:
                # Fallback: use first column if material_id is missing but we need IDs
                first_col = df.columns[0]
                logger.warning(f"File {filename} missing 'material_id', using '{first_col}'")
                ids = set(df[first_col].astype(str))
            else:
                ids = set(df['material_id'].astype(str))
            
            indices_map[level] = ids
            logger.info(f"Loaded {len(ids)} items for {level}%")
        except Exception as e:
            logger.error(f"Failed to load {filename}: {e}")
            raise

    return indices_map

def verify_nesting(
    indices_map: dict[int, set],
    levels: list[int]
) -> dict:
    """
    Verify that subsets are strictly nested in descending order.
    
    Rule: Level X% must be a strict subset of Level Y% where Y > X.
    Specifically, we check the chain: 1% ⊂ 2% ⊂ 5% ⊂ ... ⊂ 100%
    
    Args:
        indices_map: Dict of level -> set of IDs
        levels: Sorted list of levels (ascending)
        
    Returns:
        Dict with verification results
    """
    if not levels:
        return {"is_strictly_nested": False, "reason": "No levels provided"}

    sorted_levels = sorted(levels)
    is_nested = True
    details = []

    # Check chain: sorted_levels[i] must be subset of sorted_levels[i+1]
    for i in range(len(sorted_levels) - 1):
        lower_level = sorted_levels[i]
        higher_level = sorted_levels[i + 1]
        
        set_lower = indices_map[lower_level]
        set_higher = indices_map[higher_level]
        
        is_subset = set_lower.issubset(set_higher)
        is_strict = len(set_lower) < len(set_higher)
        
        if not is_subset:
            is_nested = False
            missing = set_lower - set_higher
            details.append({
                "check": f"{lower_level}% ⊂ {higher_level}%",
                "status": "FAILED",
                "reason": f"Not a subset. Missing {len(missing)} items in higher level.",
                "sample_missing": list(missing)[:5]
            })
        elif not is_strict:
            # Technically a subset, but not strictly smaller (could be equal)
            # For sparsity, we expect strictly smaller counts usually, 
            # but the requirement is "strictly nested" implying proper subset.
            # If counts are equal, it's not a strict subset.
            is_nested = False
            details.append({
                "check": f"{lower_level}% ⊂ {higher_level}%",
                "status": "FAILED",
                "reason": f"Not a strict subset. Counts are equal ({len(set_lower)}).",
                "count_lower": len(set_lower),
                "count_higher": len(set_higher)
            })
        else:
            details.append({
                "check": f"{lower_level}% ⊂ {higher_level}%",
                "status": "PASSED",
                "count_lower": len(set_lower),
                "count_higher": len(set_higher)
            })

    return {
        "is_strictly_nested": is_nested,
        "levels_checked": sorted_levels,
        "details": details
    }

def main():
    parser = argparse.ArgumentParser(description="Verify strict nesting of sparsity subsets")
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/processed",
        help="Directory containing sparsity CSV files"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/metadata/nesting_verification.json",
        help="Output path for verification JSON"
    )
    parser.add_argument(
        "--levels",
        type=str,
        default="1,2,5,10,20,30,40,50,100",
        help="Comma-separated list of sparsity levels to check"
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    output_path = Path(args.output)
    levels = [int(x.strip()) for x in args.levels.split(",")]

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting nesting verification for levels: {levels}")
    
    try:
        # 1. Load all subsets
        indices_map = load_subset_indices(data_dir, levels)
        
        # 2. Verify nesting
        result = verify_nesting(indices_map, levels)
        
        # 3. Save result
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
        
        if result["is_strictly_nested"]:
            logger.info("Verification PASSED: All subsets are strictly nested.")
        else:
            logger.error("Verification FAILED: Nesting constraints violated.")
            for detail in result["details"]:
                if detail["status"] == "FAILED":
                    logger.error(f"  - {detail['check']}: {detail['reason']}")
        
        # Exit with code 1 if failed, to block pipeline if necessary
        if not result["is_strictly_nested"]:
            sys.exit(1)

    except FileNotFoundError as e:
        logger.critical(f"Critical error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error during verification: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()