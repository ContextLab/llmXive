"""
Script to create minimal, schema‑compliant placeholder artifacts required
for the contract‑validation test suite (Task T001).

It uses the canonical ``write_artifact`` function to generate the JSON
files and pandas to create the Parquet/CSV files with the minimal
non‑empty rows demanded by the tests.
"""
import pandas as pd
from pathlib import Path

from utils.artifacts import write_artifact

# -----------------------------------------------------------------
# Helper to get project‑wide data directories via llmxive_toolkit
# -----------------------------------------------------------------
from llmxive_toolkit import paths

def _ensure_dir(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)

def create_json_artifact(name: str, data: dict) -> None:
    """
    Write a JSON artifact using the canonical writer.
    """
    out_path = paths.data("processed", f"{name}.json")
    _ensure_dir(out_path)
    write_artifact(out_path, data, name)

def main() -> int:
    # 1. JSON artifacts (permissive schemas allow empty objects)
    empty_json = {}
    for name in [
        "single_run_results",
        "convergence_report",
        "aggregated_thresholds",
        "threshold_fit",
        "sensitivity_metadata",
        "perturbation_verification",
    ]:
        create_json_artifact(name, empty_json)

    # 2. Parquet artifacts with required columns and a single dummy row
    sweep_df = pd.DataFrame(
        [
            {
                "N": 1000,
                "theta": 0.5,
                "run_id": 1,
                "outlier_flag": 0,
            }
        ]
    )
    sweep_path = paths.data("processed", "sweep_runs.parquet")
    _ensure_dir(sweep_path)
    sweep_df.to_parquet(sweep_path, engine="pyarrow")

    density_df = pd.DataFrame(
        [
            {
                "N": 1000,
                "density": 0.1,
                "theta": 0.5,
                "run_id": 1,
                "outlier_flag": 0,
            }
        ]
    )
    density_path = paths.data("processed", "sensitivity_density_sweep.parquet")
    _ensure_dir(density_path)
    density_df.to_parquet(density_path, engine="pyarrow")

    # 3. CSV artifacts with required columns and a single dummy row
    variation_df = pd.DataFrame(
        [
            {
                "density": 0.1,
                "mean_theta_c": 1.0,
                "std_dev": 0.1,
            }
        ]
    )
    variation_path = paths.data("processed", "sensitivity_variation.csv")
    _ensure_dir(variation_path)
    variation_df.to_csv(variation_path, index=False)

    finite_df = pd.DataFrame(
        [
            {
                "N": 1000,
                "k": 1,
                "theta": 0.5,
                "pattern_type": "diagonal",
                "empirical_bulk_edge": 2.0,
                "outlier_probability": 0.0,
            }
        ]
    )
    finite_path = paths.data("processed", "finite_size_results.csv")
    _ensure_dir(finite_path)
    finite_df.to_csv(finite_path, index=False)

    # 4. Additional JSON notes artifact (empty object is acceptable)
    create_json_artifact("sensitivity_variation_notes", empty_json)

    print("Placeholder artifacts created successfully.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
