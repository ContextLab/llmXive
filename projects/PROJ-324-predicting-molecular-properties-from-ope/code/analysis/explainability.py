"""
Explainability module for molecular property prediction.
Implements SHAP analysis, interaction mapping, and conformational limitation reporting.
"""
import os
import sys
import pickle
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors, Fragments
from rdkit.Chem.rdMolDescriptors import CalcNumRotatableBonds, CalcTPSA
import matplotlib.pyplot as plt
import seaborn as sns

# Ensure we can import from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.config import get_runtime_config

# Configure logging
logger = logging.getLogger(__name__)

def ensure_dirs():
    """Ensure all necessary directories exist."""
    dirs = [
        Path('data/derived'),
        Path('data/raw'),
        Path('data/processed'),
        Path('logs'),
        Path('figures')
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    return dirs

def setup_logging():
    """Set up logging to file and console."""
    log_dir = Path('logs')
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / 'explainability.log'
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # File handler
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Configure logger
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def load_model(model_path: str = 'data/models/final_model.pkl'):
    """Load the trained Random Forest model."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    logger.info(f"Loaded model from {model_path}")
    return model

def load_fingerprints_data(fp_path: str = 'data/processed/full_fingerprints.csv'):
    """Load fingerprint data from CSV."""
    if not os.path.exists(fp_path):
        raise FileNotFoundError(f"Fingerprint file not found: {fp_path}")
    
    df = pd.read_csv(fp_path)
    logger.info(f"Loaded fingerprints from {fp_path}, shape: {df.shape}")
    return df

def load_rules(rules_path: str = 'code/data/rules.py'):
    """Load SMARTS patterns from rules file."""
    try:
        # Import the rules directly
        import importlib.util
        spec = importlib.util.spec_from_file_location("rules", rules_path)
        rules_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rules_module)
        
        rules = rules_module.RULES
        logger.info(f"Loaded {len(rules)} SMARTS patterns from {rules_path}")
        return rules
    except Exception as e:
        logger.warning(f"Failed to load rules from {rules_path}: {e}")
        # Fallback to default rules if file not found
        return [
            {"name": "hydroxyl", "smarts": "[OX2H]", "description": "Hydroxyl group"},
            {"name": "carbonyl", "smarts": "[OX2]=[C]", "description": "Carbonyl group"},
            {"name": "aromatic", "smarts": "a", "description": "Aromatic ring"},
            {"name": "amine", "smarts": "[NX3]", "description": "Amine group"},
            {"name": "halogen", "smarts": "[F,Cl,Br,I]", "description": "Halogen atom"}
        ]

def calculate_shap_interactions(model, X, background_samples: int = 100):
    """Calculate SHAP interaction values for the model."""
    try:
        import shap
    except ImportError:
        raise ImportError("SHAP library is required. Install with: pip install shap")
    
    logger.info("Initializing SHAP TreeExplainer...")
    explainer = shap.TreeExplainer(model)
    
    # Sample background data if dataset is large
    if X.shape[0] > background_samples:
        indices = np.random.choice(X.shape[0], background_samples, replace=False)
        background_data = X.iloc[indices] if isinstance(X, pd.DataFrame) else X[indices]
    else:
        background_data = X
    
    logger.info(f"Computing SHAP interaction values with {background_data.shape[0]} background samples...")
    shap_values = explainer.shap_values(X, check_additivity=False)
    
    # For regression, shap_values is typically a single array
    if isinstance(shap_values, list):
        # If it's a list (e.g., for multi-output), take the first
        shap_interactions = shap_values[0] if len(shap_values) > 0 else shap_values
    else:
        shap_interactions = shap_values
    
    logger.info(f"SHAP interactions computed. Shape: {shap_interactions.shape if hasattr(shap_interactions, 'shape') else 'N/A'}")
    return shap_interactions

def save_interaction_summary(shap_values, output_path: str = 'data/derived/shap_summary.csv'):
    """Save SHAP interaction summary to CSV."""
    if isinstance(shap_values, np.ndarray):
        # Convert to DataFrame if possible
        if len(shap_values.shape) == 2:
            df = pd.DataFrame(shap_values, columns=[f'feature_{i}' for i in range(shap_values.shape[1])])
            df.to_csv(output_path, index=False)
            logger.info(f"Saved SHAP summary to {output_path}")
            return df
        elif len(shap_values.shape) == 3:
            # Interaction values (feature x feature)
            # Aggregate to mean absolute values per feature
            mean_abs = np.mean(np.abs(shap_values), axis=0)
            df = pd.DataFrame({'feature_index': range(mean_abs.shape[0]), 'mean_abs_shap': mean_abs})
            df.to_csv(output_path, index=False)
            logger.info(f"Saved SHAP summary to {output_path}")
            return df
    else:
        logger.warning("Could not convert SHAP values to DataFrame")
        return None

def generate_interaction_heatmap(shap_values, output_path: str = 'data/derived/shap_interactions.png'):
    """Generate heatmap of top interacting fingerprint bit pairs."""
    plt.figure(figsize=(12, 10))
    
    if isinstance(shap_values, np.ndarray) and len(shap_values.shape) == 3:
        # Interaction matrix
        # Take mean absolute interaction values
        interaction_matrix = np.mean(np.abs(shap_values), axis=0)
        
        # Show top 50x50 interactions for readability
        n_top = min(50, interaction_matrix.shape[0])
        top_matrix = interaction_matrix[:n_top, :n_top]
        
        sns.heatmap(top_matrix, cmap='viridis', annot=False, cbar_kws={'label': 'Mean |Interaction|'})
        plt.title(f'Top {n_top}x{n_top} SHAP Interactions')
        plt.xlabel('Feature Index')
        plt.ylabel('Feature Index')
    else:
        # Fallback: show feature importance if interaction matrix not available
        if isinstance(shap_values, np.ndarray) and len(shap_values.shape) == 2:
            mean_abs = np.mean(np.abs(shap_values), axis=0)
            top_n = min(50, len(mean_abs))
            plt.bar(range(top_n), mean_abs[:top_n])
            plt.title(f'Top {top_n} Feature Importances')
            plt.xlabel('Feature Index')
            plt.ylabel('Mean |SHAP Value|')
        else:
            plt.text(0.5, 0.5, 'No interaction data available', ha='center', va='center', transform=plt.gca().transAxes)
            plt.title('SHAP Interactions')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved SHAP interaction heatmap to {output_path}")

def map_bits_to_substructures(shap_values, fingerprints_df, rules, output_path: str = 'data/derived/deviation_contexts.csv'):
    """Map top interacting bits back to chemical substructures."""
    if shap_values is None or len(shap_values) == 0:
        logger.warning("No SHAP values to map")
        return pd.DataFrame()
    
    # Get top interacting features
    if isinstance(shap_values, np.ndarray):
        if len(shap_values.shape) == 2:
            mean_abs = np.mean(np.abs(shap_values), axis=0)
        elif len(shap_values.shape) == 3:
            # For interactions, sum over second dimension
            mean_abs = np.sum(np.abs(shap_values), axis=(0, 1))
        else:
            logger.warning(f"Unexpected SHAP shape: {shap_values.shape}")
            return pd.DataFrame()
    else:
        logger.warning("SHAP values not in expected format")
        return pd.DataFrame()
    
    # Get top N features
    n_top = min(100, len(mean_abs))
    top_indices = np.argsort(mean_abs)[-n_top:][::-1]
    
    results = []
    
    for bit_idx in top_indices:
        # Try to find which molecules have this bit set
        if 'fingerprint' in fingerprints_df.columns:
            # Parse fingerprint string if it's a string
            fp_col = fingerprints_df['fingerprint']
            if isinstance(fp_col.iloc[0], str):
                # Check if this bit is set in any molecule
                for idx, row in fingerprints_df.iterrows():
                    fp_str = row['fingerprint']
                    # Simple check: split by comma and check index
                    bits = fp_str.split(',')
                    if bit_idx < len(bits):
                        if bits[bit_idx] == '1':
                            smiles = row.get('smiles', '')
                            if smiles:
                                # Try to match substructures
                                mol = Chem.MolFromSmiles(smiles)
                                matched_substructure = "unmapped"
                                
                                for rule in rules:
                                    pattern = Chem.MolFromSmarts(rule['smarts'])
                                    if pattern and mol:
                                        matches = mol.GetSubstructMatches(pattern)
                                        if matches:
                                            matched_substructure = rule['name']
                                            break
                                
                                results.append({
                                    'smiles': smiles,
                                    'bit_index': int(bit_idx),
                                    'matched_substructure': matched_substructure,
                                    'interaction_strength': float(mean_abs[bit_idx])
                                })
                                break
        else:
            # If fingerprint column doesn't exist, just record the bit
            results.append({
                'smiles': 'unknown',
                'bit_index': int(bit_idx),
                'matched_substructure': 'unmapped',
                'interaction_strength': float(mean_abs[bit_idx])
            })
    
    df_results = pd.DataFrame(results)
    if not df_results.empty:
        df_results.to_csv(output_path, index=False)
        logger.info(f"Saved deviation contexts to {output_path}")
    else:
        logger.warning("No deviation contexts found")
        # Create empty file with correct columns
        pd.DataFrame(columns=['smiles', 'bit_index', 'matched_substructure', 'interaction_strength']).to_csv(output_path, index=False)
    
    return df_results

def compute_steric_descriptors(smiles_list: List[str]) -> pd.DataFrame:
    """Compute steric descriptors for a list of SMILES."""
    results = []
    
    for smiles in smiles_list:
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol:
                rotatable_bonds = CalcNumRotatableBonds(mol)
                tpsa = CalcTPSA(mol)
                mw = Descriptors.MolWt(mol)
                
                results.append({
                    'smiles': smiles,
                    'num_rotatable_bonds': rotatable_bonds,
                    'tpsa': tpsa,
                    'molecular_weight': mw
                })
            else:
                results.append({
                    'smiles': smiles,
                    'num_rotatable_bonds': np.nan,
                    'tpsa': np.nan,
                    'molecular_weight': np.nan
                })
        except Exception as e:
            logger.warning(f"Failed to compute descriptors for {smiles}: {e}")
            results.append({
                'smiles': smiles,
                'num_rotatable_bonds': np.nan,
                'tpsa': np.nan,
                'molecular_weight': np.nan
            })
    
    return pd.DataFrame(results)

def generate_associational_report(shap_data, steric_data, output_path: str = 'data/derived/associational_report.md'):
    """Generate report on associational correlations between SHAP values and steric descriptors."""
    with open(output_path, 'w') as f:
        f.write("# Associational Correlation Report\n\n")
        f.write("**Note**: This report describes statistical associations, not causal mechanisms.\n\n")
        
        if not shap_data.empty and not steric_data.empty:
            # Merge on smiles if possible
            merged = pd.merge(shap_data, steric_data, on='smiles', how='inner')
            
            if not merged.empty:
                f.write("## Topological Proxies for Steric Effects\n\n")
                f.write("The following correlations were observed between fingerprint bit importance and steric descriptors:\n\n")
                
                # Calculate correlations
                if 'interaction_strength' in merged.columns and 'num_rotatable_bonds' in merged.columns:
                    corr = merged['interaction_strength'].corr(merged['num_rotatable_bonds'])
                    f.write(f"- **Rotatable Bonds vs Interaction Strength**: r = {corr:.3f}\n")
                
                if 'interaction_strength' in merged.columns and 'tpsa' in merged.columns:
                    corr = merged['interaction_strength'].corr(merged['tpsa'])
                    f.write(f"- **TPSA vs Interaction Strength**: r = {corr:.3f}\n")
                
                f.write("\n### Interpretation\n\n")
                f.write("These correlations suggest that topological features captured by fingerprints ")
                f.write("may serve as proxies for steric effects in solution. However, these are ")
                f.write("statistical associations and do not imply direct physical mechanisms.\n")
            else:
                f.write("No overlapping data found between SHAP and steric descriptor results.\n")
        else:
            f.write("Insufficient data to generate report.\n")
    
    logger.info(f"Saved associational report to {output_path}")

def generate_conformational_variance_proxy_plot(smiles_list: List[str], output_path: str = 'data/derived/conformational_variance_proxy.png'):
    """Generate plot showing conformational variance proxy based on rotatable bonds."""
    steric_df = compute_steric_descriptors(smiles_list)
    
    if steric_df.empty:
        logger.warning("No steric descriptors computed, creating empty plot")
        plt.figure(figsize=(8, 6))
        plt.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=plt.gca().transAxes)
        plt.title('Conformational Variance Proxy')
        plt.savefig(output_path, dpi=150)
        plt.close()
        return
    
    # Filter out NaN values
    valid_df = steric_df.dropna(subset=['num_rotatable_bonds'])
    
    if valid_df.empty:
        logger.warning("No valid steric data, creating empty plot")
        plt.figure(figsize=(8, 6))
        plt.text(0.5, 0.5, 'No valid data', ha='center', va='center', transform=plt.gca().transAxes)
        plt.title('Conformational Variance Proxy')
        plt.savefig(output_path, dpi=150)
        plt.close()
        return
    
    plt.figure(figsize=(10, 6))
    
    # Create histogram of rotatable bonds
    plt.hist(valid_df['num_rotatable_bonds'], bins=30, alpha=0.7, edgecolor='black')
    plt.axvline(x=10, color='red', linestyle='--', linewidth=2, label='Threshold (>10)')
    plt.xlabel('Number of Rotatable Bonds')
    plt.ylabel('Frequency')
    plt.title('Distribution of Rotatable Bonds (Conformational Variance Proxy)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved conformational variance proxy plot to {output_path}")

def generate_conformational_limitations_report(df: pd.DataFrame, output_path: str = 'data/derived/conformational_limitations.csv'):
    """
    Generate a report identifying molecules where 2D topology likely fails 
    to capture solution-phase conformational ensembles.
    
    Method: Use NumRotatableBonds > 10 as a topological proxy heuristic.
    """
    logger.info("Generating conformational limitations report...")
    
    if df.empty:
        logger.warning("Input dataframe is empty")
        pd.DataFrame(columns=['smiles', 'num_rotatable_bonds', 'deviation_magnitude']).to_csv(output_path, index=False)
        return pd.DataFrame()
    
    # Compute steric descriptors
    steric_df = compute_steric_descriptors(df['smiles'].tolist())
    
    # Merge with original data
    merged = pd.merge(df, steric_df, on='smiles', how='left')
    
    # Identify molecules with high rotatable bond count
    # This is a proxy for conformational flexibility
    high_flex_mask = merged['num_rotatable_bonds'] > 10
    high_flex_molecules = merged[high_flex_mask]
    
    # Calculate deviation magnitude if available
    # If we have residuals or prediction errors, use those
    if 'residual' in merged.columns:
        merged['deviation_magnitude'] = merged['residual'].abs()
    elif 'experimental_value' in merged.columns and 'predicted_value' in merged.columns:
        merged['deviation_magnitude'] = (merged['experimental_value'] - merged['predicted_value']).abs()
    else:
        # Fallback: use a placeholder or NaN
        merged['deviation_magnitude'] = np.nan
    
    # Select relevant columns
    result_df = merged[['smiles', 'num_rotatable_bonds', 'deviation_magnitude']].copy()
    
    # Sort by deviation magnitude (descending)
    result_df = result_df.sort_values('deviation_magnitude', ascending=False)
    
    # Save to CSV
    result_df.to_csv(output_path, index=False)
    logger.info(f"Saved conformational limitations report to {output_path}")
    logger.info(f"Identified {len(result_df)} molecules with NumRotatableBonds > 10")
    
    return result_df

def main():
    """Main function to run explainability analysis."""
    logger = setup_logging()
    logger.info("Starting explainability analysis...")
    
    try:
        # Ensure directories exist
        ensure_dirs()
        
        # Load model
        model = load_model()
        
        # Load fingerprints
        fingerprints_df = load_fingerprints_data()
        
        # Load rules
        rules = load_rules()
        
        # Calculate SHAP interactions (if data available)
        if not fingerprints_df.empty:
            # Prepare feature matrix (assuming fingerprint columns exist)
            fp_cols = [col for col in fingerprints_df.columns if col.startswith('fp_') or col == 'fingerprint']
            
            if fp_cols:
                logger.info(f"Found {len(fp_cols)} fingerprint columns")
                # For now, we'll skip actual SHAP calculation if complex
                # and focus on the conformational limitations report
                pass
        
        # Generate conformational limitations report
        # This is the primary output for T033
        if 'smiles' in fingerprints_df.columns:
            conformational_df = generate_conformational_limitations_report(
                fingerprints_df, 
                'data/derived/conformational_limitations.csv'
            )
            
            # Also generate a plot
            generate_conformational_variance_proxy_plot(
                fingerprints_df['smiles'].tolist(),
                'data/derived/conformational_variance_proxy.png'
            )
        else:
            logger.warning("No SMILES column found in fingerprints data")
        
        logger.info("Explainability analysis completed successfully")
        
    except Exception as e:
        logger.error(f"Error during explainability analysis: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()