import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple

# Configure logger for this module
def setup_logger(name: str, log_file: str, level=logging.INFO) -> logging.Logger:
    """Setup a logger that writes to both file and console."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create file handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(level)

    # Create console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # Add handlers to the logger
    if not logger.handlers:
        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger

def load_predictions(input_path: str, logger: logging.Logger) -> pd.DataFrame:
    """
    Load the aggregated UQ predictions file.
    Expects columns: sample_id, method, prediction, variance, lower_50, upper_50, lower_90, upper_90, aleatoric, epistemic, total, uncertainty_type
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading predictions from {input_path}")
    df = pd.read_csv(input_path)
    
    # Validate essential columns exist
    required_cols = ['sample_id', 'method', 'prediction', 'variance', 'aleatoric', 'epistemic', 'uncertainty_type']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {input_path}: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} rows. Methods found: {df['method'].unique().tolist()}")
    return df

def validate_decomposition(df: pd.DataFrame, logger: logging.Logger) -> Dict[str, Any]:
    """
    Validate the aleatoric/epistemic decomposition logic.
    
    Checks:
    1. Epistemic variance is non-negative for Deep Ensemble and MC Dropout.
    2. Epistemic variance is consistent with model variance (correlation > 0.9) for Deep Ensemble.
    3. Sparse GP has null aleatoric/epistemic and 'total' uncertainty type.
    
    Returns a summary dictionary of validation results.
    """
    results = {
        "total_rows": len(df),
        "checks": {},
        "passed": True,
        "details": []
    }

    methods = df['method'].unique()
    logger.info(f"Validating decomposition for methods: {methods}")

    # 1. Check for non-negative epistemic variance in Deep Ensemble and MC Dropout
    ensemble_methods = ['deep_ensemble', 'mc_dropout']
    for method in ensemble_methods:
        if method in methods:
            subset = df[df['method'] == method]
            # Handle numeric conversion for potentially null values (though they shouldn't be for these methods)
            epistemic_vals = pd.to_numeric(subset['epistemic'], errors='coerce')
            
            # Check non-negative
            negative_count = (epistemic_vals < 0).sum()
            if negative_count > 0:
                msg = f"FAIL: {method} has {negative_count} negative epistemic variance values."
                results["checks"][f"{method}_non_negative"] = False
                results["details"].append(msg)
                results["passed"] = False
                logger.error(msg)
            else:
                msg = f"PASS: {method} epistemic variance is non-negative."
                results["checks"][f"{method}_non_negative"] = True
                results["details"].append(msg)
                logger.info(msg)

    # 2. Check consistency (correlation > 0.9) for Deep Ensemble
    # Epistemic variance is the variance of predictions across ensemble members.
    # Total variance is the mean of predicted variances (aleatoric) + variance of means (epistemic).
    # The task specifically asks to validate that epistemic variance is consistent with model variance.
    # In the decomposition logic:
    #   Epistemic = Variance(E[pred | model]) -> Variance of the means
    #   Aleatoric = E[Var(p | model)] -> Mean of the variances
    #   Total = Epistemic + Aleatoric
    # We check if Epistemic correlates strongly with the spread of predictions.
    # Since we only have the aggregated stats here, we verify that Epistemic is derived correctly
    # by checking if Epistemic > 0 implies significant variation in the underlying ensemble (if we had raw ensemble data).
    # However, with only the summary stats, we check the relationship: Total - Aleatoric == Epistemic.
    # And we check if Epistemic correlates with the 'variance' column (which is Total variance in the summary).
    
    if 'deep_ensemble' in methods:
        de_df = df[df['method'] == 'deep_ensemble'].copy()
        de_df['aleatoric_num'] = pd.to_numeric(de_df['aleatoric'], errors='coerce').fillna(0)
        de_df['epistemic_num'] = pd.to_numeric(de_df['epistemic'], errors='coerce').fillna(0)
        de_df['total_num'] = pd.to_numeric(de_df['total'], errors='coerce').fillna(0)
        
        # Check 2a: Arithmetic consistency (Total approx Aleatoric + Epistemic)
        # Allow small float tolerance
        de_df['sum_check'] = de_df['aleatoric_num'] + de_df['epistemic_num']
        diff = np.abs(de_df['total_num'] - de_df['sum_check'])
        consistent_count = (diff < 1e-6).sum()
        
        if consistent_count == len(de_df):
            msg = "PASS: Deep Ensemble Total = Aleatoric + Epistemic (arithmetic consistency)."
            results["checks"]["de_arithmetic_consistency"] = True
            logger.info(msg)
        else:
            msg = f"FAIL: Deep Ensemble arithmetic consistency failed for {len(de_df) - consistent_count} rows."
            results["checks"]["de_arithmetic_consistency"] = False
            results["passed"] = False
            logger.error(msg)

        # Check 2b: Correlation between Epistemic and Total Variance
        # If Epistemic is a significant component, it should correlate with Total if Aleatoric is relatively stable or smaller.
        # More importantly, we check if Epistemic is non-zero where expected.
        # The requirement "consistent with model variance (correlation > 0.9)" implies that the calculated epistemic
        # should track with the variance of the ensemble predictions.
        # Since we don't have raw ensemble predictions here, we check the correlation between Epistemic and the 'variance' column
        # (which represents total uncertainty). If the decomposition is correct, they should be related.
        # However, a stricter interpretation: Epistemic IS the variance of the means.
        # Let's check correlation between Epistemic and (Total - Aleatoric) which is exactly Epistemic.
        # Instead, let's check if Epistemic correlates with the spread of the 'prediction' values? No, that's mean.
        
        # Re-reading requirement: "validating that ... epistemic variance is ... consistent with model variance (correlation > 0.9)"
        # This likely refers to the fact that Epistemic Variance = Var(E[y|x, model]).
        # In the aggregated file, 'variance' is the total variance.
        # If the model has high epistemic uncertainty, the total variance should be high.
        # Let's calculate correlation between Epistemic and Total Variance.
        # We drop rows where epistemic is 0 or NaN to avoid skew.
        valid_rows = de_df[(de_df['epistemic_num'] > 0) & (de_df['total_num'] > 0)]
        if len(valid_rows) > 10:
            corr = valid_rows['epistemic_num'].corr(valid_rows['total_num'])
            if corr > 0.9:
                msg = f"PASS: Deep Ensemble Epistemic vs Total Variance correlation = {corr:.4f} (> 0.9)."
                results["checks"]["de_correlation"] = True
                logger.info(msg)
            else:
                msg = f"FAIL: Deep Ensemble Epistemic vs Total Variance correlation = {corr:.4f} (<= 0.9)."
                results["checks"]["de_correlation"] = False
                results["passed"] = False
                logger.error(msg)
        else:
            msg = "WARN: Not enough valid rows to calculate correlation for Deep Ensemble."
            results["checks"]["de_correlation"] = "insufficient_data"
            logger.warning(msg)

    # 3. Check Sparse GP handling
    if 'sparse_gp' in methods:
        gp_df = df[df['method'] == 'sparse_gp']
        # Aleatoric and Epistemic should be null (or NaN in pandas)
        # Uncertainty type should be 'total'
        gp_aleatoric_null = gp_df['aleatoric'].isna().all() or (gp_df['aleatoric'].apply(lambda x: pd.isna(x) if isinstance(x, float) else False)).all()
        gp_epistemic_null = gp_df['epistemic'].isna().all() or (gp_df['epistemic'].apply(lambda x: pd.isna(x) if isinstance(x, float) else False)).all()
        gp_type_correct = (gp_df['uncertainty_type'] == 'total').all()
        
        if gp_aleatoric_null and gp_epistemic_null and gp_type_correct:
            msg = "PASS: Sparse GP correctly has null aleatoric/epistemic and 'total' type."
            results["checks"]["gp_handling"] = True
            logger.info(msg)
        else:
            msg = f"FAIL: Sparse GP handling incorrect. Aleatoric null: {gp_aleatoric_null}, Epistemic null: {gp_epistemic_null}, Type correct: {gp_type_correct}"
            results["checks"]["gp_handling"] = False
            results["passed"] = False
            logger.error(msg)

    return results

def main():
    """Main entry point for the UQ validation script."""
    # Setup logging
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "uq_validation.log"
    logger = setup_logger("validate_uq", str(log_file))
    
    logger.info("Starting UQ Decomposition Validation")
    
    # Input file path
    input_path = "results/uq_predictions_decomposed.csv"
    
    try:
        df = load_predictions(input_path, logger)
        results = validate_decomposition(df, logger)
        
        # Write summary to log and potentially a JSON file
        logger.info("Validation Summary:")
        for key, value in results["checks"].items():
            logger.info(f"  {key}: {value}")
        
        logger.info(f"Overall Result: {'PASSED' if results['passed'] else 'FAILED'}")
        
        # Save detailed results to JSON for programmatic access
        results_path = Path("results") / "uq_validation_summary.json"
        results_path.parent.mkdir(exist_ok=True)
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Validation summary saved to {results_path}")
        
        if not results["passed"]:
            logger.error("Validation FAILED. Please check the logs for details.")
            sys.exit(1)
        else:
            logger.info("Validation PASSED.")
            sys.exit(0)
            
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()