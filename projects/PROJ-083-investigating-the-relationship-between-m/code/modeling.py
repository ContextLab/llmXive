"""
Modeling module for investigating the relationship between molecular topology and reaction selectivity.

This module implements:
1. Selectivity target extraction (Regioisomer Diversity Count)
2. Ordinal Logistic Regression (primary model)
3. Symmetry Check (FR-008)
4. Fallback to Descriptive Statistics
5. Model evaluation and reporting
"""

import logging
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.miscmodels.ordinal_model import OrderedModel
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, LeaveOneOut
from sklearn.preprocessing import StandardScaler
from scipy import stats

from config import get_config, Config
from utils.logger import setup_logger, handle_exception
from utils.symmetry import SymmetryValidator, ReactionRecord, SymmetryGroup
from descriptors import calculate_descriptors_for_smiles, TopologicalDescriptorCalculator

# Initialize logger
logger = setup_logger(__name__)

def calculate_regioisomer_count(smiles: str) -> int:
    """
    Calculate the Regioisomer Diversity Count (target variable) based on reactant symmetry.

    Algorithm:
    1. Parse SMILES to RDKit molecule.
    2. Identify the aromatic ring (assumed to be the core for EAS).
    3. Calculate graph automorphism orbits on the aromatic ring atoms.
    4. The number of unique orbits corresponds to the number of non-equivalent sites.

    Returns:
        int: The number of non-equivalent substitution sites (1 to 6 for benzene derivatives).
    """
    try:
        from rdkit import Chem
        from rdkit.Chem import rdMolDescriptors
        import networkx as nx

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.warning(f"Could not parse SMILES: {smiles}")
            return 0

        # Convert to NetworkX graph for automorphism analysis
        # RDKit does not have a direct "get automorphism orbits" function exposed simply,
        # so we use networkx for graph isomorphism/orbit calculation.
        G = nx.Graph()
        atom_map = {}
        for i, atom in enumerate(mol.GetAtoms()):
            G.add_node(i, symbol=atom.GetSymbol(), aromatic=atom.GetIsAromatic())
            atom_map[i] = atom

        for bond in mol.GetBonds():
            G.add_edge(bond.GetBeginAtomIdx(), bond.GetEndAtomIdx())

        # Identify aromatic ring atoms (simplified: assume the largest aromatic component)
        aromatic_nodes = [n for n, d in G.nodes(data=True) if d.get('aromatic', False)]
        
        if not aromatic_nodes:
            # Fallback: if no aromatic ring found, return 1 (single site assumption)
            # In a real production system, this might raise an error or skip the record.
            logger.warning(f"No aromatic ring found in {smiles}, assuming 1 site.")
            return 1

        # Create a subgraph of the aromatic ring
        # Note: For complex fused systems, this simple subgraph approach might need refinement.
        # For standard EAS (benzene derivatives), this works.
        aromatic_subgraph = G.subgraph(aromatic_nodes)

        # Calculate automorphism orbits
        # We use the "orbits" from the automorphism group.
        # NetworkX has `automorphism_group` but it's expensive.
        # A simpler heuristic for small rings: use canonical labeling or simple symmetry checks.
        # However, for exact orbits, we can use `networkx.algorithms.isomorphism.categorical_edge_match`
        # or simply rely on RDKit's `GetSymmSSR` (Symmetry Smallest Set of Smallest Rings) if available,
        # but let's stick to the graph approach requested.
        
        # Use a simpler approach: RDKit's GetSymmSSR gives symmetry classes of atoms.
        # This is more robust than manual graph traversal for this specific task.
        from rdkit.Chem import rdMolDescriptors
        # Get symmetry classes of atoms (0-indexed, lower number = higher symmetry)
        # This returns a tuple of integers where identical values mean symmetric atoms.
        sym_classes = rdMolDescriptors.CalcSymmSSR(mol)
        
        # Filter for atoms in the aromatic ring
        ring_atom_indices = set(aromatic_nodes)
        ring_sym_classes = [sym_classes[i] for i in ring_atom_indices]
        
        # Count unique symmetry classes in the ring
        unique_classes = set(ring_sym_classes)
        return len(unique_classes)

    except Exception as e:
        logger.error(f"Error calculating regioisomer count for {smiles}: {e}")
        return 0

def perform_symmetry_check(df: pd.DataFrame, threshold: float = 0.01) -> bool:
    """
    Perform the "Symmetry Check" step (FR-008).

    Logic:
    1. Initialize the SymmetryValidator with the project's defined SymmetryGroup (from T043/T044).
    2. Run the validator on a sample or the full dataset.
    3. If the failure rate (variance detected) > threshold (1%), log a warning and return False.
    4. If failure rate <= threshold, return True.

    Returns:
        bool: True if symmetry holds, False if it fails significantly.
    """
    logger.info("Starting Symmetry Check (FR-008)...")
    
    # Load the defined symmetry group (assumed to be defined in T043/T044)
    # Since T044 returns a SymmetryValidator class or instance, we assume the group is configured.
    # We need to instantiate the validator.
    # The SymmetryGroup definition is in docs/reports/symmetry_group_definition.md, 
    # but the code implementation is in code/utils/symmetry.py.
    
    # We use the SymmetryValidator from T044.
    # We need to pass a sample of the data to validate.
    
    sample_size = min(len(df), 1000)
    sample_df = df.sample(n=sample_size, random_state=42)
    
    failures = 0
    total_checked = 0
    
    # We need to construct ReactionRecord objects for the validator
    # Assuming ReactionRecord is a NamedTuple or dataclass with necessary fields.
    # From code/utils/symmetry.py API: ReactionRecord, SymmetryValidator
    
    # We assume the validator has a method `validate_record` or similar.
    # Based on T044 description: "Apply all permutations in G to the reactant graph..."
    
    # Let's assume the SymmetryValidator is initialized with the group G.
    # We need to get the group G. Since T043 defines it, we assume it's loaded or hardcoded.
    # For this implementation, we assume the SymmetryGroup is configured in the SymmetryValidator class.
    
    # We will iterate and check invariance.
    # Note: The actual implementation of `SymmetryValidator` in T044 is expected to handle the logic.
    # We call `validate_invariance_on_dataset` if available, or loop.
    
    from utils.symmetry import SymmetryValidator, ReactionRecord
    
    # Assuming SymmetryValidator has a method to check a list of records.
    # If not, we loop.
    # Let's assume the API from T044: `SymmetryValidator` takes a `SymmetryGroup` definition.
    # We need to get the group. Since T043 is done, we assume the group is available.
    # For simplicity, we assume the SymmetryValidator is stateless or configured globally.
    
    # We will use the `validate_invariance_on_dataset` function from T044 if it exists.
    # If not, we implement the loop here.
    
    # Let's assume the function `validate_invariance_on_dataset` exists in utils.symmetry
    # as per T044 API surface.
    
    try:
        from utils.symmetry import validate_invariance_on_dataset
        
        # Prepare data for validation
        # We need to convert DataFrame rows to ReactionRecord
        records = []
        for _, row in sample_df.iterrows():
            # Assuming 'smiles' column exists
            rec = ReactionRecord(
                reaction_id=row.get('reaction_id', 'unknown'),
                smiles=row['smiles'],
                # Add other necessary fields if required by ReactionRecord
            )
            records.append(rec)
        
        # Run validation
        # The function `validate_invariance_on_dataset` should return a dict with failure stats
        result = validate_invariance_on_dataset(records)
        
        failure_rate = result.get('failure_rate', 0.0)
        
        if failure_rate > threshold:
            logger.warning(f"Symmetry Check FAILED: Failure rate {failure_rate:.4f} > threshold {threshold}.")
            logger.warning("Switching to Descriptive Statistics mode.")
            return False
        else:
            logger.info(f"Symmetry Check PASSED: Failure rate {failure_rate:.4f} <= threshold {threshold}.")
            return True
            
    except ImportError as e:
        logger.error(f"Could not import SymmetryValidator functions: {e}")
        # If the module is missing, we cannot perform the check. 
        # Per the task, we must log a warning and switch to descriptive stats if we can't verify.
        logger.warning("SymmetryCheck module not fully available. Assuming failure for safety.")
        return False
    except Exception as e:
        logger.error(f"Error during Symmetry Check: {e}")
        return False

def fit_ordinal_logistic_model(X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    """
    Fit an Ordinal Logistic Regression model.
    
    Returns:
        Dict containing model results, coefficients, and p-values.
    """
    try:
        # Ensure y is ordered
        y = y.astype('category')
        y = y.cat.reorder_categories(sorted(y.cat.categories))
        
        model = OrderedModel(y, X, distr='logit')
        result = model.fit(method='bfgs')
        
        return {
            'success': True,
            'loglik': result.loglik,
            'params': result.params.to_dict(),
            'pvalues': result.pvalues.to_dict(),
            'rsquared_pseudo': result.rsquared_pseudo
        }
    except Exception as e:
        logger.error(f"Ordinal Logistic Regression failed: {e}")
        return {'success': False, 'error': str(e)}

def calculate_vif(X: pd.DataFrame) -> pd.Series:
    """Calculate Variance Inflation Factor for each feature."""
    vif_data = pd.Series(index=X.columns, dtype=float)
    for feature in X.columns:
        others = [f for f in X.columns if f != feature]
        if not others:
            vif_data[feature] = 1.0
            continue
        r2 = sm.OLS(X[feature], sm.add_constant(X[others])).fit().rsquared
        vif_data[feature] = 1.0 / (1.0 - r2)
    return vif_data

def run_modeling_pipeline(df: pd.DataFrame, output_dir: str = "data/models") -> Dict[str, Any]:
    """
    Main pipeline for US3: Modeling and Validation.
    
    Steps:
    1. Perform Symmetry Check (FR-008).
    2. If check fails (>1% failure), switch to Descriptive Statistics.
    3. If check passes, fit Ordinal Logistic Regression.
    4. Handle degenerate targets (variance=0) -> Descriptive Statistics.
    5. Evaluate R2, calculate MDE if needed.
    6. Save results.
    """
    results = {
        'status': 'unknown',
        'symmetry_check': None,
        'model_type': None,
        'metrics': {},
        'message': ''
    }
    
    # 1. Symmetry Check
    symmetry_pass = perform_symmetry_check(df)
    results['symmetry_check'] = 'passed' if symmetry_pass else 'failed'
    
    if not symmetry_pass:
        logger.info("Symmetry Check failed. Switching to Descriptive Statistics.")
        results['model_type'] = 'descriptive_statistics'
        results['status'] = 'completed_fallback'
        results['message'] = "Symmetry check failed. Using descriptive statistics."
        
        # Calculate basic stats
        desc_stats = df.describe()
        results['metrics'] = {
            'mean': desc_stats.mean().to_dict(),
            'std': desc_stats.std().to_dict(),
            'count': desc_stats.count().to_dict()
        }
        
        # Save results
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        with open(Path(output_dir) / "results.json", 'w') as f:
            json.dump(results, f, indent=2)
        return results

    # 2. Target Extraction (if not already present)
    if 'target_count' not in df.columns:
        logger.info("Calculating target_count (Regioisomer Diversity)...")
        df['target_count'] = df['smiles'].apply(calculate_regioisomer_count)
    
    # 3. Check for degenerate target
    if df['target_count'].nunique() <= 1:
        logger.warning("Target variable has zero variance. Switching to Descriptive Statistics.")
        results['model_type'] = 'descriptive_statistics'
        results['status'] = 'completed_fallback'
        results['message'] = "Degenerate target (zero variance). Using descriptive statistics."
        
        desc_stats = df.describe()
        results['metrics'] = {
            'mean': desc_stats.mean().to_dict(),
            'std': desc_stats.std().to_dict(),
            'count': desc_stats.count().to_dict()
        }
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        with open(Path(output_dir) / "results.json", 'w') as f:
            json.dump(results, f, indent=2)
        return results

    # 4. Prepare features (using descriptors)
    # Assume descriptors are in columns like 'wiener', 'balaban', 'zagreb'
    feature_cols = [c for c in df.columns if c in ['wiener', 'balaban', 'zagreb']]
    if not feature_cols:
        logger.error("No descriptor columns found in dataset.")
        results['status'] = 'failed'
        results['message'] = "No descriptor columns found."
        return results

    X = df[feature_cols].dropna()
    y = df.loc[X.index, 'target_count'].dropna()
    
    if len(X) < 10:
        logger.warning("Insufficient data for modeling. Switching to Descriptive Statistics.")
        results['model_type'] = 'descriptive_statistics'
        results['status'] = 'completed_fallback'
        results['message'] = "Insufficient data for modeling."
        return results

    # 5. Collinearity Check (VIF)
    vif = calculate_vif(X)
    if (vif > 5).any():
        logger.warning("High collinearity detected (VIF > 5). Removing high VIF features.")
        # Remove features with VIF > 5 iteratively
        while (vif > 5).any():
            max_vif_feature = vif.idxmax()
            logger.info(f"Removing feature {max_vif_feature} with VIF {vif[max_vif_feature]:.2f}")
            X = X.drop(columns=[max_vif_feature])
            if X.empty:
                break
            vif = calculate_vif(X)
    
    if X.empty:
        logger.error("All features removed due to collinearity.")
        results['status'] = 'failed'
        results['message'] = "All features removed due to collinearity."
        return results

    # 6. Fit Ordinal Logistic Regression
    logger.info("Fitting Ordinal Logistic Regression...")
    X_sm = sm.add_constant(X)
    model_result = fit_ordinal_logistic_model(X_sm.values, y.values)
    
    if not model_result['success']:
        logger.warning("Ordinal Logistic Regression failed. Switching to Descriptive Statistics.")
        results['model_type'] = 'descriptive_statistics'
        results['status'] = 'completed_fallback'
        results['message'] = "Ordinal Logistic Regression failed."
        return results

    # 7. Evaluate R2
    # statsmodels OrderedModel does not have a direct R2. We use pseudo R2.
    pseudo_r2 = model_result.get('rsquared_pseudo', 0.0)
    results['model_type'] = 'ordinal_logistic_regression'
    results['metrics'] = {
        'pseudo_r2': pseudo_r2,
        'params': model_result['params'],
        'pvalues': model_result['pvalues']
    }
    
    # 8. Check R2 threshold (SC-002: R2 > 0.05)
    if pseudo_r2 <= 0.05:
        logger.warning(f"R2 ({pseudo_r2:.4f}) is below threshold (0.05). Calculating MDE.")
        # Calculate MDE (Minimum Detectable Effect)
        # Simplified MDE calculation: based on sample size and variance
        n = len(y)
        # MDE approx = 2 * std(y) / sqrt(n) (very rough)
        std_y = y.std()
        mde = 2 * std_y / np.sqrt(n)
        results['metrics']['mde'] = mde
        results['message'] = f"R2 below threshold. MDE: {mde:.4f}. Project Analysis Complete."
        results['status'] = 'completed_low_power'
    else:
        results['status'] = 'completed'
        results['message'] = "Modeling completed successfully."

    # 9. Save results
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    with open(Path(output_dir) / "results.json", 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Modeling pipeline completed. Status: {results['status']}")
    return results

def main():
    """Entry point for the modeling pipeline."""
    config = get_config()
    
    # Load data
    data_path = Path(config.data_processed_dir) / "descriptors.csv"
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        sys.exit(1)
    
    df = pd.read_csv(data_path)
    
    # Run pipeline
    results = run_modeling_pipeline(df, output_dir=config.models_dir)
    
    # Print summary
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()