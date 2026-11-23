"""
Dataset generator for the Participation Ratio analysis (T010).
Iterates over all disorder widths, system sizes and realisations defined in the
configuration, invokes ``analyze_single_realization`` and writes the combined
result to ``data/processed/pr_raw_multiL.json``.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

from code.config import get_config
from code.analyze_pr import analyze_single_realization

logger = logging.getLogger(__name__)


def generate_multiL_pr_dataset() -> List[Dict[str, Any]]:
    """
    Generate the full PR dataset across the (W, L) grid.

    Returns
    -------
    List[Dict[str, Any]]
        All per‑eigenstate records ready for downstream scaling analysis.
    """
    cfg = get_config()
    W_list = cfg["W_LIST"]
    L_list = cfg["L_LIST"]
    n_real = cfg["NUM_REALIZATIONS"]
    base_seed = cfg["SEED"]

    all_records: List[Dict[str, Any]] = []
    for W in W_list:
        for L in L_list:
            for r_idx in range(n_real):
                seed = base_seed + r_idx
                records = analyze_single_realization(
                    W=W,
                    L=L,
                    seed=seed,
                    realization_index=r_idx,
                )
                all_records.extend(records)
    return all_records


def main() -> None:
    """
    Entry point used by the orchestration script (``code/main.py``).
    Writes the dataset to the expected location.
    """
    dataset = generate_multiL_pr_dataset()
    output_path = Path("data/processed/pr_raw_multiL.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(dataset, f, indent=2)
    logger.info(f"PR dataset written to {output_path} ({len(dataset)} records)")


if __name__ == "__main__":
    main()
