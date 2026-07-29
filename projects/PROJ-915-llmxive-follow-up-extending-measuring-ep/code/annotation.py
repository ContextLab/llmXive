"""
Annotation module for generating deterministic mock labels and pilot data.
Implements T017a, T017b, T017c, T017d, T017e, and T027a.
"""
import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import numpy as np
import pandas as pd

from config import get_config
from error_handling import DatasetDownloadError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
RANDOM_SEED = 42
MOCK_LABELS_COUNT = 50
LABELS = [0, 1, 2]  # 0: Resilient-Correct, 1: Adherent, 2: Resilient-Refusal

def log_pipeline_event(stage: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Log a pipeline event to the pipeline log."""
    config = get_config()
    log_path = Path(config.pipeline_log_path)
    
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "stage": stage,
        "cumulative_seconds": 0,  # Updated by validation module in real runs
        "status": status,
        "details": details or {}
    }
    
    if log_path.exists():
        with open(log_path, 'r') as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
    else:
        logs = []
    
    logs.append(event)
    
    with open(log_path, 'w') as f:
        json.dump(logs, f, indent=2)
    
    logger.info(f"Logged event: {stage} - {status}")

def load_subset_data() -> pd.DataFrame:
    """Load the MedMisBench subset from data/raw/medmis_subset.csv."""
    config = get_config()
    input_path = Path(config.medmis_subset_path)
    
    if not input_path.exists():
        raise DatasetDownloadError(f"Subset data not found at {input_path}. Run ingestion first.")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def load_feature_data() -> pd.DataFrame:
    """Load extracted features from data/processed/features.csv."""
    config = get_config()
    input_path = Path(config.features_path)
    
    if not input_path.exists():
        raise DatasetDownloadError(f"Feature data not found at {input_path}. Run feature extraction first.")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows of features from {input_path}")
    return df

def load_annotation_data() -> pd.DataFrame:
    """Load existing cached annotation data if available."""
    config = get_config()
    input_path = Path(config.human_pilot_cached_path)
    
    if input_path.exists():
        df = pd.read_csv(input_path)
        logger.info(f"Loaded cached pilot data: {len(df)} rows")
        return df
    
    logger.info("No cached pilot data found.")
    return pd.DataFrame()

def save_pilot_cache(df: pd.DataFrame, output_path: str) -> None:
    """Save pilot data to cache."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"Saved pilot cache to {output_path}")

def generate_deterministic_pilot(features_df: pd.DataFrame, n_samples: int = MOCK_LABELS_COUNT) -> pd.DataFrame:
    """
    Generate a reproducible dataset of n=50 mock adherence labels (T027a).
    
    Method: Read prompt IDs from features_df. Generate adherence_label (0, 1, 2)
    using a deterministic function of linguistic features plus fixed random noise.
    
    Output: DataFrame with columns [prompt_id, adherence_label].
    """
    np.random.seed(RANDOM_SEED)
    
    if len(features_df) < n_samples:
        logger.warning(f"Feature dataset has {len(features_df)} rows, sampling {len(features_df)} for mock labels.")
        n_samples = len(features_df)
    
    # Sample rows deterministically
    sampled_indices = np.random.choice(len(features_df), size=n_samples, replace=False)
    sampled_df = features_df.iloc[sampled_indices].copy()
    
    # Extract relevant features for mock label generation
    # Using: modal_freq, imperative_ratio, citation_density (with safe defaults)
    modal_freq = sampled_df.get('modal_freq', 0.0).fillna(0.0)
    imperative_ratio = sampled_df.get('imperative_ratio', 0.0).fillna(0.0)
    citation_density = sampled_df.get('citation_density', 0.0).fillna(0.0)
    
    # Deterministic function: weighted sum of features + noise
    # Higher authority density (modal_freq + imperative_ratio) -> higher chance of Adherent (1)
    # Higher citation density -> higher chance of Resilient-Correct (0)
    # Noise added for variability but seeded for reproducibility
    noise = np.random.normal(0, 0.1, n_samples)
    score = (0.4 * modal_freq + 0.4 * imperative_ratio - 0.2 * citation_density + noise)
    
    # Map score to labels:
    # score < -0.3 -> 0 (Resilient-Correct)
    # -0.3 <= score <= 0.3 -> 1 (Adherent)
    # score > 0.3 -> 2 (Resilient-Refusal)
    labels = np.select(
        [score < -0.3, score <= 0.3],
        [0, 1],
        default=2
    )
    
    result_df = pd.DataFrame({
        'prompt_id': sampled_df['prompt_id'],
        'adherence_label': labels
    })
    
    logger.info(f"Generated {len(result_df)} mock adherence labels with distribution: {dict(pd.Series(labels).value_counts())}")
    return result_df

def aggregate_rater_responses(rater_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate multiple rater responses into a single score per prompt."""
    if rater_df.empty:
        return pd.DataFrame()
    
    # Group by prompt_id and compute mean authority_density_score
    aggregated = rater_df.groupby('prompt_id')['authority_density_score'].mean().reset_index()
    aggregated.columns = ['prompt_id', 'authority_density_score']
    return aggregated

def merge_data_for_correlation(features_df: pd.DataFrame, pilot_df: pd.DataFrame) -> pd.DataFrame:
    """Merge feature data with pilot data for correlation analysis."""
    merged = pd.merge(
        features_df,
        pilot_df,
        on='prompt_id',
        how='inner'
    )
    logger.info(f"Merged {len(merged)} rows for correlation analysis")
    return merged

def compute_correlations(merged_df: pd.DataFrame) -> Dict[str, float]:
    """Compute Pearson/Spearman correlation between features and human ratings."""
    results = {}
    
    # Map human rating column to feature columns
    if 'authority_density_score' in merged_df.columns:
        target_col = 'authority_density_score'
        
        # Correlate with key linguistic features
        for feature in ['modal_freq', 'imperative_ratio', 'citation_density']:
            if feature in merged_df.columns:
                # Pearson correlation
                pearson_corr, pearson_p = merged_df[feature].corr(merged_df[target_col], method='pearson')
                results[f'pearson_{feature}'] = pearson_corr
                
                # Spearman correlation
                spearman_corr, spearman_p = merged_df[feature].corr(merged_df[target_col], method='spearman')
                results[f'spearman_{feature}'] = spearman_corr
    
    return results

def generate_validation_report(correlations: Dict[str, float], threshold: float = 0.6) -> Dict[str, Any]:
    """Generate a validation report based on correlation thresholds."""
    # Find max correlation
    max_corr = max(abs(v) for v in correlations.values()) if correlations else 0.0
    
    status = "Pass" if max_corr > threshold else "Warning"
    
    report = {
        "max_correlation": max_corr,
        "threshold": threshold,
        "status": status,
        "correlations": correlations,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return report

def run_annotation_generate_pipeline() -> None:
    """
    Main pipeline for T027a: Generate Deterministic Mock Labels (Outcome).
    
    Steps:
    1. Load feature data (T014 output)
    2. Generate n=50 mock adherence labels
    3. Save to data/interim/human_pilot_labels_mock.csv
    """
    log_pipeline_event("T027a_Start", "running", {"n_samples": MOCK_LABELS_COUNT})
    
    try:
        # Load feature data
        features_df = load_feature_data()
        
        # Generate mock labels
        mock_labels_df = generate_deterministic_pilot(features_df, n_samples=MOCK_LABELS_COUNT)
        
        # Save output
        config = get_config()
        output_path = Path(config.human_pilot_labels_mock_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        mock_labels_df.to_csv(output_path, index=False)
        
        logger.info(f"Successfully generated {len(mock_labels_df)} mock labels at {output_path}")
        log_pipeline_event("T027a_Complete", "success", {"output_path": str(output_path), "rows": len(mock_labels_df)})
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        log_pipeline_event("T027a_Failed", "failed", {"error": str(e)})
        raise

def run_annotation_correlation_pipeline() -> None:
    """
    Pipeline for T017c/T017d: Compute correlation and validate.
    """
    log_pipeline_event("T017c_Start", "running")
    
    try:
        # Load data
        features_df = load_feature_data()
        pilot_df = load_annotation_data()
        
        if pilot_df.empty:
            raise RuntimeError("No pilot data found. Run T017a first.")
        
        # Aggregate and merge
        aggregated_pilot = aggregate_rater_responses(pilot_df)
        merged_df = merge_data_for_correlation(features_df, aggregated_pilot)
        
        if merged_df.empty:
            raise RuntimeError("No merged data for correlation.")
        
        # Compute correlations
        correlations = compute_correlations(merged_df)
        
        # Save correlation results
        config = get_config()
        corr_path = Path(config.annotation_correlation_path)
        corr_path.parent.mkdir(parents=True, exist_ok=True)
        with open(corr_path, 'w') as f:
            json.dump(correlations, f, indent=2)
        
        # Generate validation report
        report = generate_validation_report(correlations)
        report_path = Path(config.feature_validation_report_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        log_pipeline_event("T017c_Complete", "success", {"correlations": correlations})
        
        # T017d: Check threshold
        if report["status"] == "Warning":
            log_pipeline_event("T017d_Gate", "warning", report)
        else:
            log_pipeline_event("T017d_Gate", "pass", report)
        
    except Exception as e:
        logger.error(f"Correlation pipeline failed: {e}", exc_info=True)
        log_pipeline_event("T017c_Failed", "failed", {"error": str(e)})
        raise

def main():
    """Entry point for the annotation module."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Annotation pipeline for mock labels and pilot data")
    parser.add_argument('--mode', choices=['generate_labels', 'compute_correlations', 'full'], default='generate_labels',
                        help='Mode to run: generate_labels (T027a), compute_correlations (T017c), or full')
    
    args = parser.parse_args()
    
    if args.mode == 'generate_labels':
        run_annotation_generate_pipeline()
    elif args.mode == 'compute_correlations':
        run_annotation_correlation_pipeline()
    elif args.mode == 'full':
        run_annotation_generate_pipeline()
        run_annotation_correlation_pipeline()

if __name__ == '__main__':
    main()
