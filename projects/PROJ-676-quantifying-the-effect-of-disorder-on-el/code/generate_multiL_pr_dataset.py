"""
Generate a PR dataset for all disorder widths and system sizes.

This script creates `data/processed/pr_raw_multiL.json`, which contains a list of
dictionaries with keys: W, L, realization_index, energy, pr.

It uses the existing `analyze_single_realization` function from
`code.analyze_pr` to generate Hamiltonians, compute eigenstates, and evaluate
participation ratios.
"""
import json
from pathlib import Path
from typing import List, Dict, Any

from code.config import get_config
from code.analyze_pr import analyze_single_realization

def generate_multiL_pr_dataset() -> List[Dict[str, Any]]:
    """
    Generate PR data for every combination of disorder width, system size,
    and realization index defined in the configuration.

    Returns:
        A list of dictionaries, each representing a single eigenstate record.
    """
    config = get_config()
    W_list: List[float] = config["W_LIST"]
    L_list: List[int] = config["L_LIST"]
    n_realizations: int = config["NUM_REALIZATIONS"]
    base_seed: int = config["SEED"]

    all_records: List[Dict[str, Any]] = []

    for W in W_list:
        for L in L_list:
            for idx in range(n_realizations):
                # Derive a deterministic seed per realization to ensure reproducibility
                seed = base_seed + idx + int(W * 1000) + L
                # The analyze_single_realization function returns a list of records,
                # one per eigenstate within the energy window.
                records = analyze_single_realization(
                    W=W,
                    L=L,
                    seed=seed,
                    realization_index=idx,
                )
                all_records.extend(records)

    return all_records

def main() -> None:
    """
    Entry point for the script. Writes the dataset to the expected location.
    """
    output_path = Path("data/processed/pr_raw_multiL.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    dataset = generate_multiL_pr_dataset()
    with open(output_path, "w") as f:
        json.dump(dataset, f, indent=2)

    print(f"Generated PR dataset with {len(dataset)} records at {output_path}")

if __name__ == "__main__":
    main()
