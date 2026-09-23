import os
import sys
import pickle
import logging
import re
from pathlib import Path
from typing import Any, List, Dict, Optional, Tuple
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for CI/runner environments
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
from rdkit import DataStructs
from rdkit.Chem.Fingerprints import FingerprintMols

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/explainability.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Ensure output directories exist
def ensure_dirs():
    """Create necessary directories for output artifacts."""
    dirs = [
        'data/derived',
        'data/derived/figures',
        'logs'
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def load_model(model_path: str = 'data/derived/final_model.pkl') -> Any:
    """Load the trained Random Forest model."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def load_fingerprints_data(fp_path: str = 'data/derived/fp_train.pkl') -> Tuple[np.ndarray, List[str]]:
    """Load fingerprint data and feature names."""
    if not os.path.exists(fp_path):
        # Fallback to parquet if pkl not found, though spec says pkl
        try:
            df = pd.read_parquet('data/processed/train_fingerprints.parquet')
            # Extract bits if stored as string or list
            # This is a simplified loader; real implementation depends on T019 output format
            logger.warning("Using parquet fallback for fingerprints")
            return np.array([]), []
        except Exception as e:
            raise FileNotFoundError(f"Fingerprint data not found: {e}")
    
    with open(fp_path, 'rb') as f:
        data = pickle.load(f)
    if isinstance(data, tuple):
        return data[0], data[1]
    return data, []

def load_rules(rules_path: str = 'code/data/rules.py') -> List[Dict[str, str]]:
    """Load SMARTS patterns from rules file."""
    # Import the rules if available, otherwise define defaults
    try:
        from data.rules import SMARTS_PATTERNS
        return SMARTS_PATTERNS
    except ImportError:
        logger.warning("Rules file not found, using defaults")
        return [
            {"name": "hydroxyl", "smarts": "[OX2H]", "description": "Hydroxyl group"},
            {"name": "carbonyl", "smarts": "[OX2]=C", "description": "Carbonyl group"},
            {"name": "aromatic", "smarts": "a", "description": "Aromatic ring"},
            {"name": "amine", "smarts": "[NX3]", "description": "Amine group"}
        ]

def calculate_shap_interactions(model: Any, X: np.ndarray, feature_names: List[str] = None) -> Any:
    """
    Calculate SHAP interaction values.
    Note: Using shap.TreeExplainer for tree-based models.
    """
    try:
        import shap
        # Check if InteractionValues exists in this shap version
        # In newer versions, it's shap.Explainer().shap_interaction_values
        explainer = shap.TreeExplainer(model)
        # For large datasets, use a sample
        if X.shape[0] > 500:
            logger.info(f"Sampling 500 rows for SHAP interaction calculation")
            indices = np.random.choice(X.shape[0], 500, replace=False)
            X_sample = X[indices]
        else:
            X_sample = X
        
        # Calculate interactions
        # shap_interaction_values returns a 3D array: (samples, features, features)
        interactions = explainer.shap_interaction_values(X_sample)
        
        # If the API returns a different object, adapt
        if hasattr(interactions, 'values'):
            return interactions
        return interactions
    except Exception as e:
        logger.error(f"Error calculating SHAP interactions: {e}")
        raise

def save_interaction_summary(interactions: Any, output_path: str = 'data/derived/shap_interaction_summary.json'):
    """Save interaction summary to JSON."""
    # Simplified summary extraction
    if hasattr(interactions, 'values'):
        vals = interactions.values
    else:
        vals = interactions
    
    # Get top interacting pairs
    # Sum over samples and flatten
    if len(vals.shape) == 3:
        summary = np.abs(vals).mean(axis=0)
        # Get top 10 pairs
        top_indices = np.unravel_index(np.argsort(summary.ravel())[-10:], summary.shape)
        top_pairs = list(zip(top_indices[0], top_indices[1]))
    else:
        top_pairs = []
    
    with open(output_path, 'w') as f:
        import json
        json.dump({"top_pairs": top_pairs}, f, indent=2)

def generate_interaction_heatmap(interactions: Any, output_path: str = 'data/derived/shap_interactions.png'):
    """Generate heatmap of top interacting fingerprint bit pairs."""
    try:
        if hasattr(interactions, 'values'):
            vals = interactions.values
        else:
            vals = interactions
        
        if len(vals.shape) == 3:
            # Average over samples
            mean_interactions = np.abs(vals).mean(axis=0)
            
            plt.figure(figsize=(10, 8))
            plt.imshow(mean_interactions, cmap='viridis')
            plt.colorbar(label='Mean |Interaction Value|')
            plt.title('Top Interacting Fingerprint Bit Pairs')
            plt.xlabel('Feature Index')
            plt.ylabel('Feature Index')
            plt.tight_layout()
            plt.savefig(output_path, dpi=150)
            plt.close()
            logger.info(f"Saved SHAP heatmap to {output_path}")
        else:
            logger.warning("Interaction data shape not suitable for heatmap")
    except Exception as e:
        logger.error(f"Error generating heatmap: {e}")
        raise

def map_bits_to_substructures(smiles_list: List[str], bit_indices: List[int], rules: List[Dict], output_path: str = 'data/derived/deviation_contexts.csv'):
    """Map fingerprint bits to chemical substructures using RDKit."""
    results = []
    for smiles in smiles_list:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            continue
        
        # Get bit info for this molecule
        # This is a simplified mapping; real implementation would use RDKit's bit info
        fp = DataStructs.cDataStructs.ExplicitBitVect(2048)
        # Generate fingerprint
        from rdkit.Chem import AllChem
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)
        
        bit_info = {}
        AllChem.GetMorganFingerprintAsBitVect(mol, 2, bitInfo=bit_info)
        
        for bit_idx in bit_indices:
            if bit_idx in bit_info:
                atom_indices = [idx for idx, _ in bit_info[bit_idx]]
                # Check against rules
                for rule in rules:
                    pattern = Chem.MolFromSmarts(rule['smarts'])
                    if pattern:
                        matches = mol.GetSubstructMatches(pattern)
                        for match in matches:
                            if any(idx in match for idx in atom_indices):
                                results.append({
                                    'smiles': smiles,
                                    'bit_index': bit_idx,
                                    'matched_substructure': rule['name'],
                                    'interaction_strength': 1.0 # Placeholder
                                })
    
    df = pd.DataFrame(results)
    if not df.empty:
        df.to_csv(output_path, index=False)
        logger.info(f"Saved deviation contexts to {output_path}")
    else:
        logger.warning("No substructure matches found")

def compute_steric_descriptors(smiles_list: List[str], output_path: str = 'data/derived/steric_descriptors.csv'):
    """Compute steric descriptors for molecules."""
    results = []
    for smiles in smiles_list:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            continue
        
        results.append({
            'smiles': smiles,
            'molecular_weight': Descriptors.MolWt(mol),
            'tpsa': Descriptors.TPSA(mol),
            'num_rotatable_bonds': rdMolDescriptors.CalcNumRotatableBonds(mol),
            'num_rings': rdMolDescriptors.CalcNumRings(mol)
        })
    
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved steric descriptors to {output_path}")
    return df

def generate_associational_report(interaction_data: Dict, output_path: str = 'data/derived/associational_report.md'):
    """Generate report framing findings as associational correlations."""
    with open(output_path, 'w') as f:
        f.write("# Associational Correlation Report\n\n")
        f.write("## Disclaimer\n")
        f.write("This report presents **associational correlations** derived from 2D topological fingerprints. ")
        f.write("The identified 'substructures' are statistical proxies, not direct physical measurements of solution-phase conformational ensembles.\n\n")
        f.write("## Findings\n")
        f.write(f"Top interacting bits: {interaction_data.get('top_pairs', [])}\n")
        f.write("\n*Note: These correlations do not imply causal mechanisms.*\n")
    logger.info(f"Saved associational report to {output_path}")

def generate_conformational_variance_proxy_plot(
    rf_predictions_path: str = 'data/derived/rf_test_predictions.csv',
    baseline_predictions_path: str = 'data/derived/baseline_test_predictions.csv',
    output_path: str = 'data/derived/conformational_variance_proxy.png'
):
    """
    Generate a plot visualizing the distribution of NumRotatableBonds for molecules
    where the RF model deviates significantly (>2σ) from the Crippen baseline.
    
    This addresses the concern that 2D fingerprints cannot resolve solution-phase
    conformational ensembles, labeling high-deviation, high-flexibility molecules
    as 'Potential Conformational Artifacts'.
    """
    ensure_dirs()
    
    # Load predictions
    try:
        rf_df = pd.read_csv(rf_predictions_path)
        baseline_df = pd.read_csv(baseline_predictions_path)
    except FileNotFoundError as e:
        logger.error(f"Required prediction files not found: {e}")
        raise
    
    # Merge on smiles
    merged = pd.merge(
        rf_df, 
        baseline_df, 
        on='smiles', 
        suffixes=('_rf', '_crippen'),
        how='inner'
    )
    
    if merged.empty:
        raise ValueError("No overlapping molecules found between RF and Baseline predictions.")
    
    # Calculate residuals and deviation
    # Assume columns are 'experimental_value_x' (from RF merge) and 'predicted_value_y' (from Baseline merge)
    # Adjust column names based on actual schema from T014.5 and T020.1
    # T014.5 output: smiles, property_name, experimental_value, predicted_value, residual
    # T020.1 output: smiles, property_name, experimental_value, predicted_value, residual
    
    # We need to calculate: RF residual - Crippen residual
    # Or: (RF_pred - Exp) - (Crippen_pred - Exp) = RF_pred - Crippen_pred
    # Let's compute the absolute difference between RF and Crippen predictions as the deviation metric
    # Since both predict the same property for the same molecule
    
    # Determine property column
    if 'property_name' in merged.columns:
        # Filter for a specific property if needed, or process all
        # For simplicity, assume we process the first property found or all
        pass
    
    # Calculate deviation magnitude: |RF_pred - Crippen_pred|
    # Using 'predicted_value' from both sources
    # Note: Column names might be 'predicted_value_x' (RF) and 'predicted_value_y' (Crippen)
    if 'predicted_value_x' in merged.columns and 'predicted_value_y' in merged.columns:
        merged['deviation_magnitude'] = np.abs(merged['predicted_value_x'] - merged['predicted_value_y'])
    else:
        # Fallback if columns are named differently
        logger.warning("Predicted value columns not found as expected. Attempting fallback.")
        # Try to find any predicted columns
        pred_cols = [c for c in merged.columns if 'predicted' in c.lower()]
        if len(pred_cols) >= 2:
            merged['deviation_magnitude'] = np.abs(merged[pred_cols[0]] - merged[pred_cols[1]])
        else:
            raise ValueError("Could not identify predicted value columns to calculate deviation.")
    
    # Calculate statistics for deviation
    mean_dev = merged['deviation_magnitude'].mean()
    std_dev = merged['deviation_magnitude'].std()
    threshold = mean_dev + 2 * std_dev
    
    # Identify significant deviations
    merged['significant_deviation'] = merged['deviation_magnitude'] > threshold
    
    # Calculate NumRotatableBonds for each molecule
    # We need to parse SMILES to get this descriptor
    def get_rotatable_bonds(smiles):
        mol = Chem.MolFromSmiles(smiles)
        if mol:
            return rdMolDescriptors.CalcNumRotatableBonds(mol)
        return 0
    
    # Vectorize for performance
    merged['num_rotatable_bonds'] = merged['smiles'].apply(get_rotatable_bonds)
    
    # Separate data for plotting
    significant = merged[merged['significant_deviation']]
    non_significant = merged[~merged['significant_deviation']]
    
    # Create the plot
    plt.figure(figsize=(12, 8))
    
    # Plot distribution of NumRotatableBonds
    plt.hist(
        significant['num_rotatable_bonds'],
        bins=20,
        alpha=0.6,
        label='Significant Deviation (>2σ)',
        color='red',
        edgecolor='black'
    )
    plt.hist(
        non_significant['num_rotatable_bonds'],
        bins=20,
        alpha=0.6,
        label='Normal Deviation',
        color='blue',
        edgecolor='black'
    )
    
    plt.xlabel('Number of Rotatable Bonds')
    plt.ylabel('Frequency')
    plt.title('Conformational Variance Proxy: Rotatable Bonds vs. Model Deviation')
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    
    # Add annotation for the disclaimer
    plt.text(
        0.02, 0.98,
        "Disclaimer: 2D fingerprints cannot resolve solution-phase ensembles.\n"
        "High deviation in flexible molecules may indicate conformational artifacts.",
        transform=plt.gca().transAxes,
        fontsize=9,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    )
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    logger.info(f"Saved conformational variance proxy plot to {output_path}")
    
    # Log summary statistics
    logger.info(f"Mean deviation: {mean_dev:.4f}, Std deviation: {std_dev:.4f}, Threshold: {threshold:.4f}")
    logger.info(f"Number of molecules with significant deviation: {len(significant)}")
    if len(significant) > 0:
        logger.info(f"Mean rotatable bonds (significant): {significant['num_rotatable_bonds'].mean():.2f}")
        logger.info(f"Mean rotatable bonds (non-significant): {non_significant['num_rotatable_bonds'].mean():.2f}")

def main():
    """Main entry point for generating conformational variance proxy plot."""
    logger.info("Starting Conformational Variance Proxy Plot generation (T047)...")
    try:
        generate_conformational_variance_proxy_plot(
            rf_predictions_path='data/derived/rf_test_predictions.csv',
            baseline_predictions_path='data/derived/baseline_test_predictions.csv',
            output_path='data/derived/conformational_variance_proxy.png'
        )
        logger.info("T047 completed successfully.")
    except Exception as e:
        logger.error(f"T047 failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()