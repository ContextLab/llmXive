"""
Integration utilities for combining regression and cross‑validation results.
"""
import json
from pathlib import Path
from typing import Dict, Any, List

# Updated import path
from code.utils.logging import get_logger

logger = get_logger(__name__)


def load_regression_results(regression_output_path: Path) -> Dict[str, Any]:
    with open(regression_output_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_cross_validation_results(cv_output_path: Path) -> Dict[str, Any]:
    with open(cv_output_path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_metrics_summary(regression_data: Dict[str, Any], cv_data: Dict[str, Any]) -> Dict[str, Any]:
    summary = {
        "baseline_r2": regression_data["Baseline_Dst"]["r_squared"],
        "full_r2": regression_data["Full_Dst"]["r_squared"],
        "delta_r2": regression_data["Delta_R2_Dst"],
        "cv_baseline_r2": cv_data["baseline_r2"],
        "cv_full_r2": cv_data["full_r2"],
        "cv_delta_r2": cv_data["delta_r2"],
    }
    return summary


def create_coefficients_dataframe(regression_data: Dict[str, Any]) -> pd.DataFrame:
    import pandas as pd

    rows = []
    for model_key, model_res in regression_data.items():
        if not isinstance(model_res, dict) or "coefficients" not in model_res:
            continue
        for var, coef in model_res["coefficients"].items():
            rows.append(
                {
                    "model": model_key,
                    "variable": var,
                    "coefficient": coef,
                    "p_value": model_res["pvalues"].get(var, None),
                }
            )
    return pd.DataFrame(rows)


def integrate_results(
    regression_output: Path,
    cv_output: Path,
    output_dir: Path,
    base_name: str = "regression_summary",
) -> Dict[str, Path]:
    regression_data = load_regression_results(regression_output)
    cv_data = load_cross_validation_results(cv_output)

    metrics = create_metrics_summary(regression_data, cv_data)
    coeffs_df = create_coefficients_dataframe(regression_data)

    metrics_path = output_dir / f"{base_name}_metrics.json"
    coeffs_path = output_dir / f"{base_name}_coefficients.csv"

    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    coeffs_df.to_csv(coeffs_path, index=False)

    logger.info(f"Integrated results written to {metrics_path} and {coeffs_path}")
    return {"metrics": metrics_path, "coefficients": coeffs_path}


def main() -> None:
    logger.info("Integrate results script executed as script – no action defined.")


if __name__ == "__main__":
    main()
