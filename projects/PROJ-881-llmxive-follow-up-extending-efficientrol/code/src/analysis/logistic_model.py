import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Assuming these exist in validators as per API surface
try:
    from src.utils.validators import EntropyProfile
except ImportError:
    # Fallback for standalone execution if imports differ
    EntropyProfile = None

logger = logging.getLogger(__name__)


class GLMMAnalysisResult:
    """Container for logistic regression analysis results."""
    def __init__(
        self,
        model: Any,
        summary: str,
        auc_roc: float,
        p_values: Dict[str, float],
        coefficients: Dict[str, float],
        significant: bool,
        stratification: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        self.model = model
        self.summary = summary
        self.auc_roc = auc_roc
        self.p_values = p_values
        self.coefficients = coefficients
        self.significant = significant
        self.stratification = stratification
        self.error_message = error_message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "auc_roc": self.auc_roc,
            "p_values": self.p_values,
            "coefficients": self.coefficients,
            "significant": self.significant,
            "stratification": self.stratification,
            "error_message": self.error_message
        }


def load_entropy_profiles_for_analysis(data_path: Path) -> pd.DataFrame:
    """
    Load entropy profiles from JSONL into a DataFrame suitable for analysis.
    Flattens layer-wise entropy into a long format for regression.
    """
    records = []
    if not data_path.exists():
        raise FileNotFoundError(f"Data path not found: {data_path}")

    with open(data_path, 'r') as f:
        for line_num, line in enumerate(f):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                prompt_id = data.get('prompt_id')
                validity = data.get('validity')
                layers = data.get('layers', [])

                if layers is None:
                    logger.warning(f"Skipping record {prompt_id}: layers is None")
                    continue

                for layer_data in layers:
                    layer_idx = layer_data.get('layer_index')
                    entropy_val = layer_data.get('entropy_value')

                    if entropy_val is None:
                        logger.warning(f"Skipping layer {layer_idx} for {prompt_id}: entropy_value is None")
                        continue

                    records.append({
                        'prompt_id': prompt_id,
                        'layer_index': layer_idx,
                        'entropy': entropy_val,
                        'validity': validity,
                        'task_type': data.get('task_type', 'unknown')
                    })
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON at line {line_num}")
                continue

    if not records:
        raise ValueError("No valid records found in the dataset.")

    return pd.DataFrame(records)


def calculate_auc_roc(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate AUC-ROC using a simple implementation or sklearn if available."""
    try:
        from sklearn.metrics import roc_auc_score
        return roc_auc_score(y_true, y_pred)
    except ImportError:
        # Fallback simple implementation if sklearn is missing
        # Sort by predicted probability
        sorted_indices = np.argsort(y_pred)[::-1]
        y_true_sorted = y_true[sorted_indices]
        
        n_pos = np.sum(y_true == 1)
        n_neg = np.sum(y_true == 0)
        
        if n_pos == 0 or n_neg == 0:
            return 0.5
        
        # Calculate AUC using trapezoidal rule on ROC curve points
        tpr_list = []
        fpr_list = []
        tp = 0
        fp = 0
        
        for i in range(len(y_true_sorted)):
            if y_true_sorted[i] == 1:
                tp += 1
            else:
                fp += 1
            tpr_list.append(tp / n_pos)
            fpr_list.append(fp / n_neg)
        
        # Sort FPR and calculate AUC
        auc = 0.0
        for i in range(1, len(fpr_list)):
            auc += (fpr_list[i] - fpr_list[i-1]) * (tpr_list[i] + tpr_list[i-1]) / 2
        
        return auc


def fit_mixed_effects_model(df: pd.DataFrame, stratification: Optional[str] = None) -> GLMMAnalysisResult:
    """
    Fits a standard logistic regression model (GLMM deferred).
    Handles cases where p >= 0.05 by logging a warning and marking significant=False.
    """
    logger.info(f"Fitting logistic regression with stratification: {stratification}")
    
    # Check for perfect separation or empty classes
    unique_validity = df['validity'].unique()
    if len(unique_validity) < 2:
        logger.warning("Dataset contains only one class for validity. Skipping regression fit.")
        return GLMMAnalysisResult(
            model=None,
            summary="Skipped: Single class in target",
            auc_roc=0.5,
            p_values={},
            coefficients={},
            significant=False,
            stratification=stratification,
            error_message="Perfect separation: only one class present"
        )

    # Prepare features
    X = df[['entropy']].values
    y = df['validity'].values

    # Add constant for intercept
    X_with_const = sm.add_constant(X)

    try:
        # Fit Logistic Regression
        model = sm.Logit(y, X_with_const)
        result = model.fit(disp=0)  # disp=0 to suppress convergence warnings in output

        # Extract p-values
        p_values = {
            'intercept': float(result.pvalues[0]),
            'entropy': float(result.pvalues[1])
        }

        # Extract coefficients
        coefficients = {
            'intercept': float(result.params[0]),
            'entropy': float(result.params[1])
        }

        # Calculate AUC
        y_pred = result.predict(X_with_const)
        auc = calculate_auc_roc(y, y_pred)

        # Check significance (T030 requirement)
        entropy_p_value = p_values.get('entropy', 1.0)
        
        if entropy_p_value >= 0.05:
            logger.warning(
                f"P-value for entropy ({entropy_p_value:.4f}) >= 0.05. "
                "Result marked as not significant."
            )
            significant = False
        else:
            significant = True

        return GLMMAnalysisResult(
            model=result,
            summary=result.summary2.as_text() if hasattr(result, 'summary2') else str(result.summary()),
            auc_roc=auc,
            p_values=p_values,
            coefficients=coefficients,
            significant=significant,
            stratification=stratification
        )

    except Exception as e:
        logger.error(f"Error fitting logistic regression: {str(e)}")
        return GLMMAnalysisResult(
            model=None,
            summary=str(e),
            auc_roc=0.0,
            p_values={},
            coefficients={},
            significant=False,
            stratification=stratification,
            error_message=str(e)
        )


def stratified_analysis(data_path: Path, stratify_by: str = 'task_type') -> Dict[str, GLMMAnalysisResult]:
    """
    Perform stratified analysis (e.g., by task_type: GSM8K vs MiniGrid).
    Returns a dictionary of results per stratum.
    """
    df = load_entropy_profiles_for_analysis(data_path)
    
    if stratify_by not in df.columns:
        logger.warning(f"Stratification column '{stratify_by}' not found. Running unstratified.")
        return {"all": fit_mixed_effects_model(df)}

    results = {}
    for group, group_df in df.groupby(stratify_by):
        logger.info(f"Processing group: {group}")
        result = fit_mixed_effects_model(group_df, stratification=group)
        results[str(group)] = result
    
    return results


def analyze_entropy_validity_relationship(data_path: Path) -> Dict[str, Any]:
    """
    Main analysis function that orchestrates loading, stratifying, and fitting.
    Returns a summary dictionary suitable for reporting.
    """
    logger.info(f"Starting analysis on {data_path}")
    
    results = stratified_analysis(data_path)
    
    summary = {
        "groups": {},
        "overall_stats": {}
    }
    
    all_p_values = []
    all_auc = []
    
    for group_name, result in results.items():
        summary["groups"][group_name] = {
            "significant": result.significant,
            "auc_roc": result.auc_roc,
            "p_value_entropy": result.p_values.get('entropy', None),
            "coefficients": result.coefficients
        }
        
        if result.p_values.get('entropy') is not None:
            all_p_values.append(result.p_values['entropy'])
        if result.auc_roc > 0:
            all_auc.append(result.auc_roc)
    
    if all_p_values:
        summary["overall_stats"]["min_p_value"] = min(all_p_values)
        summary["overall_stats"]["avg_auc_roc"] = np.mean(all_auc)
    
    return summary


def main():
    """Entry point for script execution."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/logistic_model_analysis.log')
        ]
    )
    
    # Default paths, can be overridden by args in a real CLI
    data_path = Path("data/entropy_profiles_merged.jsonl")
    
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        sys.exit(1)
        
    try:
        results = analyze_entropy_validity_relationship(data_path)
        output_path = Path("results/logistic_analysis_results.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Analysis complete. Results written to {output_path}")
    except Exception as e:
        logger.critical(f"Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()