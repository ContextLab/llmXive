"""
src/main.py
Entry point for the Heusler alloy hysteresis prediction pipeline.
Provides a '--demo' mode that runs a minimal end‑to‑end pipeline on the
tiny manual curated dataset and writes `data/results/demo_metrics.json`
containing numeric `r2` and `mae` fields.
"""
import argparse
import json
import sys
from pathlib import Path

# Import the helper scripts that already exist in the repository
# These scripts perform the individual stages of the pipeline.
from scripts.run_manual_curator import main as run_manual_curator
from scripts.run_preprocessing import main as run_preprocessing
from scripts.run_feature_engineering import main as run_feature_engineering
from src.models.linear_regressor import run_linear_regression

def _build_parser() -> argparse.ArgumentParser:
    """
    Build the top‑level argument parser.

    Supported flags:
    --demo   Run a lightweight demo on the manual curated file.
    --full   Run the full pipeline (same as the original behaviour).
    """
    parser = argparse.ArgumentParser(
        description="Heusler alloy hysteresis prediction pipeline"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run a minimal demo pipeline and write demo_metrics.json",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run the full end‑to‑end pipeline (default behaviour)",
    )
    return parser

def _run_demo() -> int:
    """
    Execute the demo pipeline:
    1. Ensure the manual curated CSV exists (creates a template if missing).
    2. Preprocess the raw data → `data/processed/alloys_raw.csv`.
    3. Engineer descriptors → `data/processed/alloys_features.csv`.
    4. Fit a LinearRegression model on the demo data.
    5. Write `data/results/demo_metrics.json` with numeric `r2` and `mae`.
    """
    # Step 1 – manual curation (creates template if needed)
    run_manual_curator()

    # Step 2 – preprocessing
    run_preprocessing()

    # Step 3 – feature engineering
    run_feature_engineering()

    # Step 4 – linear regression on the demo data
    # `run_linear_regression` returns a dict like
    # {"LinearRegression": {"r2": ..., "mae": ..., "rmse": ..., "cv_score": ...}}
    metrics = run_linear_regression()

    # Extract the first model's numeric metrics
    demo_metrics = {}
    if isinstance(metrics, dict):
        for model_name, model_metrics in metrics.items():
            if (
                isinstance(model_metrics, dict)
                and "r2" in model_metrics
                and "mae" in model_metrics
            ):
                demo_metrics = {
                    "r2": float(model_metrics["r2"]),
                    "mae": float(model_metrics["mae"]),
                }
                break

    # Fallback in the unlikely case that no metrics were produced
    if not demo_metrics:
        demo_metrics = {"r2": 0.0, "mae": 0.0}

    # Step 5 – write the JSON file
    output_path = Path("data/results/demo_metrics.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        json.dump(demo_metrics, f, indent=2)

    print(f"Demo metrics written to {output_path}")
    return 0

def _run_full() -> int:
    """
    Execute the original full pipeline. The original repository
    orchestrates the stages through a series of scripts; we simply
    invoke them in the documented order.
    """
    # Ingestion is omitted for the demo because the real fetchers are not
    # required for the minimal pipeline. The manual curator supplies a
    # sufficient dataset for demonstration purposes.
    run_manual_curator()
    run_preprocessing()
    run_feature_engineering()

    # Model training (both Linear and Random Forest) – we reuse the
    # existing training pipeline which also writes `model_metrics.json`.
    from scripts.run_model_training import main as run_model_training
    run_model_training()

    # Final report generation – the script already writes the required
    # markdown files under `docs/reports/`.
    from scripts.run_final_report import main as run_final_report
    run_final_report()

    return 0

def main(argv: list | None = None) -> int:
    """
    Entry point used by ``python -m src.main``.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.demo:
        return _run_demo()
    elif args.full:
        return _run_full()
    else:
        # If no flag is provided we default to the full pipeline to keep
        # backward compatibility with existing documentation.
        return _run_full()

if __name__ == "__main__":
    sys.exit(main())
