import pandas as pd
import logging
from pathlib import Path
from typing import Optional
from src.config import load_config

logger = logging.getLogger(__name__)

def save_correlation_results(
    results_df: pd.DataFrame,
    output_path: Optional[str] = None,
    status: str = "success"
) -> None:
    """
    Save correlation results to CSV.

    Expected columns in results_df:
    - sample_id
    - diversity_index
    - sleep_metric
    - r (Spearman correlation coefficient)
    - p (raw p-value)
    - q (FDR-adjusted p-value)
    - is_moderate (boolean)
    - is_significant (boolean)

    Args:
        results_df: DataFrame containing correlation results.
        output_path: Path to the output CSV file. Defaults to config.
        status: Status string to append (e.g., 'success', 'blocked').
    """
    config = load_config()
    if output_path is None:
        output_path = config.get("OUTPUT_CORRELATION_PATH", "data/processed/correlation_results.csv")

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if results_df.empty:
        logger.warning("Correlation results DataFrame is empty. Saving empty file with status=blocked.")
        blocked_df = pd.DataFrame(columns=[
            "sample_id", "diversity_index", "sleep_metric", "r", "p", "q",
            "is_moderate", "is_significant", "status"
        ])
        blocked_df["status"] = "blocked"
        blocked_df.to_csv(output_file, index=False)
    else:
        # Ensure status column exists
        if "status" not in results_df.columns:
            results_df["status"] = status

        # Reorder columns to match expected schema
        expected_cols = [
            "sample_id", "diversity_index", "sleep_metric", "r", "p", "q",
            "is_moderate", "is_significant", "status"
        ]
        
        # Only keep columns that exist in the dataframe, then append missing ones if any
        # (though run_correlation_analysis should produce them)
        final_cols = [c for c in expected_cols if c in results_df.columns]
        missing_cols = [c for c in expected_cols if c not in results_df.columns]
        
        if missing_cols:
            logger.warning(f"Missing expected columns: {missing_cols}. Adding them with default values.")
            for col in missing_cols:
                if col == "status":
                    results_df[col] = status
                else:
                    results_df[col] = None

        # Select and order columns
        results_df = results_df[expected_cols]
        
        results_df.to_csv(output_file, index=False)
        logger.info(f"Saved correlation results to {output_file} ({len(results_df)} rows).")
