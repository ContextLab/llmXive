import os
import sys
import json
import logging
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np
from scipy import stats

# Add project root to path if running as script
if 'code' not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import get_config, ensure_directories
from utils.logging_utils import setup_logging, get_logger, log_metric

def load_kinetic_dataset(filepath: str) -> pd.DataFrame:
    """Load the kinetic dataset from the curated assets."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Kinetic dataset not found at {filepath}. "
                                "Ensure T009f has completed successfully.")
    df = pd.read_csv(filepath)
    required_cols = ['molecule_id', 'smiles', 'reaction_type', 'experimental_rate']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Kinetic dataset missing required columns: {missing_cols}")
    return df

def load_model_predictions(filepath: str) -> pd.DataFrame:
    """Load model comparison results and extract predictions."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Model comparison results not found at {filepath}. "
                                "Ensure T024 has completed successfully.")
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # The structure is expected to be: {model: {predictions: [...], ...}}
    # We need to find the model predictions that correspond to the kinetic dataset.
    # Assuming the 'Spectral GNN' or the best model from T024 was used for this validation.
    # We look for a key that contains predictions aligned with the kinetic dataset size.
    
    predictions = None
    best_model_name = None
    
    # Heuristic: Find the model with the lowest MSE or simply the first one with predictions
    best_mse = float('inf')
    
    for model_name, results in data.items():
        if isinstance(results, dict) and 'predictions' in results:
            preds = results['predictions']
            mse = results.get('mse', float('inf'))
            
            if len(preds) > 0:
                # We expect the predictions to align with the kinetic dataset size eventually
                # For now, we just store candidates
                if mse < best_mse:
                    best_mse = mse
                    predictions = preds
                    best_model_name = model_name
    
    if predictions is None:
        raise ValueError("No valid predictions found in model_comparison_results.json")
    
    # Return as DataFrame for easier merging later
    # We assume the order matches the kinetic dataset if T024 used the same data source
    return pd.DataFrame({
        'model_name': [best_model_name] * len(predictions),
        'predicted_gap': predictions
    })

def calculate_correlations(
    kinetic_df: pd.DataFrame, 
    predictions_df: pd.DataFrame
) -> Tuple[float, Dict[str, float]]:
    """
    Calculate Pearson correlation for the full dataset and by reaction type.
    """
    # Merge on index assuming they are aligned from the same source processing
    # If T024 used the kinetic dataset for evaluation, the order should match.
    # If not, we might need a join key, but T024 description implies it evaluated
    # on the data produced by the pipeline.
    
    # Create a combined dataframe
    combined = kinetic_df.copy()
    combined['predicted_gap'] = predictions_df['predicted_gap'].values
    
    # Filter out any NaNs that might exist in experimental_rate or predicted_gap
    combined = combined.dropna(subset=['experimental_rate', 'predicted_gap'])
    
    if len(combined) == 0:
        raise ValueError("No valid data points after merging and dropping NaNs.")
    
    # 1. Full dataset correlation
    full_corr, full_pval = stats.pearsonr(
        combined['predicted_gap'], 
        combined['experimental_rate']
    )
    
    # 2. Correlation by reaction type
    reaction_correlations = {}
    reaction_types = combined['reaction_type'].unique()
    
    for rt in reaction_types:
        subset = combined[combined['reaction_type'] == rt]
        if len(subset) > 2: # Need at least 3 points for meaningful correlation
            corr, pval = stats.pearsonr(
                subset['predicted_gap'], 
                subset['experimental_rate']
            )
            reaction_correlations[str(rt)] = {
                'pearson_r': float(corr),
                'p_value': float(pval),
                'n_samples': int(len(subset))
            }
        else:
            reaction_correlations[str(rt)] = {
                'pearson_r': None,
                'p_value': None,
                'n_samples': int(len(subset)),
                'note': 'Insufficient samples for correlation'
            }
    
    return float(full_corr), reaction_correlations

def analyze_mechanistic_consistency(
    kinetic_df: pd.DataFrame, 
    correlations: Dict[str, float],
    full_corr: float
) -> List[str]:
    """
    Analyze reaction types where the proxy is theoretically strongest.
    Generates descriptive notes based on correlation strength.
    """
    notes = []
    
    # Sort reaction types by correlation strength
    sorted_types = sorted(
        correlations.items(), 
        key=lambda x: x[1]['pearson_r'] if x[1]['pearson_r'] is not None else -999, 
        reverse=True
    )
    
    notes.append(f"Full dataset Pearson R: {full_corr:.4f}")
    notes.append("Reaction type analysis:")
    
    for rt, stats_dict in sorted_types:
        r_val = stats_dict['pearson_r']
        n = stats_dict['n_samples']
        if r_val is not None:
            strength = "strong" if abs(r_val) > 0.7 else ("moderate" if abs(r_val) > 0.4 else "weak")
            direction = "positive" if r_val > 0 else "negative"
            notes.append(
                f"  - {rt}: {strength} {direction} correlation (r={r_val:.3f}, n={n}). "
                f"This suggests the HOMO-LUMO gap proxy is {strength} for {rt} reactions."
            )
        else:
            notes.append(f"  - {rt}: Insufficient data (n={n}) for correlation analysis.")
    
    # Specific mechanistic note based on chemical intuition expected in this domain
    # Assuming higher gap = lower reactivity, we expect negative correlation with rate.
    # However, "gap" might be defined as reactivity proxy directly.
    # We provide a generic note about consistency.
    if full_corr > 0:
        notes.append(
            "Mechanistic Note: The positive correlation suggests that the predicted gap "
            "may be acting as a direct reactivity proxy (higher gap = higher rate) or "
            "the 'gap' represents an activation barrier proxy where higher is more reactive "
            "in this specific dataset context."
        )
    elif full_corr < 0:
        notes.append(
            "Mechanistic Note: The negative correlation suggests that the predicted gap "
            "behaves as an activation barrier (higher gap = lower rate), consistent with "
            "standard frontier molecular orbital theory where a larger HOMO-LUMO gap implies "
            "kinetic stability."
        )
    
    return notes

def main():
    """
    Main entry point for T033: Proxy Validation.
    Loads kinetic data and model predictions, validates correlation, and writes report.
    """
    logger = setup_logging("proxy_validation", log_file="artifacts/logs/proxy_validation.log")
    logger.info("Starting Proxy Validation (T033)")
    
    config = get_config()
    ensure_directories()
    
    # Paths
    kinetic_path = "data/assets/kinetic_dataset.csv"
    model_path = "artifacts/model_comparison_results.json"
    output_path = "artifacts/proxy_validation_report.json"
    
    try:
        # 1. Load Data
        logger.info(f"Loading kinetic dataset from {kinetic_path}")
        kinetic_df = load_kinetic_dataset(kinetic_path)
        logger.info(f"Loaded {len(kinetic_df)} molecules from kinetic dataset")
        
        logger.info(f"Loading model predictions from {model_path}")
        predictions_df = load_model_predictions(model_path)
        logger.info(f"Loaded {len(predictions_df)} predictions")
        
        # Validation: Ensure lengths match
        if len(kinetic_df) != len(predictions_df):
            # Attempt to align if possible, otherwise fail
            # T024 should have produced predictions for the exact set used in T009f
            logger.warning(
                f"Length mismatch: Kinetic ({len(kinetic_df)}) vs Predictions ({len(predictions_df)}). "
                "Attempting to proceed assuming alignment, but this may indicate a pipeline error."
            )
            # We proceed but warn. In a strict pipeline, this might be an error.
        
        # 2. Calculate Correlations
        logger.info("Calculating correlations")
        full_corr, by_reaction_type = calculate_correlations(kinetic_df, predictions_df)
        logger.info(f"Full dataset correlation: {full_corr:.4f}")
        
        # 3. Analyze Mechanistic Consistency
        logger.info("Analyzing mechanistic consistency")
        mechanistic_notes = analyze_mechanistic_consistency(kinetic_df, by_reaction_type, full_corr)
        
        # 4. Construct Report
        report = {
            "correlation_full_dataset": float(full_corr),
            "correlation_by_reaction_type_descriptive": by_reaction_type,
            "mechanistic_consistency_notes": mechanistic_notes,
            "metadata": {
                "total_samples": len(kinetic_df),
                "valid_samples": sum(1 for rt in by_reaction_type.values() if rt.get('n_samples', 0) > 0),
                "timestamp": pd.Timestamp.now().isoformat()
            }
        }
        
        # 5. Write Output
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report written to {output_path}")
        
        # Log to metrics
        log_metric("proxy_validation_full_correlation", full_corr)
        
        logger.info("T033 Proxy Validation completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"Missing required data file: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        raise

if __name__ == "__main__":
    main()
