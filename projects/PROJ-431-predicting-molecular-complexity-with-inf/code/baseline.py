import os
import json
import pickle
from typing import Dict, Any, Tuple, List, Optional
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split
from scipy.stats import pearsonr
from scipy.stats import zscore
from sklearn.metrics import mean_squared_error

# Constants
RANDOM_STATE = 42
TARGET_RMSE = "rmse"
TARGET_PEARSON = "pearson_r"
TARGET_PVALUE = "p_value"

def compute_molecular_weight(smiles: str) -> float:
    """
    Compute molecular weight from SMILES string using RDKit.
    
    Args:
        smiles: SMILES string
        
    Returns:
        Molecular weight in g/mol, or NaN if invalid
    """
    try:
        from rdkit import Chem
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return np.nan
        return rdMolDescriptors.CalcMolWt(mol)
    except Exception:
        return np.nan

def compute_atom_count(smiles: str) -> int:
    """
    Count atoms in molecule from SMILES string using RDKit.
    
    Args:
        smiles: SMILES string
        
    Returns:
        Number of atoms, or 0 if invalid
    """
    try:
        from rdkit import Chem
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return 0
        return mol.GetNumAtoms()
    except Exception:
        return 0

def train_baseline_models(
    df: pd.DataFrame, 
    target_col: str, 
    feature_cols: List[str]
) -> Dict[str, Any]:
    """
    Train baseline models and compute metrics.
    
    Args:
        df: DataFrame with features and target
        target_col: Name of target column
        feature_cols: List of feature column names
        
    Returns:
        Dictionary with model metrics
    """
    # Split data
    X = df[feature_cols].values
    y = df[target_col].values
    
    # Handle NaN
    mask = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
    X = X[mask]
    y = y[mask]
    
    if len(X) == 0:
        return {
            "model_type": "baseline",
            "features": feature_cols,
            "target": target_col,
            "n_samples": 0,
            "rmse": np.nan,
            "pearson_r": np.nan,
            "p_value": np.nan
        }
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE
    )
    
    # Train Ridge model
    model = Ridge(alpha=1.0)
    model.fit(X_train, y_train)
    
    # Predict
    y_pred = model.predict(X_test)
    
    # Compute metrics
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    pearson_r, p_value = pearsonr(y_test, y_pred)
    
    return {
        "model_type": "baseline",
        "features": feature_cols,
        "target": target_col,
        "n_samples": len(X_test),
        "rmse": float(rmse),
        "pearson_r": float(pearson_r),
        "p_value": float(p_value)
    }

def compute_partial_correlation(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    z_cols: List[str]
) -> Dict[str, float]:
    """
    Compute partial correlation between x and y, controlling for z variables.
    
    Args:
        df: DataFrame
        x_col: Primary variable
        y_col: Target variable
        z_cols: Control variables
        
    Returns:
        Dictionary with partial correlation and p-value
    """
    # Extract variables
    x = df[x_col].values
    y = df[y_col].values
    z = df[z_cols].values if z_cols else np.array([])
    
    # Handle NaN
    mask = ~np.isnan(x) & ~np.isnan(y)
    if z.size > 0:
        mask &= ~np.isnan(z).any(axis=1)
    
    x = x[mask]
    y = y[mask]
    if z.size > 0:
        z = z[mask]
    
    if len(x) < 3:
        return {
            "partial_corr": np.nan,
            "p_value": np.nan,
            "n_samples": len(x)
        }
    
    # Compute partial correlation
    from scipy import stats
    
    if z.size == 0:
        # No control variables
        corr, p_val = stats.pearsonr(x, y)
        return {
            "partial_corr": float(corr),
            "p_value": float(p_val),
            "n_samples": len(x)
        }
    
    # Residualize x and y with respect to z
    from sklearn.linear_model import LinearRegression
    
    # Residualize x
    lr_x = LinearRegression()
    lr_x.fit(z, x)
    x_resid = x - lr_x.predict(z)
    
    # Residualize y
    lr_y = LinearRegression()
    lr_y.fit(z, y)
    y_resid = y - lr_y.predict(z)
    
    # Compute correlation of residuals
    corr, p_val = stats.pearsonr(x_resid, y_resid)
    
    return {
        "partial_corr": float(corr),
        "p_value": float(p_val),
        "n_samples": len(x)
    }

def run_baseline_analysis(
    input_csv: str,
    output_json: str,
    output_pkl: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run complete baseline analysis and save results.
    
    Args:
        input_csv: Path to input CSV with entropy scores and properties
        output_json: Path to output JSON report
        output_pkl: Optional path to save baseline models
        
    Returns:
        Dictionary with all baseline results
    """
    # Load data
    df = pd.read_csv(input_csv)
    
    # Compute MW and atom count if not present
    if "molecular_weight" not in df.columns:
        df["molecular_weight"] = df["smiles"].apply(compute_molecular_weight)
    if "atom_count" not in df.columns:
        df["atom_count"] = df["smiles"].apply(compute_atom_count)
    
    # Define baselines
    baselines = {
        "mean_only": [],  # Will use mean of target
        "mw_only": ["molecular_weight"],
        "mw_plus_atoms": ["molecular_weight", "atom_count"]
    }
    
    results = {
        "logS": {},
        "logP": {},
        "partial_correlations": {}
    }
    
    # Train baselines for logS
    for name, features in baselines.items():
        if name == "mean_only":
            # Mean model: predict mean of training set
            y = df["logS"].values
            mask = ~np.isnan(y)
            if np.sum(mask) > 0:
                mean_val = np.mean(y[mask])
                # RMSE on test set
                X_train, X_test, y_train, y_test = train_test_split(
                    np.arange(len(y)), y, test_size=0.2, random_state=RANDOM_STATE
                )
                y_pred = np.full(len(y_test), mean_val)
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                results["logS"][name] = {
                    "model_type": "mean",
                    "target": "logS",
                    "n_samples": len(y_test),
                    "rmse": float(rmse),
                    "pearson_r": 0.0,
                    "p_value": 1.0,
                    "mean_value": float(mean_val)
                }
        else:
            # Ridge baseline
            result = train_baseline_models(df, "logS", features)
            result["model_name"] = name
            results["logS"][name] = result
    
    # Train baselines for logP
    for name, features in baselines.items():
        if name == "mean_only":
            y = df["logP"].values
            mask = ~np.isnan(y)
            if np.sum(mask) > 0:
                mean_val = np.mean(y[mask])
                X_train, X_test, y_train, y_test = train_test_split(
                    np.arange(len(y)), y, test_size=0.2, random_state=RANDOM_STATE
                )
                y_pred = np.full(len(y_test), mean_val)
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                results["logP"][name] = {
                    "model_type": "mean",
                    "target": "logP",
                    "n_samples": len(y_test),
                    "rmse": float(rmse),
                    "pearson_r": 0.0,
                    "p_value": 1.0,
                    "mean_value": float(mean_val)
                }
        else:
            result = train_baseline_models(df, "logP", features)
            result["model_name"] = name
            results["logP"][name] = result
    
    # Compute partial correlations
    # Control for MW and atom count
    control_vars = ["molecular_weight", "atom_count"]
    
    # For logS
    partial_logS = compute_partial_correlation(
        df, "atom_entropy", "logS", control_vars
    )
    partial_logS["feature"] = "atom_entropy"
    partial_logS["target"] = "logS"
    results["partial_correlations"]["logS"] = partial_logS
    
    partial_logS_bond = compute_partial_correlation(
        df, "bond_entropy", "logS", control_vars
    )
    partial_logS_bond["feature"] = "bond_entropy"
    partial_logS_bond["target"] = "logS"
    results["partial_correlations"]["logS_bond"] = partial_logS_bond
    
    # For logP
    partial_logP = compute_partial_correlation(
        df, "atom_entropy", "logP", control_vars
    )
    partial_logP["feature"] = "atom_entropy"
    partial_logP["target"] = "logP"
    results["partial_correlations"]["logP"] = partial_logP
    
    partial_logP_bond = compute_partial_correlation(
        df, "bond_entropy", "logP", control_vars
    )
    partial_logP_bond["feature"] = "bond_entropy"
    partial_logP_bond["target"] = "logP"
    results["partial_correlations"]["logP_bond"] = partial_logP_bond
    
    # Save JSON
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Save models if requested
    if output_pkl:
        os.makedirs(os.path.dirname(output_pkl), exist_ok=True)
        with open(output_pkl, 'wb') as f:
            pickle.dump(results, f)
    
    return results

def main():
    """CLI entry point for baseline analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run baseline models and partial correlation analysis")
    parser.add_argument("--input", type=str, required=True, help="Input CSV with entropy scores")
    parser.add_argument("--output", type=str, required=True, help="Output JSON report path")
    parser.add_argument("--models", type=str, default=None, help="Optional path to save models")
    
    args = parser.parse_args()
    
    results = run_baseline_analysis(args.input, args.output, args.models)
    print(f"Baseline analysis complete. Results saved to {args.output}")
    return results

if __name__ == "__main__":
    main()