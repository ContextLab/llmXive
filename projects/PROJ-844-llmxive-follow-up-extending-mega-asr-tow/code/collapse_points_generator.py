"""
Collapse Points Generator for User Story 2 (T022).

This script reads the generated stress curves, applies the collapse detection logic
(identifying the intensity where SSS < 0.5 * baseline_sss AND WER > 2 * baseline_wer),
and writes the results to `data/derived/collapse_points.parquet`.

It relies on pre-computed baseline files:
- data/derived/baseline_sss.json
- data/derived/baseline_wer.json
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

# Add project root to path to ensure imports work in all environments
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_config, get_default_paths
from metrics import get_config as metrics_get_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_baselines(config: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    """Load baseline SSS and WER values from JSON files."""
    paths = get_default_paths()
    
    sss_path = paths['data_derived'] / 'baseline_sss.json'
    wer_path = paths['data_derived'] / 'baseline_wer.json'

    if not sss_path.exists() or not wer_path.exists():
        raise FileNotFoundError(
            f"Baseline files missing. Expected: {sss_path}, {wer_path}. "
            "Run T020b and T020c first."
        )

    with open(sss_path, 'r') as f:
        baseline_sss = json.load(f)
    with open(wer_path, 'r') as f:
        baseline_wer = json.load(f)

    # Normalize structure: {model_id: {scenario_id: {'sss': val, 'wer': val}}}
    baselines = {}
    for model_id in baseline_sss.keys():
        baselines[model_id] = {}
        for scenario_id in baseline_sss[model_id].keys():
            baselines[model_id][scenario_id] = {
                'baseline_sss': baseline_sss[model_id][scenario_id],
                'baseline_wer': baseline_wer.get(model_id, {}).get(scenario_id, 0.0)
            }
    
    return baselines

def detect_collapse_point(
    group_df: pd.DataFrame,
    baseline_sss: float,
    baseline_wer: float
) -> Optional[Dict[str, Any]]:
    """
    Identify the collapse point for a specific model/scenario group.
    
    Criteria:
    1. SSS < 0.5 * baseline_sss
    2. WER > 2.0 * baseline_wer
    
    Returns the first intensity vector (lowest intensity) that satisfies both.
    If no collapse is found, returns None (or could return max tested).
    """
    if baseline_sss == 0:
        logger.warning(f"Baseline SSS is 0 for this group. Skipping collapse detection.")
        return None

    # Sort by intensity (assuming 'intensity_level' or similar numeric column exists)
    # We assume the stress curve is already sorted by intensity in the generation step.
    # If not, we sort here.
    if 'intensity_level' not in group_df.columns:
        # Fallback: sort by a proxy if intensity_level is missing, or assume row order
        logger.warning("intensity_level column missing. Assuming row order represents intensity.")
        sorted_df = group_df.reset_index(drop=True)
    else:
        sorted_df = group_df.sort_values('intensity_level')

    threshold_sss = 0.5 * baseline_sss
    threshold_wer = 2.0 * baseline_wer

    collapse_point = None

    for idx, row in sorted_df.iterrows():
        current_sss = row.get('sss_score', np.nan)
        current_wer = row.get('wer_score', np.nan)

        if pd.isna(current_sss) or pd.isna(current_wer):
            continue

        # Check criteria
        if current_sss < threshold_sss and current_wer > threshold_wer:
            collapse_point = {
                'model_id': row['model_id'],
                'scenario_id': row['scenario_id'],
                'collapse_intensity': row.get('intensity_level', idx),
                'sss_at_collapse': current_sss,
                'wer_at_collapse': current_wer,
                'threshold_sss': threshold_sss,
                'threshold_wer': threshold_wer,
                'status': 'collapsed'
            }
            break # Found the first collapse point

    if collapse_point is None:
        # No collapse found within tested range.
        # Per T021, record as "Max Tested"
        max_row = sorted_df.iloc[-1]
        collapse_point = {
            'model_id': max_row['model_id'],
            'scenario_id': max_row['scenario_id'],
            'collapse_intensity': max_row.get('intensity_level', 'max_tested'),
            'sss_at_collapse': max_row.get('sss_score', np.nan),
            'wer_at_collapse': max_row.get('wer_score', np.nan),
            'threshold_sss': threshold_sss,
            'threshold_wer': threshold_wer,
            'status': 'no_collapse'
        }
    
    return collapse_point

def generate_collapse_points(stress_curves_path: Path, baselines: Dict) -> pd.DataFrame:
    """Process stress curves and generate collapse points DataFrame."""
    if not stress_curves_path.exists():
        raise FileNotFoundError(f"Stress curves file not found: {stress_curves_path}")

    logger.info(f"Loading stress curves from {stress_curves_path}")
    df = pd.read_parquet(stress_curves_path)

    if df.empty:
        raise ValueError("Stress curves DataFrame is empty.")

    logger.info(f"Loaded {len(df)} rows. Columns: {df.columns.tolist()}")

    results = []
    
    # Group by model and scenario
    group_cols = ['model_id', 'scenario_id']
    # Ensure these columns exist
    missing_cols = [c for c in group_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in stress curves: {missing_cols}")

    for (model_id, scenario_id), group_df in df.groupby(group_cols):
        key = f"{model_id}_{scenario_id}"
        if model_id not in baselines or scenario_id not in baselines[model_id]:
            logger.warning(f"Skipping {model_id}/{scenario_id}: No baseline data found.")
            continue

        baseline_data = baselines[model_id][scenario_id]
        point = detect_collapse_point(
            group_df, 
            baseline_data['baseline_sss'], 
            baseline_data['baseline_wer']
        )
        if point:
            results.append(point)

    if not results:
        logger.warning("No collapse points detected for any group.")
        return pd.DataFrame()

    return pd.DataFrame(results)

def main():
    parser = argparse.ArgumentParser(description="Generate collapse points from stress curves.")
    parser.add_argument('--input-path', type=str, help='Path to stress_curves.parquet')
    parser.add_argument('--output-path', type=str, help='Path to output collapse_points.parquet')
    args = parser.parse_args()

    config = get_config() # Accepts no args or one, handled by config.py fix
    paths = get_default_paths()

    input_path = Path(args.input_path) if args.input_path else paths['data_derived'] / 'stress_curves.parquet'
    output_path = Path(args.output_path) if args.output_path else paths['data_derived'] / 'collapse_points.parquet'

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        baselines = load_baselines(config)
        collapse_df = generate_collapse_points(input_path, baselines)
        
        if not collapse_df.empty:
            collapse_df.to_parquet(output_path, index=False)
            logger.info(f"Successfully wrote collapse points to {output_path}")
            logger.info(f"Total collapse points identified: {len(collapse_df)}")
            # Log summary of status
            status_counts = collapse_df['status'].value_counts()
            logger.info(f"Status distribution:\n{status_counts}")
        else:
            logger.warning("No collapse points generated. Output file not created.")
            # Still create an empty file to satisfy the "file exists" check if needed, 
            # but usually empty is fine. Let's create an empty one with schema.
            schema_df = pd.DataFrame(columns=[
                'model_id', 'scenario_id', 'collapse_intensity', 
                'sss_at_collapse', 'wer_at_collapse', 'threshold_sss', 
                'threshold_wer', 'status'
            ])
            schema_df.to_parquet(output_path, index=False)
            logger.info(f"Created empty schema file at {output_path}")

    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise

if __name__ == '__main__':
    main()
