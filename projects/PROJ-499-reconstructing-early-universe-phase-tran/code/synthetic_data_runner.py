import os
import sys
import json
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent
sys.path.insert(0, str(code_dir))

from synthetic_data import (
    generate_inflation_synthetic, 
    generate_pt_synthetic, 
    generate_null_synthetic,
    serialize_inflation_ground_truth,
    serialize_pt_ground_truth,
    serialize_null_ground_truth
)

def main():
    """
    Script to generate all synthetic data and ground truth files.
    Ensures artifacts are written to disk as required by T060a-c and T061a-c.
    """
    base_dir = Path(__file__).parent.parent
    synthetic_dir = base_dir / "data" / "synthetic"
    synthetic_dir.mkdir(parents=True, exist_ok=True)

    print("Generating Inflation Synthetic Data...")
    inf_map_path = synthetic_dir / "inflation_synthetic.fits"
    generate_inflation_synthetic(str(inf_map_path), seed=42)
    serialize_inflation_ground_truth(str(synthetic_dir / "ground_truth_inflation.json"))

    print("Generating Null Synthetic Data...")
    null_map_path = synthetic_dir / "null_synthetic.fits"
    generate_null_synthetic(str(null_map_path), seed=44)
    serialize_null_ground_truth(str(synthetic_dir / "ground_truth_null.json"))

    print("Generating Phase Transition Synthetic Data...")
    pt_map_path = synthetic_dir / "pt_synthetic.fits"
    generate_pt_synthetic(str(pt_map_path), seed=43)
    serialize_pt_ground_truth(str(synthetic_dir / "ground_truth_pt.json"))

    print("Verification:")
    files = [
        inf_map_path,
        synthetic_dir / "ground_truth_inflation.json",
        null_map_path,
        synthetic_dir / "ground_truth_null.json",
        pt_map_path,
        synthetic_dir / "ground_truth_pt.json"
    ]
    for f in files:
        if f.exists():
            print(f"  OK: {f}")
        else:
            print(f"  MISSING: {f}")
            sys.exit(1)
    
    print("All synthetic artifacts generated successfully.")

if __name__ == "__main__":
    main()