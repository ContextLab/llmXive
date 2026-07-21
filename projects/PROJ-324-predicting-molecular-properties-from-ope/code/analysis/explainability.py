"""
Explainability module for analyzing Random Forest model predictions on molecular properties.

This module implements SHAP-based interaction analysis, bit-to-substructure mapping,
and conformational limitation detection to interpret model behavior.
"""
import os
import sys
import pickle
import logging
import re
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import shap
from sklearn.ensemble import RandomForestRegressor

from analysis.stats import ensure_dirs
from logging_utils import setup_logger
from seed_manager import get_seed

# Configure logger
logger = setup_logger(__name__)

def load_model(model_path: str) -> RandomForestRegressor:
    """Load the trained Random Forest model from disk."""
    path = Path(model_path)
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    with open(path, "rb") as f:
        model = pickle.load(f)
    logger.info(f"Loaded model from {model_path}")
    return model

def load_fingerprints_data(data_path: str) -> Tuple[np.ndarray, pd.DataFrame]:
    """
    Load fingerprint data and corresponding molecule metadata.
    Returns:
        X: numpy array of fingerprints (features)
        df_meta: DataFrame with SMILES and target values (if available)
    """
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Fingerprint data file not found: {data_path}")
    
    # Try to load as parquet first (efficient for large data)
    if path.suffix == '.parquet':
        df = pd.read_parquet(path)
    elif path.suffix == '.csv':
        df = pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")
    
    # Identify feature columns (assuming they start with 'fp_' or are numeric and not SMILES/Target)
    feature_cols = [c for c in df.columns if c.startswith('fp_') or (df[c].dtype in [np.int64, np.float64] and c not in ['smiles', 'logP', 'solubility', 'boiling_point'])]
    
    if not feature_cols:
        # Fallback: assume all numeric columns except known metadata are features
        feature_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c not in ['smiles', 'logP', 'solubility', 'boiling_point']]
    
    if not feature_cols:
        raise ValueError("No feature columns found in fingerprint data.")
    
    X = df[feature_cols].values
    # Keep metadata for reference
    meta_cols = ['smiles', 'logP', 'solubility', 'boiling_point']
    meta_cols = [c for c in meta_cols if c in df.columns]
    df_meta = df[meta_cols] if meta_cols else pd.DataFrame()
    
    logger.info(f"Loaded {X.shape[0]} samples with {X.shape[1]} fingerprint features.")
    return X, df_meta

def calculate_shap_interactions(model: RandomForestRegressor, X: np.ndarray, 
                                nsamples: int = 100) -> np.ndarray:
    """
    Calculate SHAP interaction values for the model on the given data.
    
    Args:
        model: Trained Random Forest model
        X: Feature matrix (fingerprints)
        nsamples: Number of samples to use for SHAP background (for speed)
        
    Returns:
        shap_interaction_values: 3D array (num_samples, num_features, num_features)
    """
    logger.info(f"Calculating SHAP interaction values on {X.shape[0]} samples...")
    
    # Use a subset for background if dataset is very large to save memory/time
    if X.shape[0] > 2000:
        indices = np.random.choice(X.shape[0], 2000, replace=False)
        background = X[indices]
        logger.info(f"Using 2000 samples for SHAP background.")
    else:
        background = X
    
    # Initialize SHAP explainer
    # For tree-based models, TreeExplainer is efficient
    try:
        explainer = shap.TreeExplainer(model, data=background)
    except Exception as e:
        logger.warning(f"TreeExplainer failed: {e}. Falling back to KernelExplainer (slower).")
        explainer = shap.KernelExplainer(model.predict, data=background)
    
    # Calculate interaction values
    # Note: shap_interaction_values shape is (nsamples, n_features, n_features)
    # This can be memory intensive for high-dimensional fingerprints (e.g., 1024 bits)
    # We will calculate it for a subset of features if necessary, but try full first with sampling
    
    logger.info("Computing SHAP interactions (this may take a while)...")
    shap_interaction_values = explainer.shap_interaction_values(X)
    
    logger.info(f"SHAP interactions computed. Shape: {shap_interaction_values.shape}")
    return shap_interaction_values

def save_interaction_summary(interaction_values: np.ndarray, output_path: str):
    """Save the interaction matrix summary (mean absolute interaction strength) to a CSV."""
    # Calculate mean absolute interaction strength for each pair
    # Shape: (n_samples, n_features, n_features) -> (n_features, n_features)
    mean_abs_interaction = np.mean(np.abs(interaction_values), axis=0)
    
    df_summary = pd.DataFrame(mean_abs_interaction)
    df_summary.to_csv(output_path, index=False)
    logger.info(f"Saved interaction summary to {output_path}")

def generate_interaction_heatmap(interaction_values: np.ndarray, output_path: str, 
                                 top_n: int = 20):
    """
    Generate a heatmap of the top interacting fingerprint bit pairs.
    
    Args:
        interaction_values: 3D array of SHAP interaction values
        output_path: Path to save the heatmap image
        top_n: Number of top interactions to highlight
    """
    logger.info(f"Generating interaction heatmap, saving to {output_path}")
    
    # Calculate mean absolute interaction strength
    mean_abs_interaction = np.mean(np.abs(interaction_values), axis=0)
    
    # Set up the plot
    plt.figure(figsize=(12, 10))
    
    # We only plot the top N interactions to avoid clutter, or the full matrix if small
    n_features = mean_abs_interaction.shape[0]
    
    if n_features <= 50:
        # Plot full matrix if small
        im = plt.imshow(mean_abs_interaction, cmap='viridis', aspect='auto')
        plt.colorbar(im, label='Mean |SHAP Interaction|')
        plt.title(f'SHAP Interaction Strength (Full Matrix, {n_features} features)')
        plt.xlabel('Feature Index')
        plt.ylabel('Feature Index')
    else:
        # Find top N interacting pairs
        # Flatten and sort
        flat_indices = np.unravel_index(np.argsort(mean_abs_interaction, axis=None)[::-1], mean_abs_interaction.shape)
        top_pairs = list(zip(flat_indices[0][:top_n], flat_indices[1][:top_n]))
        
        # Create a mask for the top interactions
        mask = np.zeros_like(mean_abs_interaction, dtype=bool)
        for i, j in top_pairs:
            mask[i, j] = True
            mask[j, i] = True # Symmetric
        
        # Plot with mask
        im = plt.imshow(mean_abs_interaction, cmap='viridis', aspect='auto')
        plt.colorbar(im, label='Mean |SHAP Interaction|')
        plt.title(f'Top {top_n} Interacting Bit Pairs (out of {n_features} features)')
        plt.xlabel('Feature Index')
        plt.ylabel('Feature Index')
        
        # Annotate top pairs
        for i, j in top_pairs:
            val = mean_abs_interaction[i, j]
            plt.text(j, i, f'{val:.3f}', ha='center', va='center', color='white', fontsize=8)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Heatmap saved to {output_path}")

def map_bits_to_substructures(interaction_values: np.ndarray, output_path: str):
    """
    Map top interacting bits to chemical substructures using RDKit.
    (Implementation deferred to T029, placeholder for structure)
    """
    logger.info("Mapping bits to substructures (placeholder for T029).")
    # This would involve:
    # 1. Identifying top bits
    # 2. Using RDKit to find which substructures correspond to those bits
    # 3. Saving to CSV
    pass

def generate_associational_report(output_dir: str):
    """
    Generate a report framing findings as associational correlations.
    """
    report_path = Path(output_dir) / "shap_findings_report.txt"
    with open(report_path, "w") as f:
        f.write("SHAP Interaction Analysis Report\n")
        f.write("=" * 40 + "\n\n")
        f.write("NOTE: The following findings represent associational correlations\n")
        f.write("between fingerprint bits and target properties. They do not imply\n")
        f.write("causal mechanisms or direct physical interactions.\n\n")
        f.write("Top interacting bit pairs have been identified and visualized.\n")
        f.write("Mapping to substructures (T029) will further contextualize these\n")
        f.write("topological proxies.\n")
    logger.info(f"Generated associational report at {report_path}")

def main():
    """
    Main entry point for T027: Generate SHAP interaction heatmaps.
    """
    logger.info("Starting T027: Generate SHAP interaction heatmaps.")
    
    # Paths
    project_root = Path(__file__).resolve().parents[2]
    model_path = project_root / "data" / "derived" / "final_model.pkl"
    fp_path = project_root / "data" / "derived" / "fingerprints.parquet"
    output_dir = project_root / "data" / "derived"
    heatmap_path = output_dir / "shap_interactions.png"
    
    ensure_dirs(output_dir)
    
    try:
        # 1. Load Model
        model = load_model(str(model_path))
        
        # 2. Load Fingerprints
        X, df_meta = load_fingerprints_data(str(fp_path))
        
        # 3. Calculate SHAP Interactions
        # Note: This can be memory intensive. We use a subset of data if needed.
        # For the heatmap, we might want to use a representative subset if X is huge.
        # However, the task requires "top interacting pairs", so we need a robust estimate.
        # Let's use a subset of 1000 samples for calculation if X is very large to save time/memory.
        if X.shape[0] > 1000:
            indices = np.random.choice(X.shape[0], 1000, replace=False)
            X_subset = X[indices]
            logger.info(f"Using {len(indices)} samples for SHAP calculation.")
        else:
            X_subset = X
        
        interaction_values = calculate_shap_interactions(model, X_subset)
        
        # 4. Save Summary
        summary_path = output_dir / "shap_interaction_summary.csv"
        save_interaction_summary(interaction_values, str(summary_path))
        
        # 5. Generate Heatmap
        generate_interaction_heatmap(interaction_values, str(heatmap_path), top_n=20)
        
        # 6. Generate Report
        generate_associational_report(str(output_dir))
        
        logger.info("T027 completed successfully.")
        
    except Exception as e:
        logger.error(f"T027 failed: {e}", exc_info=True)
        raise

    if not fingerprints_path.exists():
        logger.error(f"Fingerprints file not found: {fingerprints_path}")
        sys.exit(1)

    # Load model and data
    logger.info("Loading model and fingerprints...")
    model = load_model(str(model_path))
    fingerprints, targets = load_fingerprints_data(str(fingerprints_path))
    fingerprints_np = fingerprints.values

    # Calculate SHAP interactions
    logger.info("Calculating SHAP interactions...")
    shap_interactions, shap_main = calculate_shap_interactions(model, fingerprints_np)

    # Get top interacting bits
    top_bits = get_top_interacting_bits(shap_interactions, n_top=20)
    logger.info(f"Top {len(top_bits)} interacting bit pairs identified")

    # Stability analysis
    logger.info("Performing bootstrap stability analysis...")
    stability_df = bootstrap_stability_analysis(shap_interactions, top_bits, n_bootstrap=100, seed=42)
    save_stability_analysis(stability_df, str(output_dir / 'stability_analysis.csv'))

    # Map bits to substructures
    smiles_list = fingerprints.index.tolist() if hasattr(fingerprints, 'index') else []
    if not smiles_list:
        # Try to load SMILES from a separate file or assume first column
        logger.warning("No SMILES found in fingerprints index, skipping substructure mapping")
    else:
        bit_mapping = map_bits_to_substructures(smiles_list, [i for i, j in top_bits])
        save_substructure_mapping(bit_mapping, str(output_dir / 'shap_substructure_mapping.csv'))

    # Cross-reference with functional groups
    if bit_mapping:
        functional_groups_df = cross_reference_with_functional_groups(smiles_list, bit_mapping)
        # Save without global descriptors to final output
        final_output = functional_groups_df[['bit_index', 'smiles', 'num_carbonyl', 'num_hydroxyl', 'num_amine', 'num_ether', 'num_ester']]
        final_output.to_csv(output_dir / 'shap_substructure_mapping.csv', index=False)

    # Generate associational report
    generate_associational_report(final_output, str(output_dir / 'associational_report.txt'))

    # Conformational limitation analysis
    limitations_df = detect_conformational_limitations(smiles_list)
    generate_conformational_limitation_report(limitations_df, str(output_dir / 'conformational_limitation_report.txt'))

    logger.info("Explainability analysis complete")

if __name__ == "__main__":
    main()
