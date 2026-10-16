"""
T016 – Power analysis
Reads the analysis-ready CSV, computes an analytical power calculation for a
multiple linear regression with up to three predictors, and writes a modeling
configuration JSON file.

Output: data/processed/modeling_config.json
    {
        "effective_n": int,
        "detectable_f2": float,
        "power": float,
        "sc001_pass": bool,
        "power_pass": bool,
        "abort_flag": bool
    }
"""
import json
import pandas as pd
from pathlib import Path
from statsmodels.stats.power import FTestPower
from utils.logging_config import get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
ANALYSIS_READY_PATH = Path("data/processed/analysis_ready.csv")
OUTPUT_CONFIG_PATH = Path("data/processed/modeling_config.json")
ALPHA = 0.05
TARGET_POWER = 0.80
MAX_PREDICTORS = 3

def load_analysis_data(csv_path: Path) -> pd.DataFrame:
    """Load the cleaned analysis‑ready CSV."""
    if not csv_path.exists():
        log.error(f"Analysis‑ready file not found: {csv_path}")
        raise FileNotFoundError(f"{csv_path} does not exist")
    df = pd.read_csv(csv_path)
    log.info(f"Loaded analysis data with {len(df)} rows")
    return df

def select_predictor_columns(df: pd.DataFrame) -> list:
    """
    Determine which columns can be used as predictors.
    Excludes identifier columns and the outcome variable.
    """
    exclude = {"participant_id", "agency_score", "user_response_trigger"}
    predictor_cols = [c for c in df.columns if c not in exclude and pd.api.types.is_numeric_dtype(df[c])]
    # Limit to the first MAX_PREDICTORS columns (spec allows up to three)
    predictor_cols = predictor_cols[:MAX_PREDICTORS]
    log.info(f"Selected predictor columns (max {MAX_PREDICTORS}): {predictor_cols}")
    return predictor_cols

def compute_power_metrics(n: int, k: int) -> dict:
    """
    Compute detectable f² and the corresponding power for a multiple‑linear
    regression with `k` predictors and sample size `n`.
    """
    if n <= k + 1:
        # Not enough degrees of freedom to perform the calculation
        raise ValueError("Insufficient sample size for the number of predictors.")

    df_num = k
    df_denom = n - k - 1

    ftest = FTestPower()
    # Detect the smallest f² that yields the target power
    detectable_f2 = ftest.solve_power(
        effect_size=None,
        df_num=df_num,
        df_denom=df_denom,
        alpha=ALPHA,
        power=TARGET_POWER,
    )
    # Verify the power for this effect size (should be ≈ TARGET_POWER)
    power = ftest.power(
        effect_size=detectable_f2,
        df_num=df_num,
        df_denom=df_denom,
        alpha=ALPHA,
    )
    log.info(
        f"Power analysis (n={n}, k={k}): detectable_f2={detectable_f2:.5f}, power={power:.5f}"
    )
    return {
        "detectable_f2": float(detectable_f2),
        "power": float(power),
    }

def build_config(df: pd.DataFrame) -> dict:
    """Assemble the modeling configuration dictionary."""
    n_samples = len(df)
    predictor_cols = select_predictor_columns(df)
    k = len(predictor_cols)

    # If there are no predictors, we cannot perform a regression power analysis.
    if k == 0:
        log.warning("No predictor columns detected; defaulting power metrics to zero.")
        power_metrics = {"detectable_f2": 0.0, "power": 0.0}
    else:
        power_metrics = compute_power_metrics(n_samples, k)

    config = {
        "effective_n": int(n_samples),
        "detectable_f2": power_metrics["detectable_f2"],
        "power": power_metrics["power"],
        "sc001_pass": n_samples >= 100,
        "power_pass": power_metrics["power"] >= TARGET_POWER,
        "abort_flag": n_samples < 80,
    }
    return config

def write_config(config: dict, out_path: Path) -> None:
    """Write the modeling configuration JSON to disk."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, sort_keys=True)
    log.info(f"Modeling config written to {out_path}")

def main() -> int:
    """Entry point for the power‑analysis script."""
    try:
        df = load_analysis_data(ANALYSIS_READY_PATH)
        config = build_config(df)
        write_config(config, OUTPUT_CONFIG_PATH)
        return 0
    except Exception as e:
        log.exception(f"Power analysis failed: {e}")
        return 1

if __name__ == "__main__":
    import sys

    sys.exit(main())
