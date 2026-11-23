import json
from pathlib import Path

import pandas as pd

def test_mc_results_row_count():
    """The sweep must produce exactly 1008 rows as specified."""
    csv_path = Path("data") / "processed" / "mc_results.csv"
    assert csv_path.is_file(), f"{csv_path} does not exist"
    df = pd.read_csv(csv_path)
    assert len(df) == 1008, f"Expected 1008 rows, got {len(df)}"

def test_convergence_data_exists_and_structure():
    """The convergence JSON must exist and contain expected top‑level keys."""
    json_path = Path("data") / "processed" / "convergence_data.json"
    assert json_path.is_file(), f"{json_path} does not exist"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Basic sanity checks
    required_keys = {"description", "theoretical_edge", "generated_at", "per_N"}
    assert required_keys.issubset(data.keys()), f"Missing keys in convergence JSON: {required_keys - data.keys()}"
    assert isinstance(data["per_N"], list) and len(data["per_N"]) > 0, "per_N should be a non‑empty list"
    for entry in data["per_N"]:
        for k in ("N", "bulk_edge_mean", "abs_deviation_from_2"):
            assert k in entry, f"Missing '{k}' in per_N entry"