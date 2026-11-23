import os
import sys
import logging
import csv
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

from utils.config import get_project_root, get_data_processed_path
from analysis.metadata_utils import add_associational_only_flag_to_csv

logger = logging.getLogger(__name__)

def load_halo_shapes() -> pd.DataFrame:
    """Load the processed halo shapes data."""
    path = get_data_processed_path("halo_shapes.csv")
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}")
    logger.info(f"Loading halo shapes from {path}")
    return pd.read_csv(path)

def load_galaxy_properties() -> pd.DataFrame:
    """Load the galaxy properties data."""
    path = get_data_processed_path("galaxy_properties.csv")
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}")
    logger.info(f"Loading galaxy properties from {path}")
    return pd.read_csv(path)

def load_alignment_angles() -> pd.DataFrame:
    """Load the computed alignment angles data."""
    path = get_data_processed_path("alignment_angles.csv")
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}")
    logger.info(f"Loading alignment angles from {path}")
    return pd.read_csv(path)

def merge_datasets(
    halo_shapes: pd.DataFrame,
    galaxy_props: pd.DataFrame,
    alignment_angles: pd.DataFrame
) -> pd.DataFrame:
    """Merge the three datasets on halo_id/galaxy_id to create a unified analysis table."""
    # Standardize column names if necessary (assuming T038 output has 'halo_id' and 'galaxy_id')
    # T038 output: alignment_angles.csv should have halo_id, galaxy_id, spin_spin_angle, major_major_angle
    # T017 output: halo_shapes.csv should have halo_id, b_a_ratio, c_a_ratio, triaxiality, mass
    # T011/T012 output: galaxy_properties.csv should have galaxy_id, halo_id, sfr, radius, ...

    # Ensure we have the join keys
    required_keys = ['halo_id', 'galaxy_id']
    for df_name, df in [("halo_shapes", halo_shapes), ("galaxy_props", galaxy_props), ("alignment_angles", alignment_angles)]:
        missing = [k for k in required_keys if k not in df.columns]
        if missing:
            raise ValueError(f"Dataset {df_name} missing required keys: {missing}")

    # Merge alignment with galaxy properties first (1:1 or 1:N depending on simulation)
    # Assuming one alignment entry per galaxy in the subset
    merged = pd.merge(
        alignment_angles,
        galaxy_props,
        on=['halo_id', 'galaxy_id'],
        how='inner'
    )
    logger.info(f"Merged alignment and galaxy properties: {len(merged)} rows")

    # Merge with halo shapes (many galaxies per halo -> halo properties broadcast)
    merged = pd.merge(
        merged,
        halo_shapes[['halo_id', 'b_a_ratio', 'c_a_ratio', 'triaxiality', 'mass']],
        on='halo_id',
        how='inner'
    )
    logger.info(f"Merged with halo shapes: {len(merged)} rows")

    return merged

def compute_correlations(
    df: pd.DataFrame,
    predictor: str,
    outcome: str,
    method: str = 'spearman'
) -> Dict[str, Any]:
    """
    Compute correlation coefficient and p-value between predictor and outcome.
    Handles NaNs by dropping rows.
    """
    valid = df[[predictor, outcome]].dropna()
    if len(valid) < 3:
        return {
            'predictor': predictor,
            'outcome': outcome,
            'n': 0,
            'correlation': np.nan,
            'p_value': np.nan,
            'method': method,
            'status': 'insufficient_data'
        }

    if method == 'pearson':
        corr, p = scipy_stats.pearsonr(valid[predictor], valid[outcome])
    elif method == 'spearman':
        corr, p = scipy_stats.spearmanr(valid[predictor], valid[outcome])
    elif method == 'kendall':
        corr, p = scipy_stats.kendalltau(valid[predictor], valid[outcome])
    else:
        raise ValueError(f"Unknown correlation method: {method}")

    return {
        'predictor': predictor,
        'outcome': outcome,
        'n': len(valid),
        'correlation': corr,
        'p_value': p,
        'method': method,
        'status': 'success'
    }

def run_correlation_analysis(
    df: pd.DataFrame,
    predictors: List[str],
    outcomes: List[str],
    method: str = 'spearman'
) -> List[Dict[str, Any]]:
    """Run correlation analysis for all combinations of predictors and outcomes."""
    results = []
    for pred in predictors:
        for out in outcomes:
            res = compute_correlations(df, pred, out, method)
            results.append(res)
            logger.debug(f"Correlation {pred} vs {out}: r={res['correlation']:.4f}, p={res['p_value']:.4e}")
    return results

def save_results(results: List[Dict[str, Any]], output_path: Path):
    """Save correlation results to CSV."""
    if not results:
        logger.warning("No results to save.")
        return

    # Flatten results for CSV
    fieldnames = ['predictor', 'outcome', 'n', 'correlation', 'p_value', 'method', 'status']
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    logger.info(f"Saved {len(results)} correlation results to {output_path}")

def main():
    """Main entry point for T039: Correlation analysis for misalignment angles vs galaxy properties."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # 1. Load Data
        logger.info("Starting T039: Correlation Analysis")
        halo_shapes = load_halo_shapes()
        galaxy_props = load_galaxy_properties()
        alignment_angles = load_alignment_angles()

        # 2. Merge
        merged_df = merge_datasets(halo_shapes, galaxy_props, alignment_angles)
        logger.info(f"Total rows for analysis: {len(merged_df)}")

        if len(merged_df) == 0:
            raise ValueError("Merged dataset is empty. Cannot proceed with analysis.")

        # 3. Define Analysis Variables
        # Predictors: Misalignment angles (from T038 output)
        predictors = ['spin_spin_angle', 'major_major_angle']
        # Outcomes: Galaxy properties (SFR, radius)
        outcomes = ['sfr', 'radius']

        # Verify columns exist
        missing_pred = [p for p in predictors if p not in merged_df.columns]
        missing_out = [o for o in outcomes if o not in merged_df.columns]
        if missing_pred or missing_out:
            raise ValueError(f"Missing columns: Predictors {missing_pred}, Outcomes {missing_out}")

        # 4. Run Analysis
        correlation_results = run_correlation_analysis(
            merged_df,
            predictors=predictors,
            outcomes=outcomes,
            method='spearman' # Robust to non-normality
        )

        # 5. Save Output
        output_filename = "misalignment_correlations.csv"
        output_path = get_data_processed_path(output_filename)
        save_results(correlation_results, output_path)

        # 6. Apply Associational Flag (T026 requirement)
        logger.info(f"Applying associational_only flag to {output_path}")
        add_associational_only_flag_to_csv(output_path)

        logger.info("T039 completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Missing required data file: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during T039: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
