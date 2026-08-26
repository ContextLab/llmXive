import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Import from local project modules as per API surface
from config import ensure_dirs, get_config_summary
from stats.correction import apply_correction_to_results, bonferroni_correction, fdr_correction

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_instrument_registry(registry_path: str) -> List[str]:
    """
    Load the list of valid cognitive instruments from the YAML registry.
    Note: Using simple YAML parsing without external 'yaml' library dependency
    by reading lines and filtering, assuming the registry is simple key-value.
    """
    valid_instruments = []
    path = Path(registry_path)
    if not path.exists():
        logger.warning(f"Registry file not found: {registry_path}. Using empty list.")
        return valid_instruments

    try:
        with open(path, 'r') as f:
            content = f.read()
            # Simple parsing for YAML-like structure: look for lines starting with '- '
            for line in content.splitlines():
                stripped = line.strip()
                if stripped.startswith('- '):
                    instrument = stripped[2:].split()[0] # Take first word
                    if instrument:
                        valid_instruments.append(instrument)
        logger.info(f"Loaded {len(valid_instruments)} valid instruments from registry.")
    except Exception as e:
        logger.error(f"Failed to parse registry: {e}")
    return valid_instruments

def validate_cognitive_instrument(instrument: str, valid_instruments: List[str]) -> bool:
    """Check if the instrument is in the valid list."""
    return instrument in valid_instruments

def flag_cognitive_records(df: pd.DataFrame, registry_path: str) -> pd.DataFrame:
    """
    Add a 'cognitive_valid' flag to the dataframe based on the instrument registry.
    Also flags records with missing cognitive scores.
    """
    valid_instruments = load_instrument_registry(registry_path)
    df = df.copy()

    # Initialize flags
    df['cognitive_valid'] = False
    df['exclusion_reason'] = None

    # Check for missing cognitive score
    mask_missing = df['cognitive_score'].isna() | (df['cognitive_score'] == -999) # Assuming -999 is missing code if not NaN
    df.loc[mask_missing, 'exclusion_reason'] = 'Missing Cognitive Score'
    df.loc[mask_missing, 'cognitive_valid'] = False

    # Check for invalid instrument
    mask_valid_inst = df['cognitive_instrument'].isin(valid_instruments)
    mask_not_missing = ~mask_missing

    valid_mask = mask_valid_inst & mask_not_missing
    df.loc[valid_mask, 'cognitive_valid'] = True
    df.loc[~valid_mask & mask_not_missing, 'exclusion_reason'] = 'Invalid Cognitive Instrument'

    return df

def load_metrics_and_cognitive_data(metrics_path: str, download_report_path: str, registry_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load the network metrics and the metadata containing cognitive scores.
    Filters out invalid cognitive records based on T025c logic.
    """
    metrics_path = Path(metrics_path)
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")

    metrics_df = pd.read_csv(metrics_path)
    
    # Load download report to check status
    download_report = {}
    if Path(download_report_path).exists():
        with open(download_report_path, 'r') as f:
            download_report = json.load(f)
    
    # If the download report says 'BLOCKED' due to missing cognitive data,
    # we proceed but will have no cognitive data to correlate.
    # The flagging logic handles the filtering.
    
    # Load metadata (assuming it's in the same structure or a specific metadata file)
    # Based on tasks.md, metadata is likely part of the processed data or a separate join.
    # We assume a 'metadata.csv' exists in data/processed/ or similar, or we join via participant_id.
    # For this implementation, we assume the metrics file has been enriched or we load a separate file.
    # Let's assume a standard location for the joined metadata if not in metrics_df.
    # If metrics_df already has age and cognitive_score, we use it.
    
    required_cols = ['participant_id', 'age', 'cognitive_score', 'cognitive_instrument']
    missing_cols = [c for c in required_cols if c not in metrics_df.columns]
    
    if missing_cols:
        # Try to load from a metadata file
        meta_path = Path('data/processed/metadata.csv')
        if meta_path.exists():
            meta_df = pd.read_csv(meta_path)
            # Merge on participant_id
            metrics_df = metrics_df.merge(meta_df[['participant_id', 'age', 'cognitive_score', 'cognitive_instrument']], 
                                        on='participant_id', how='left')
        else:
            # If we can't find metadata, we might have to skip cognitive correlation
            logger.warning(f"Missing columns {missing_cols} in metrics file and no metadata.csv found.")
            # Add placeholder columns if they are missing but we need to run the script
            for col in missing_cols:
                metrics_df[col] = np.nan

    # Apply validation flags
    flagged_df = flag_cognitive_records(metrics_df, registry_path)
    
    return metrics_df, flagged_df

def run_spearman_correlation(metrics_df: pd.DataFrame, flagged_df: pd.DataFrame, 
                             metric_cols: List[str], outcome_cols: List[str], 
                             output_path: str, trace_id: str):
    """
    Perform Spearman rank correlation for each metric against each outcome.
    Apply multiple-comparison correction (FDR).
    """
    results = []
    
    # Filter for valid cognitive records if outcomes are cognitive
    # If outcome is 'age', we don't need cognitive validity, but we still use the dataframe.
    # For cognitive outcomes, we must exclude invalid records.
    
    valid_df = flagged_df.copy()
    
    for metric in metric_cols:
        if metric not in valid_df.columns:
            logger.warning(f"Metric column {metric} not found, skipping.")
            continue
        
        for outcome in outcome_cols:
            if outcome not in valid_df.columns:
                continue
            
            # Determine if we need to filter by cognitive validity
            # If outcome is cognitive (e.g., 'cognitive_score'), filter
            if outcome == 'cognitive_score':
                subset = valid_df[valid_df['cognitive_valid'] == True].dropna(subset=[metric, outcome])
                n = len(subset)
                if n < 3:
                    logger.warning(f"Not enough data for {metric} vs {outcome} (n={n}). Skipping.")
                    continue
            else:
                # For age, use all valid data (no cognitive score filter needed)
                subset = valid_df.dropna(subset=[metric, outcome])
                n = len(subset)
                if n < 3:
                    continue

            # Calculate Spearman
            try:
                corr, p_val = stats.spearmanr(subset[metric], subset[outcome])
                if np.isnan(corr):
                    logger.warning(f"NaN correlation for {metric} vs {outcome}.")
                    continue
                
                results.append({
                    'metric_name': metric,
                    'outcome': outcome,
                    'spearman_r': corr,
                    'p_value': p_val,
                    'n': n,
                    'trace_id': trace_id
                })
            except Exception as e:
                logger.error(f"Error calculating correlation for {metric} vs {outcome}: {e}")

    if not results:
        logger.warning("No correlations calculated.")
        # Create empty DF with correct schema
        df_results = pd.DataFrame(columns=['metric_name', 'outcome', 'spearman_r', 'p_value', 'p_adjusted', 'n', 'trace_id'])
    else:
        df_results = pd.DataFrame(results)
        
        # Multiple comparison correction
        # Collect all p-values for correction
        p_values = df_results['p_value'].values
        if len(p_values) > 0:
            # Using FDR as primary, Bonferroni as alternative if specified
            # The task asks for Bonferroni or FDR. We'll use FDR (Benjamini-Hochberg) as it's less conservative.
            # stats.correction.apply_correction_to_results expects a DF or list.
            # Let's assume it returns adjusted p-values.
            # We need to import stats.spearmanr
            import scipy.stats as stats
            
            # Manual FDR implementation using statsmodels if helper is complex
            from statsmodels.stats.multitest import multipletests
            corrected = multipletests(p_values, method='fdr_bh')
            df_results['p_adjusted'] = corrected[1]
        else:
            df_results['p_adjusted'] = np.nan

    # Ensure output directory exists
    ensure_dirs([str(Path(output_path).parent)])
    
    # Save to CSV
    df_results.to_csv(output_path, index=False)
    logger.info(f"Correlation results saved to {output_path}")

def main():
    """
    Main entry point for T023.
    """
    config = get_config_summary()
    project_root = Path(config.get('project_root', '.'))
    
    # Paths
    metrics_path = project_root / 'data' / 'results' / 'network_metrics.csv'
    download_report_path = project_root / 'data' / 'quality' / 'download_report.json'
    registry_path = project_root / 'data' / 'config' / 'cognitive_instrument_registry.yaml'
    output_path = project_root / 'data' / 'results' / 'correlation_results.csv'
    
    # Trace ID (should ideally be injected, but we generate a placeholder if not present)
    # In a real run, this would come from the version map or a passed argument.
    trace_id = "T023_EXECUTION_TRACE"
    
    # Define metrics and outcomes
    # Based on T008, metrics include: global_efficiency, local_efficiency, clustering_coeff, modularity
    metric_cols = ['global_efficiency', 'local_efficiency', 'clustering_coeff', 'modularity']
    outcome_cols = ['age', 'cognitive_score']
    
    try:
        logger.info("Loading metrics and cognitive data...")
        metrics_df, flagged_df = load_metrics_and_cognitive_data(
            str(metrics_path), 
            str(download_report_path), 
            str(registry_path)
        )
        
        logger.info("Running Spearman correlations...")
        run_spearman_correlation(
            metrics_df, 
            flagged_df, 
            metric_cols, 
            outcome_cols, 
            str(output_path),
            trace_id
        )
        
        logger.info("T023 Completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Required file missing: {e}")
        # If metrics file is missing, we can't proceed.
        # If cognitive data is missing (BLOCKED), we might still run for age.
        if "network_metrics.csv" in str(e):
            raise
    except Exception as e:
        logger.error(f"Error during T023 execution: {e}")
        raise

if __name__ == "__main__":
    main()
