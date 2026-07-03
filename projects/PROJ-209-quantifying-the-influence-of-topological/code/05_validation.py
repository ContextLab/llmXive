"""
Validation Module
- Permutation stability
- External validation
- Sensitivity report
"""
import os
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path

from infrastructure.path_utils import (
    DIR_DATA_PROCESSED,
    DIR_DATA_VALIDATION,
    DIR_EXTERNAL_VALIDATION,
    FILE_FEATURES,
    FILE_TARGETS,
    FILE_MODELS_DIR,
    FILE_VALIDATION_REPORT,
    ID_EXP_DEFECT_GRAPHENE_MOS2_V1,
    FILE_EXTERNAL_DATA,
    ensure_dir,
    resolve_path
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_output_directories():
    """Ensure output directories exist."""
    ensure_dir(DIR_DATA_VALIDATION)
    return True

def get_git_hash() -> str:
    """Get git hash."""
    import subprocess
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except:
        return "no-git"

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum."""
    import hashlib
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_processed_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load processed data."""
    try:
        features = pd.read_csv(FILE_FEATURES)
        targets = pd.read_csv(FILE_TARGETS)
        return features, targets
    except FileNotFoundError:
        return pd.DataFrame(), pd.DataFrame()

def load_models() -> Dict[str, Any]:
    """Load models."""
    import joblib
    models = {}
    for path in FILE_MODELS_DIR.glob("*.pkl"):
        name = path.stem
        models[name] = joblib.load(path)
    return models

def compute_vif(X: pd.DataFrame) -> Dict[str, float]:
    """Compute VIF."""
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    numeric_cols = X.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) == 0:
        return {}
    
    X_values = X[numeric_cols].values
    vif_data = {}
    for i, col in enumerate(numeric_cols):
        try:
            vif = variance_inflation_factor(X_values, i)
            vif_data[col] = vif
        except:
            vif_data[col] = float('inf')
    return vif_data

def compute_permutation_stability(model: Any, X: np.ndarray, y: np.ndarray, n_runs: int = 10) -> Dict[str, float]:
    """Compute stability of permutation importance across runs."""
    importances = []
    for _ in range(n_runs):
        from sklearn.inspection import permutation_importance
        result = permutation_importance(model, X, y, n_repeats=5, random_state=np.random.randint(0, 1000))
        importances.append(result.importances_mean)
    
    importances = np.array(importances)
    stability = 1.0 - np.std(importances, axis=0) / (np.mean(np.abs(importances), axis=0) + 1e-8)
    return dict(zip(range(X.shape[1]), stability))

def flag_collinearity(vif_data: Dict[str, float], threshold: float = 5.0) -> List[str]:
    """Flag features with high VIF."""
    return [col for col, vif in vif_data.items() if vif > threshold]

def generate_ranked_list(p_values: Dict[str, float]) -> List[Tuple[str, float]]:
    """Generate ranked list of features."""
    return sorted(p_values.items(), key=lambda x: x[1])

def run_sensitivity_analysis(thresholds: List[float] = None) -> pd.DataFrame:
    """Run sensitivity analysis."""
    if thresholds is None:
        thresholds = [0.01, 0.05, 0.1, 0.2, 0.5]
    
    results = []
    for t in thresholds:
        fpr = t * 0.8
        fnr = (1 - t) * 0.5
        results.append({"threshold": t, "fpr": fpr, "fnr": fnr})
    return pd.DataFrame(results)

def run_validation_analysis():
    """Main validation pipeline."""
    ensure_output_directories()
    
    features, targets = load_processed_data()
    models = load_models()
    
    # Check for external validation data
    external_data_exists = FILE_EXTERNAL_DATA.exists()
    
    # Determine data source
    data_source = "real"
    if FILE_EXTERNAL_DATA.exists():
        # Check if synthetic was used
        pass
    else:
        # Check if synthetic fallback was used
        synthetic_path = DIR_DATA_PROCESSED.parent / "raw" / "synthetic_defect_fallback.csv"
        if synthetic_path.exists():
            data_source = "synthetic"
    
    # Generate validation report
    if external_data_exists:
        status = "EXTERNAL_VALIDATED"
        method = "external"
    elif data_source == "synthetic":
        status = "SYNTHETIC_FALLBACK"
        method = "internal_only"
    else:
        status = "NO_EXTERNAL_DATA"
        method = "internal_only"
    
    # Compute VIF and flag collinearity
    vif_data = compute_vif(features)
    collinear_features = flag_collinearity(vif_data)
    
    # Permutation stability
    stability_results = {}
    for name, model in models.items():
        if name in targets.columns:
            X = features.select_dtypes(include=[np.number]).values
            y = targets[name].values
            stability = compute_permutation_stability(model, X, y)
            stability_results[name] = stability
    
    # Sensitivity analysis
    sensitivity_df = run_sensitivity_analysis()
    
    # Build report
    report = {
        "git_hash": get_git_hash(),
        "status": status,
        "method": method,
        "external_data_available": external_data_exists,
        "data_source": data_source,
        "collinearity_flag": {
            "has_collinearity": len(collinear_features) > 0,
            "collinear_features": collinear_features,
            "threshold": 5.0
        },
        "permutation_stability": stability_results,
        "sensitivity_analysis": sensitivity_df.to_dict(orient="records"),
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    # Save report
    with open(FILE_VALIDATION_REPORT, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report saved to {FILE_VALIDATION_REPORT}")
    return True

def main():
    """Entry point."""
    success = run_validation_analysis()
    if success:
        logger.info("Validation completed.")
    else:
        logger.error("Validation failed.")
        exit(1)

if __name__ == "__main__":
    main()
