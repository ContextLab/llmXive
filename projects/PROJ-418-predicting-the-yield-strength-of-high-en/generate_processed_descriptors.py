"""
Task T200 – Generate the processed descriptor dataset.

This script is deliberately separate from the core pipeline so that it can
be invoked both from the quick‑start entry point (src/pipeline/run.py) and
directly in tests.  It performs the following steps:

1. Load the raw HEA CSV (downloaded by T140) via ``load_raw_dataset``.
2. Pre‑process the raw data (filtering, unit normalisation) via
   ``preprocess_data``.
3. Compute compositional descriptors (δ, Δχ, VEC, mixing entropy,
   melting‑temperature variance, …) via ``calculate_descriptors``.
4. Compute the Variance Inflation Factor (VIF) for every descriptor.
5. Drop any descriptor whose VIF exceeds a conservative threshold
   (default 5.0) – this constitutes the “remediation” step.
6. Write the final, VIF‑cleaned descriptor table to
   ``data/processed/hea_descriptors.csv``.
"""
import os
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor

from data.load_dataset import load_raw_dataset
from data.preprocess import preprocess_data
from data.descriptors import calculate_descriptors
from utils.logging import get_logger

OUTPUT_PATH = os.path.join("data", "processed", "hea_descriptors.csv")
VIF_THRESHOLD = 5.0  # descriptors with VIF > 5 are considered collinear


def compute_vif(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the Variance Inflation Factor for each column in ``df``.
    Returns a DataFrame with columns ``feature`` and ``VIF``.
    """
    # VIF cannot be computed on non‑numeric columns; ensure numeric only
    numeric_df = df.select_dtypes(include="number")
    if numeric_df.empty:
        raise ValueError("No numeric columns available for VIF computation.")

    vif_data = pd.DataFrame()
    vif_data["feature"] = numeric_df.columns
    # variance_inflation_factor expects a 2‑D numpy array
    vif_data["VIF"] = [
        variance_inflation_factor(numeric_df.values, i)
        for i in range(numeric_df.shape[1])
    ]
    return vif_data


def remediate_descriptors(df: pd.DataFrame, vif_df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop descriptor columns whose VIF exceeds ``VIF_THRESHOLD``.
    """
    high_vif = vif_df[vif_df["VIF"] > VIF_THRESHOLD]["feature"].tolist()
    if high_vif:
        get_logger(__name__).info(
            "Dropping %d descriptor(s) due to high VIF: %s",
            len(high_vif),
            ", ".join(high_vif),
        )
    return df.drop(columns=high_vif, errors="ignore")


def main() -> None:
    logger = get_logger(__name__)

    # ------------------------------------------------------------------
    # 1. Load raw dataset
    # ------------------------------------------------------------------
    logger.info("Loading raw HEA dataset from data/raw/heas_raw.csv")
    raw_df = load_raw_dataset()
    logger.debug("Raw dataset shape: %s", raw_df.shape)

    # ------------------------------------------------------------------
    # 2. Pre‑process
    # ------------------------------------------------------------------
    logger.info("Pre‑processing raw data")
    preprocessed_df = preprocess_data(raw_df)
    logger.debug("Pre‑processed shape: %s", preprocessed_df.shape)

    # ------------------------------------------------------------------
    # 3. Descriptor calculation
    # ------------------------------------------------------------------
    logger.info("Calculating compositional descriptors")
    descriptor_df = calculate_descriptors(preprocessed_df)
    logger.debug(
        "Descriptor dataframe shape (before VIF): %s", descriptor_df.shape
    )

    # ------------------------------------------------------------------
    # 4. VIF computation
    # ------------------------------------------------------------------
    logger.info("Computing VIF for descriptors")
    vif_df = compute_vif(descriptor_df)
    logger.debug("VIF dataframe:\n%s", vif_df)

    # ------------------------------------------------------------------
    # 5. Remediation (drop high‑VIF descriptors)
    # ------------------------------------------------------------------
    logger.info("Remediating descriptor set based on VIF")
    cleaned_df = remediate_descriptors(descriptor_df, vif_df)
    logger.debug(
        "Descriptor dataframe shape (after VIF remediation): %s",
        cleaned_df.shape,
    )

    # ------------------------------------------------------------------
    # 6. Write to disk
    # ------------------------------------------------------------------
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    cleaned_df.to_csv(OUTPUT_PATH, index=False)
    logger.info("Processed descriptor dataset written to %s", OUTPUT_PATH)


if __name__ == "__main__":
    main()
