import json
import logging
import os
import random
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_absolute_error, r2_score
from scipy.stats import spearmanr

# Local imports matching API surface
from metrics import calculate_mae, calculate_r2, calculate_spearman_rho, calculate_deviation_index, calculate_all_metrics
from ingest import load_manifest, validate_manifest, fetch_dataset, find_supplementary_files, parse_pdf_for_metadata, parse_csv_for_metadata, process_manifest_entry, verify_dataset_variables, ingest_pipeline, main as ingest_main
from failure_logger import FailureReason, load_existing_failure_log, record_failure, compile_failure_summary, write_failure_report, main as failure_main

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('artifacts/logs/model_runner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

PARAMETER_LIMIT = 1_000_000  # 1M parameters
RANDOM_FOREST_N_ESTIMATORS = 100
RANDOM_FOREST_MAX_DEPTH = 5
DEFAULT_SEED = 42

def set_seed(seed: int = DEFAULT_SEED) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Random seed set to {seed}")

def count_model_parameters(model) -> int:
    """Count total parameters in a model."""
    if hasattr(model, 'get_params'):
        # For sklearn models, we estimate based on structure if possible
        # For RF, n_estimators * (tree_size approx)
        if isinstance(model, RandomForestRegressor):
            # Rough estimate: trees * nodes * features (simplified)
            # Actual parameter count in RF is complex, but we can estimate
            n_trees = model.n_estimators
            # Approximate: each tree has ~2^max_depth nodes, each node has feature split info
            # This is a heuristic estimate
            return n_trees * (2 ** model.max_depth) * 10  # rough multiplier
        return 0  # Default for unknown models
    return 0

def load_processed_data(data_path: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Load processed data from the specified path."""
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Processed data not found at {data_path}")
    
    # Try to load CSV or JSON
    if path.suffix == '.csv':
        df = pd.read_csv(path)
    elif path.suffix == '.json':
        with open(path, 'r') as f:
            data = json.load(f)
            df = pd.DataFrame(data)
    else:
        # Try CSV by default
        df = pd.read_csv(str(path))
    
    logger.info(f"Loaded data with {len(df)} rows and {len(df.columns)} columns")
    return df, {}

def encode_smiles(smiles_list: List[str]) -> np.ndarray:
    """Encode SMILES strings into molecular fingerprints."""
    try:
        from rdkit import Chem
        from rdkit.Chem import AllChem
    except ImportError:
        raise ImportError("RDKit is required for SMILES encoding. Install with: pip install rdkit")
    
    fingerprints = []
    for smi in smiles_list:
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            # Handle invalid SMILES
            fp = np.zeros(2048)
        else:
            fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)
            fp = np.array(fp)
        fingerprints.append(fp)
    
    return np.array(fingerprints)

def train_model(X_train: np.ndarray, y_train: np.ndarray, 
                use_rf_baseline: bool = False, 
                seed: int = DEFAULT_SEED) -> Tuple[Any, str]:
    """Train a model, substituting with RF if needed."""
    set_seed(seed)
    
    if use_rf_baseline:
        logger.info("Using Random Forest baseline (model substitution)")
        model = RandomForestRegressor(
            n_estimators=RANDOM_FOREST_N_ESTIMATORS,
            max_depth=RANDOM_FOREST_MAX_DEPTH,
            random_state=seed,
            n_jobs=-1
        )
        model.fit(X_train, y_train)
        return model, "RandomForest"
    else:
        # For now, use RF as the default model since we don't have deep learning setup
        # In a full implementation, this would load the reported model architecture
        logger.info("Training Random Forest model (default baseline)")
        model = RandomForestRegressor(
            n_estimators=RANDOM_FOREST_N_ESTIMATORS,
            max_depth=RANDOM_FOREST_MAX_DEPTH,
            random_state=seed,
            n_jobs=-1
        )
        model.fit(X_train, y_train)
        return model, "RandomForest"

def evaluate_model(model: Any, X_test: np.ndarray, y_test: np.ndarray, 
                   reported_metrics: Dict[str, float]) -> Dict[str, Any]:
    """Evaluate model and compute metrics."""
    y_pred = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    rho, _ = spearmanr(y_test, y_pred)
    
    # Calculate deviations
    reported_mae = reported_metrics.get('mae', 0)
    reported_r2 = reported_metrics.get('r2', 0)
    reported_rho = reported_metrics.get('rho', 0)
    
    deviation_mae = abs(mae - reported_mae)
    deviation_r2 = abs(r2 - reported_r2)
    deviation_rho = abs(rho - reported_rho)
    
    return {
        'mae': mae,
        'r2': r2,
        'rho': rho,
        'deviation_mae': deviation_mae,
        'deviation_r2': deviation_r2,
        'deviation_rho': deviation_rho,
        'predicted_values': y_pred.tolist(),
        'actual_values': y_test.tolist()
    }

def run_sensitivity_analysis(data_path: str, reported_metrics: Dict[str, float],
                             seeds: List[int] = [42, 123, 999]) -> Dict[str, float]:
    """Run sensitivity analysis with different seeds."""
    results = {}
    metric_variances = {'mae': [], 'r2': [], 'rho': []}
    
    for seed in seeds:
        set_seed(seed)
        df, _ = load_processed_data(data_path)
        
        # Prepare features and target
        if 'smiles' in df.columns:
            X = encode_smiles(df['smiles'].tolist())
        else:
            # Use numeric columns as features
            feature_cols = [c for c in df.columns if c not in ['yield', 'target', 'smiles']]
            X = df[feature_cols].values
        
        y = df['yield'].values if 'yield' in df.columns else df['target'].values
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=seed)
        
        model, _ = train_model(X_train, y_train, seed=seed)
        eval_results = evaluate_model(model, X_test, y_test, reported_metrics)
        
        metric_variances['mae'].append(eval_results['mae'])
        metric_variances['r2'].append(eval_results['r2'])
        metric_variances['rho'].append(eval_results['rho'])
    
    # Calculate standard deviations
    max_std = 0
    for metric, values in metric_variances.items():
        std_dev = np.std(values)
        results[f'{metric}_std'] = std_dev
        if std_dev > max_std:
            max_std = std_dev
    
    results['max_metric_std'] = max_std
    return results

def run_reproducibility_assessment(paper_doi: str, data_path: str, 
                                   reported_metrics: Dict[str, float],
                                   experimental_replicates: Optional[int] = None,
                                   reaction_conditions: Optional[Dict[str, Any]] = None,
                                   yield_std_dev: Optional[float] = None) -> Dict[str, Any]:
    """Run full reproducibility assessment for a single paper."""
    logger.info(f"Starting reproducibility assessment for paper: {paper_doi}")
    
    try:
        # Load data
        df, metadata = load_processed_data(data_path)
        
        # Prepare features and target
        if 'smiles' in df.columns:
            X = encode_smiles(df['smiles'].tolist())
        else:
            # Use numeric columns as features
            feature_cols = [c for c in df.columns if c not in ['yield', 'target', 'smiles']]
            if not feature_cols:
                raise ValueError("No feature columns found in dataset")
            X = df[feature_cols].values
        
        y = df['yield'].values if 'yield' in df.columns else df['target'].values
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Check parameter count and decide on model substitution
        # For now, we use RF as baseline, but we log if original model would exceed limit
        # Since we don't have the original model, we assume substitution if data suggests complexity
        use_rf_baseline = True  # Default to RF baseline
        model_substituted = True
        substitution_reason = "Model Substitution/Unavailable"
        
        # Train model
        model, model_type = train_model(X_train, y_train, use_rf_baseline=use_rf_baseline, seed=42)
        
        # Evaluate
        eval_results = evaluate_model(model, X_test, y_test, reported_metrics)
        
        # Run sensitivity analysis
        sensitivity_results = run_sensitivity_analysis(data_path, reported_metrics)
        
        # Calculate reproducibility score S (simple weighted average of deviations)
        deviation_mae = eval_results['deviation_mae']
        deviation_r2 = eval_results['deviation_r2']
        deviation_rho = eval_results['deviation_rho']
        
        # Normalize deviations (assuming typical ranges)
        norm_mae = deviation_mae / (deviation_mae + 1)  # Simple normalization
        norm_r2 = deviation_r2 / (deviation_r2 + 1)
        norm_rho = deviation_rho / (deviation_rho + 1)
        
        score_s = 1 - (norm_mae * 0.4 + norm_r2 * 0.3 + norm_rho * 0.3)
        
        # Compile results
        result = {
            'doi': paper_doi,
            'mae': eval_results['mae'],
            'r2': eval_results['r2'],
            'rho': eval_results['rho'],
            'deviation_mae': deviation_mae,
            'deviation_r2': deviation_r2,
            'deviation_rho': deviation_rho,
            'score_s': score_s,
            'max_metric_std': sensitivity_results['max_metric_std'],
            'flags': [],
            'experimental_replicates': experimental_replicates,
            'reaction_conditions': reaction_conditions,
            'yield_std_dev': yield_std_dev,
            'model_substituted': model_substituted,
            'substitution_reason': substitution_reason if model_substituted else None,
            'model_type': model_type,
            'sensitivity_analysis': sensitivity_results
        }
        
        # Add flags if needed
        if experimental_replicates is None:
            result['flags'].append('missing_replicates')
        if reaction_conditions is None:
            result['flags'].append('missing_conditions')
        if yield_std_dev is None:
            result['flags'].append('missing_yield_std')
        
        # Log substitution if applicable
        if model_substituted:
            logger.warning(f"Model substitution applied for {paper_doi}: {substitution_reason}")
            record_failure(
                paper_doi=paper_doi,
                failure_mode=FailureReason.MODEL_SUBSTITUTION,
                details=substitution_reason
            )
        
        logger.info(f"Completed assessment for {paper_doi}: MAE={eval_results['mae']:.4f}, R2={eval_results['r2']:.4f}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing {paper_doi}: {str(e)}")
        record_failure(
            paper_doi=paper_doi,
            failure_mode=FailureReason.PROCESSING_ERROR,
            details=str(e)
        )
        return {
            'doi': paper_doi,
            'mae': None,
            'r2': None,
            'rho': None,
            'deviation_mae': None,
            'deviation_r2': None,
            'deviation_rho': None,
            'score_s': None,
            'max_metric_std': None,
            'flags': ['processing_error'],
            'experimental_replicates': experimental_replicates,
            'reaction_conditions': reaction_conditions,
            'yield_std_dev': yield_std_dev,
            'model_substituted': False,
            'substitution_reason': None,
            'model_type': None,
            'sensitivity_analysis': {},
            'error': str(e)
        }

def main():
    """Main entry point for model runner."""
    logger.info("Starting model runner pipeline")
    
    # Load manifest
    manifest_path = Path("data/manifest.csv")
    if not manifest_path.exists():
        manifest_path = Path("data/manifest.yaml")
    
    if not manifest_path.exists():
        logger.error("No manifest file found")
        return
    
    manifests = load_manifest(str(manifest_path))
    
    # Ensure output directory exists
    output_dir = Path("artifacts/reports")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    for manifest in manifests:
        doi = manifest.get('doi', 'unknown')
        data_path = manifest.get('processed_data_path', f"data/processed/{doi}_processed.csv")
        reported_metrics = manifest.get('reported_metrics', {})
        experimental_replicates = manifest.get('experimental_replicates')
        reaction_conditions = manifest.get('reaction_conditions')
        yield_std_dev = manifest.get('yield_std_dev')
        
        result = run_reproducibility_assessment(
            paper_doi=doi,
            data_path=data_path,
            reported_metrics=reported_metrics,
            experimental_replicates=experimental_replicates,
            reaction_conditions=reaction_conditions,
            yield_std_dev=yield_std_dev
        )
        
        results.append(result)
    
    # Write results to JSON
    output_path = output_dir / "repro_results.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Reproducibility results written to {output_path}")
    
    # Compile and write failure log
    failure_summary = compile_failure_summary()
    write_failure_report(failure_summary)
    
    logger.info("Model runner pipeline completed")

if __name__ == "__main__":
    main()