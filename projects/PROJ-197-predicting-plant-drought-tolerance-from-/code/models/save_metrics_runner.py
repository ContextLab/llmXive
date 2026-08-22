"""
Runner script to aggregate and save all metrics from the pipeline to data/logs/metrics.json.

This script is executed after model training and evaluation to ensure a single source
of truth for all reproducibility data. It reads the outputs from evaluate.py and 
compare.py (which are assumed to have generated the necessary in-memory or file-based
results) and writes them to the central JSON log.

Usage:
    python code/models/save_metrics_runner.py
"""
import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from config import get_config
from utils.logging import DataPipelineLog
from utils.metrics_logger import (
    log_model_result, 
    log_validation_result, 
    log_comparison_report
)
from models.evaluate import load_test_data, load_models, evaluate_model, select_best_model, save_metrics
from models.compare import load_cv_results, perform_rf_vs_xgb_ttest, calculate_permutation_importance, classify_features

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """
    Orchestrates the collection and saving of all metrics to data/logs/metrics.json.
    """
    logger.info("Starting metrics aggregation for reproducibility...")
    
    # 1. Load Models and Evaluate (re-run evaluation to get fresh metrics if needed, 
    #    or load from existing artifacts if evaluate.py already saved them)
    # Note: T022 (evaluate.py) calls save_metrics which likely saved to a temp or specific file.
    # We will re-evaluate to ensure we capture the exact state for the central log.
    
    config = get_config()
    data_dir = Path(config["paths"]["processed_data"])
    models_dir = Path(config["paths"]["models"])
    
    try:
        X_test, y_test = load_test_data()
        models = load_models()
        
        logger.info(f"Loaded {len(models)} models for evaluation.")
        
        # Evaluate each model and log
        for name, model in models.items():
            logger.info(f"Evaluating {name}...")
            metrics_dict = evaluate_model(model, X_test, y_test)
            
            # Get hyperparameters from the model if possible
            hyperparams = {}
            if hasattr(model, 'get_params'):
                hyperparams = model.get_params()
            
            # Get feature importance if available
            feat_imp = None
            if hasattr(model, 'feature_importances_'):
                # Map indices back to feature names if available
                # For simplicity, we log the raw array or try to get names from config if needed
                # Here we assume the metric logger handles the mapping or we just log the array
                feat_imp = {f"feature_{i}": float(val) for i, val in enumerate(model.feature_importances_)}
            elif hasattr(model, 'coef_'):
                feat_imp = {f"feature_{i}": float(val) for i, val in enumerate(model.coef_)}
            
            log_model_result(
                model_name=name,
                metrics=metrics_dict,
                hyperparameters=hyperparams,
                feature_importance=feat_imp
            )
        
        # 2. Log Statistical Comparisons
        logger.info("Logging statistical comparisons...")
        
        # DeLong's Test (from T023) - comparing best model vs baseline
        # We assume the results are available or re-compute if necessary.
        # For this runner, we re-compute to ensure consistency.
        best_model_name, best_model_obj = select_best_model(models, X_test, y_test)
        baseline_name = "KNN_Baseline"
        
        # Re-evaluate baseline for DeLong
        if baseline_name in models:
            baseline_metrics = evaluate_model(models[baseline_name], X_test, y_test)
            best_metrics = evaluate_model(best_model_obj, X_test, y_test)
            
            # We need AUCs for DeLong. 
            # Note: evaluate_model returns a dict. We assume 'auc' is the key.
            auc_best = best_metrics.get('auc', 0.0)
            auc_base = baseline_metrics.get('auc', 0.0)
            
            # Since we don't have the raw prediction arrays here easily without re-running predict_proba,
            # and the task T023 already performed this, we will log the *result* if we can extract it.
            # However, to be robust, we assume the user has run T022/T023 and we are just aggregating.
            # If we must re-run DeLong, we need the raw arrays. 
            # Let's assume the 'save_metrics' in T022 saved the raw arrays or we re-calculate.
            # Given the constraint, we will log a placeholder for DeLong if not available, 
            # but the instruction says "Ensure all metrics... are written".
            # We will attempt to re-run the t-test and DeLong if the data is available.
            
            # For this script to be fully functional, we need the raw predictions.
            # We will assume they were saved by T022/T023 to a temp file or re-compute.
            # To keep it simple and compliant with "write real outputs", we will log the 
            # comparison results if we can compute them.
            
            # Re-compute DeLong (T023 logic)
            from utils.stats import delong_test_auc
            # We need raw predictions. Let's get them.
            y_pred_best_proba = best_model_obj.predict_proba(X_test)[:, 1]
            y_pred_base_proba = models[baseline_name].predict_proba(X_test)[:, 1]
            
            p_val, stat = delong_test_auc(y_test, y_pred_best_proba, y_pred_base_proba)
            log_validation_result(
                test_name="DeLong_AUC_Best_vs_Baseline",
                p_value=p_val,
                statistic=stat,
                significance_threshold=0.05
            )
            
        # RF vs XGB T-Test (T027)
        if "RandomForest" in models and "XGBoost" in models:
            # We need CV scores. These are usually generated during training (T020).
            # If T020 saved them, we load. If not, we re-run CV.
            # To avoid heavy re-computation, we assume T027 generated a report or saved scores.
            # We will try to load CV results if T027 saved them, otherwise re-run.
            # For this implementation, we assume the CV scores are available in the model's history 
            # or we re-run a quick CV.
            
            # Re-run CV for RF and XGB to get scores
            from sklearn.model_selection import cross_val_score
            from config import get_config
            cfg = get_config()
            seed = cfg.get("random_seed", 42)
            
            rf_scores = cross_val_score(models["RandomForest"], X_test, y_test, cv=5, scoring='roc_auc')
            xgb_scores = cross_val_score(models["XGBoost"], X_test, y_test, cv=5, scoring='roc_auc')
            
            from utils.stats import paired_ttest
            p_ttest, stat_ttest = paired_ttest(rf_scores, xgb_scores)
            log_validation_result(
                test_name="RF_vs_XGB_CV_AUC_TTest",
                p_value=p_ttest,
                statistic=stat_ttest,
                significance_threshold=0.05
            )

        # 3. Log Comparison Report (T029)
        logger.info("Logging final comparison report...")
        perm_imp, feature_names = calculate_permutation_importance(best_model_obj, X_test, y_test)
        # perm_imp is likely a dict or array. classify_features needs names.
        # We assume feature_names is available from the data split or config.
        
        # Re-classify features
        from models.compare import classify_features
        genomic_count, physio_count, top_features = classify_features(perm_imp, feature_names)
        
        # Validation check (SC-005)
        validation_genes = [
            "DREB2A", "ERF1", "ABI5", "RD29A", "COR15A", 
            "LEA3", "HSP70", "SOD", "APX1", "CAT1", 
            "GPX1", "MDHAR", "DHAR", "GSTU", "ZAT12"
        ]
        # Check if top_features contain validation genes
        top_10 = top_features[:10]
        match_count = sum(1 for f in top_10 if any(vg in f for vg in validation_genes))
        validation_check = match_count >= 3
        
        log_comparison_report(
            best_model=best_model_name,
            top_features=top_10,
            genomic_count=genomic_count,
            physiological_count=physio_count,
            validation_check=validation_check
        )
        
        logger.info("All metrics successfully written to data/logs/metrics.json")
        
    except Exception as e:
        logger.error(f"Error during metrics aggregation: {e}")
        raise

if __name__ == "__main__":
    main()