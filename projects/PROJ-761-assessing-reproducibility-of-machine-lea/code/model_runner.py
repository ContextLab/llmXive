import json
import logging
import os
import random
import numpy as np
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
from scipy.stats import spearmanr
import rdkit.Chem as Chem
from rdkit import DataStructs
from rdkit.Chem import AllChem
from metrics import calculate_mae, calculate_r2, calculate_spearman_rho, calculate_deviation_index, calculate_all_metrics

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
SEEDS_TO_SWEEP = [42, 123, 999]
MAX_MODEL_PARAMS = 1_000_000
DEFAULT_SEED = 42

def count_model_parameters(model: Any) -> int:
    """Count total number of trainable parameters in a scikit-learn model."""
    total_params = 0
    for attr_name in dir(model):
        attr = getattr(model, attr_name, None)
        if hasattr(attr, 'shape') and hasattr(attr, 'dtype'):
            # Check if it's a numpy array (parameter array)
            if isinstance(attr, np.ndarray):
                total_params += attr.size
    return total_params

def load_processed_data(data_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """Load processed data from CSV/Parquet. Returns (X, y)."""
    import pandas as pd
    path = Path(data_path)
    if path.suffix == '.csv':
        df = pd.read_csv(path)
    elif path.suffix == '.parquet':
        df = pd.read_parquet(path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")
    
    # Assume columns 'features' (array string) and 'yield' (target)
    # Or standard numeric features if 'features' not present
    if 'features' in df.columns:
        # Parse string representation of lists if necessary
        try:
            X = np.array([np.fromstring(f.strip('[]'), sep=',') for f in df['features'].astype(str)])
        except Exception:
            # Fallback for list of lists
            X = np.array([np.array(f) if isinstance(f, list) else np.array([float(f)]) for f in df['features']])
        y = df['yield'].values
    elif 'yield' in df.columns:
        # Assume all other columns are features
        feature_cols = [c for c in df.columns if c != 'yield']
        X = df[feature_cols].values
        y = df['yield'].values
    else:
        raise ValueError("Dataset must contain 'yield' column and either 'features' or numeric columns.")
    
    return X, y

def encode_smiles(smiles_list: List[str]) -> np.ndarray:
    """Convert list of SMILES strings to ECFP4 fingerprints."""
    fingerprints = []
    for smi in smiles_list:
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            # Fallback or raise error depending on strictness
            fp = np.zeros(2048)
        else:
            fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)
            arr = np.zeros((2048,), dtype=int)
            DataStructs.ConvertToNumpyArray(fp, arr)
            fingerprints.append(arr)
    return np.array(fingerprints)

def train_model(X: np.ndarray, y: np.ndarray, seed: int = 42, max_params: int = MAX_MODEL_PARAMS) -> Tuple[Any, bool]:
    """
    Train a model. If the specified model exceeds max_params, substitute with a baseline.
    Returns (model, was_substituted).
    """
    random.seed(seed)
    np.random.seed(seed)
    
    # Attempt to use a standard model (Random Forest as baseline)
    # RF parameter count is roughly n_estimators * n_features * tree_depth (approx)
    # We will train a small RF first to check, or just use a fixed small config
    # For strict adherence: Try a complex model, check count, if > limit, switch to small RF.
    
    # Let's assume the "reported" model logic is abstracted here.
    # We will instantiate a RandomForest with n_estimators=100 as the "target"
    # and check its parameter count. If it exceeds limit, we reduce n_estimators.
    
    # Note: scikit-learn RF doesn't expose a direct "num_params" property easily
    # without inspecting estimators_. We approximate or count explicitly.
    
    # Strategy: Train a standard RF. If param count > 1M, retrain with fewer trees.
    
    # Initial attempt with reasonable size
    base_rf = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=seed, n_jobs=1)
    
    # Count parameters (approximate: sum of nodes * features in trees)
    # For strict count, we'd need to sum over all trees.
    # Let's implement a helper to count RF params properly
    def count_rf_params(rf: RandomForestRegressor) -> int:
        count = 0
        for tree in rf.estimators_:
            # Tree structure: nodes * features + thresholds + impurities etc.
            # Approximate: number of nodes * (n_features + 1)
          count += tree.tree_.node_count * (rf.n_features_in_ + 1)
        return count

    estimated_params = count_rf_params(base_rf)
    
    if estimated_params > max_params:
        logger.warning(f"Model parameter count ({estimated_params}) exceeds limit ({max_params}). Substituting with baseline.")
        # Reduce n_estimators to fit
        # Simple scaling: target_params = max_params
        # n_estimators_new = max_params / (n_features * avg_depth)
        # Just reduce significantly
        new_n_est = max(1, int((max_params / 100) * (100 / base_rf.n_estimators)))
        base_rf = RandomForestRegressor(n_estimators=new_n_est, max_depth=5, random_state=seed, n_jobs=1)
        return base_rf, True
    
    return base_rf, False

def evaluate_model(model: Any, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
    """Evaluate model and return metrics."""
    y_pred = model.predict(X)
    mae = calculate_mae(y, y_pred)
    r2 = calculate_r2(y, y_pred)
    rho, _ = calculate_spearman_rho(y, y_pred)
    return {
        "MAE": float(mae),
        "R2": float(r2),
        "SpearmanRho": float(rho)
    }

def run_sensitivity_analysis(X: np.ndarray, y: np.ndarray, seeds: List[int] = SEEDS_TO_SWEEP) -> Dict[str, Any]:
    """
    Run model training and evaluation for a list of seeds.
    Compute standard deviation for each metric and the maximum observed.
    """
    results = []
    metric_keys = ["MAE", "R2", "SpearmanRho"]
    
    logger.info(f"Running sensitivity analysis with seeds: {seeds}")
    
    for seed in seeds:
        logger.info(f"Training with seed {seed}...")
        model, substituted = train_model(X, y, seed=seed)
        metrics = evaluate_model(model, X, y)
        results.append({
            "seed": seed,
            "metrics": metrics,
            "substituted": substituted
        })
    
    # Compute stats
    mae_vals = [r["metrics"]["MAE"] for r in results]
    r2_vals = [r["metrics"]["R2"] for r in results]
    rho_vals = [r["metrics"]["SpearmanRho"] for r in results]
    
    metric_std = {
        "MAE": float(np.std(mae_vals, ddof=1)),
        "R2": float(np.std(r2_vals, ddof=1)),
        "SpearmanRho": float(np.std(rho_vals, ddof=1))
    }
    
    max_metric_std = max(metric_std.values())
    
    return {
        "sensitivity_results": results,
        "metric_std": metric_std,
        "max_metric_std": float(max_metric_std)
    }

def run_reproducibility_assessment(
    data_path: str,
    reported_metrics: Optional[Dict[str, float]] = None,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main function to run reproducibility assessment including sensitivity analysis.
    """
    logger.info(f"Loading data from {data_path}")
    try:
        X, y = load_processed_data(data_path)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return {"error": str(e), "status": "Data Unavailable"}
    
    # Run sensitivity analysis
    sensitivity_data = run_sensitivity_analysis(X, y)
    
    # If reported metrics are provided, calculate deviations
    deviation_data = None
    if reported_metrics:
        # We need a reference run to compare against reported metrics
        # Let's use the seed 42 result as the primary reproducible run
        ref_seed = 42
        ref_result = next((r for r in sensitivity_data["sensitivity_results"] if r["seed"] == ref_seed), None)
        
        if ref_result:
            ref_metrics = ref_result["metrics"]
            dev_mae = abs(ref_metrics["MAE"] - reported_metrics.get("MAE", 0))
            dev_r2 = abs(ref_metrics["R2"] - reported_metrics.get("R2", 0))
            dev_rho = abs(ref_metrics["SpearmanRho"] - reported_metrics.get("SpearmanRho", 0))
            
            # Calculate Deviation Index S
            epsilon = 1e-6
            term_mae = dev_mae / (abs(reported_metrics.get("MAE", 0)) + epsilon)
            term_r2 = dev_r2 / (abs(reported_metrics.get("R2", 0)) + epsilon)
            term_rho = dev_rho / (abs(reported_metrics.get("SpearmanRho", 0)) + epsilon)
            s_score = 1 - (term_mae + term_r2 + term_rho) / 3.0
            
            deviation_data = {
                "deviation_mae": float(dev_mae),
                "deviation_r2": float(dev_r2),
                "deviation_rho": float(dev_rho),
                "deviation_index_S": float(s_score),
                "reference_seed": ref_seed
            }
        else:
            deviation_data = {"error": "Reference seed result not found"}
    
    repro_result = {
        "data_source": data_path,
        "sensitivity_analysis": sensitivity_data,
        "deviation_analysis": deviation_data,
        "status": "Success"
    }
    
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(repro_result, f, indent=2)
        logger.info(f"Results written to {output_path}")
    
    return repro_result

def main():
    """Entry point for CLI execution."""
    import argparse
    parser = argparse.ArgumentParser(description="Run reproducibility assessment and sensitivity analysis.")
    parser.add_argument("--data", type=str, required=True, help="Path to processed data file.")
    parser.add_argument("--output", type=str, default="artifacts/reports/repro_results.json", help="Output JSON path.")
    parser.add_argument("--reported-metrics", type=str, default=None, help="Path to JSON with reported metrics (optional).")
    args = parser.parse_args()
    
    reported_metrics = None
    if args.reported_metrics:
        with open(args.reported_metrics, 'r') as f:
            reported_metrics = json.load(f)
    
    result = run_reproducibility_assessment(
        data_path=args.data,
        reported_metrics=reported_metrics,
        output_path=args.output
    )
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()