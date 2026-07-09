import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.formula.api import mixedlm
import sys

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))

from config import is_synthetic, is_methodology_validation_mode
from collinearity import check_and_handle_collinearity
from memory_monitor import check_and_warn, enforce_limit

logger = logging.getLogger(__name__)

def load_preprocessed_data(data_dir: Path) -> pd.DataFrame:
    """Load preprocessed data from JSON or CSV."""
    json_path = data_dir / "connectivity_metrics.json"
    csv_path = data_dir / "connectivity_metrics.csv"
    
    if json_path.exists():
        with open(json_path, "r") as f:
            data = json.load(f)
        return pd.DataFrame(data)
    elif csv_path.exists():
        return pd.read_csv(csv_path)
    else:
        raise FileNotFoundError(f"No preprocessed data found in {data_dir}")

def check_multicollinearity(df: pd.DataFrame, predictors: List[str]) -> Dict[str, Any]:
    """Check for multicollinearity among predictors."""
    from collinearity import calculate_vif
    
    if len(predictors) < 2:
        return {"vif_values": {}, "max_vif": 0.0, "is_collinear": False}
    
    vif_values = {}
    for col in predictors:
        try:
            vif_values[col] = calculate_vif(df, col, predictors)
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")
            vif_values[col] = float('inf')
    
    max_vif = max(vif_values.values()) if vif_values else 0.0
    return {
        "vif_values": vif_values,
        "max_vif": max_vif,
        "is_collinear": max_vif > 5
    }

def fit_linear_mixed_effects_model(
    df: pd.DataFrame,
    outcome: str,
    predictors: List[str],
    subject_col: str = "subject_id",
    time_col: str = "time_point"
) -> Dict[str, Any]:
    """
    Fit a Linear Mixed-Effects Model:
    Outcome ~ Predictors + Time + (1|Subject)
    """
    if df.empty:
        raise ValueError("DataFrame is empty. Cannot fit model.")
    
    # Check memory
    check_and_warn()
    
    # Prepare formula
    formula = f"{outcome} ~ {' + '.join(predictors)} + {time_col}"
    grouping = subject_col
    
    try:
        model = mixedlm(formula, df, groups=df[grouping])
        result = model.fit(reml=False)
        
        return {
            "success": True,
            "coefficients": result.params.to_dict(),
            "p_values": result.pvalues.to_dict(),
            "conf_int": result.conf_int().to_dict(),
            "log_likelihood": result.llf,
            "aic": result.aic,
            "bic": result.bic,
            "converged": result.converged
        }
    except Exception as e:
        logger.warning(f"Model fitting failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "converged": False
        }

def run_statistical_analysis(
    data_dir: Path,
    output_dir: Path,
    outcome_col: str = "cognitive_score",
    predictor_cols: List[str] = None
) -> Dict[str, Any]:
    """Run the full statistical analysis pipeline."""
    if predictor_cols is None:
        predictor_cols = ["global_efficiency", "modularity"]
    
    logger.info(f"Loading data from {data_dir}")
    df = load_preprocessed_data(data_dir)
    
    # Handle collinearity
    collinearity_report = check_and_handle_collinearity(df, predictor_cols)
    
    if collinearity_report.get("pca_applied", False):
        logger.info("PCA applied to predictors. Using PCA components.")
        predictor_cols = collinearity_report.get("pca_columns", predictor_cols)
    
    # Fit model
    model_results = fit_linear_mixed_effects_model(
        df, 
        outcome_col, 
        predictor_cols,
        subject_col="subject_id",
        time_col="time_point"
    )
    
    # Prepare final output
    output = {
        "model_results": model_results,
        "collinearity_report": collinearity_report,
        "sample_size": len(df),
        "is_synthetic": is_synthetic(),
        "methodology_validation_mode": is_methodology_validation_mode(),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    # Save results
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "model_results.json"
    
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    
    logger.info(f"Results saved to {output_path}")
    return output

def main():
    """Main entry point for statistical model analysis."""
    logging.basicConfig(level=logging.INFO)
    
    data_dir = Path("data/processed")
    output_dir = Path("data/results")
    
    try:
        results = run_statistical_analysis(data_dir, output_dir)
        print(json.dumps(results, indent=2, default=str))
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
