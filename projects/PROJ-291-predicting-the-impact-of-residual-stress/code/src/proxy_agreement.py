"""
proxy_agreement.py
------------------
Computes the agreement between measured residual stress and the deterministic
proxy (Pearson r and R²) on rows where both values are present. The result is
written to ``data/results/proxy_agreement.csv`` together with a descriptive
caveat column.
"""
import pandas as pd
from pathlib import Path
from scipy.stats import pearsonr
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def compute_proxy_agreement(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Pearson correlation and R² between ``residual_stress_measured`` and
    ``residual_stress_proxy`` for rows where both are non‑missing.

    Returns a DataFrame with a single row containing the metrics and a
    ``caveat`` column.
    """
    # Select rows with both values present
    mask = df["residual_stress_measured"].notna() & df["residual_stress_proxy"].notna()
    if mask.sum() == 0:
        raise ValueError("No rows contain both measured and proxy residual stress.")

    measured = pd.to_numeric(df.loc[mask, "residual_stress_measured"])
    proxy = pd.to_numeric(df.loc[mask, "residual_stress_proxy"])

    # Compute Pearson r
    r, _ = pearsonr(measured, proxy)
    r_squared = r ** 2

    result = pd.DataFrame(
        {
            "pearson_r": [round(r, 6)],
            "r_squared": [round(r_squared, 6)],
            "caveat": [
                "descriptive – proxy is deterministic function of predictors"
            ],
        }
    )
    return result

def write_proxy_agreement(df: pd.DataFrame) -> None:
    """
    Write the agreement DataFrame to ``data/results/proxy_agreement.csv``.
    """
    out_path: Path = paths.results("proxy_agreement.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    log.info("Proxy‑measured agreement written to %s", out_path)

def main(unified_path: Path = None) -> None:
    """
    Entry point used by the e2e runner. If *unified_path* is ``None`` the
    default location ``data/processed/unified_fatigue.csv`` is used.
    """
    if unified_path is None:
        unified_path = paths.processed("unified_fatigue.csv")
    df = pd.read_csv(unified_path)
    agreement_df = compute_proxy_agreement(df)
    write_proxy_agreement(agreement_df)

if __name__ == "__main__":
    main()
