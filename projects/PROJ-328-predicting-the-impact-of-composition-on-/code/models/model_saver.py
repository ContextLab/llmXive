"""
Model Saver Module for T031.
Saves model artifacts, metrics, and diagnostics to models/ and data/processed/.
Ensures FR-007 associational framing warnings are included in all outputs.
"""
import os
import sys
import json
import pickle
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import get_models_dir, get_data_processed_dir, get_data_outputs_dir
from utils.logging_config import get_logger

logger = get_logger(__name__)

def save_model(model: Any, model_name: str, output_dir: Optional[Path] = None) -> Path:
    """Save a trained model to disk using pickle."""
    if output_dir is None:
        output_dir = get_models_dir()
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = output_dir / f"{model_name}.pkl"
    
    try:
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        logger.info(f"Model saved to {model_path}")
        return model_path
    except Exception as e:
        logger.error(f"Failed to save model {model_name}: {e}")
        raise

def save_metrics(metrics: Dict[str, Any], model_name: str, output_dir: Optional[Path] = None) -> Path:
    """Save model metrics to YAML with associational framing warning."""
    if output_dir is None:
        output_dir = get_data_processed_dir()
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    metrics_path = output_dir / f"{model_name}_metrics.yaml"
    
    # Ensure FR-007 associational framing is present
    if 'associational_framing_warning' not in metrics:
        metrics['associational_framing_warning'] = (
            "Findings are associational, not causal. "
            "The data is observational; correlations do not imply causation."
        )
    
    try:
        with open(metrics_path, 'w') as f:
            yaml.dump(metrics, f, default_flow_style=False)
        logger.info(f"Metrics saved to {metrics_path}")
        return metrics_path
    except Exception as e:
        logger.error(f"Failed to save metrics for {model_name}: {e}")
        raise

def save_vif_results(vif_results: List[Dict[str, Any]], output_dir: Optional[Path] = None) -> Path:
    """Save VIF analysis results to YAML."""
    if output_dir is None:
        output_dir = get_data_processed_dir()
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    vif_path = output_dir / "vif_report.yaml"
    
    try:
        with open(vif_path, 'w') as f:
            yaml.dump(vif_results, f, default_flow_style=False)
        logger.info(f"VIF results saved to {vif_path}")
        return vif_path
    except Exception as e:
        logger.error(f"Failed to save VIF results: {e}")
        raise

def save_shap_summary(shap_summary: Dict[str, Any], output_dir: Optional[Path] = None) -> Path:
    """Save SHAP analysis summary to YAML."""
    if output_dir is None:
        output_dir = get_data_processed_dir()
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    shap_path = output_dir / "shap_ranking.yaml"
    
    try:
        with open(shap_path, 'w') as f:
            yaml.dump(shap_summary, f, default_flow_style=False)
        logger.info(f"SHAP summary saved to {shap_path}")
        return shap_path
    except Exception as e:
        logger.error(f"Failed to save SHAP summary: {e}")
        raise

def save_comparison_report(comparison_report: Dict[str, Any], output_dir: Optional[Path] = None) -> Path:
    """Save model comparison report to YAML with associational framing warning."""
    if output_dir is None:
        output_dir = get_data_processed_dir()
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    report_path = output_dir / "model_comparison_report.yaml"
    
    # Ensure FR-007 associational framing is present
    if 'associational_framing_warning' not in comparison_report:
        comparison_report['associational_framing_warning'] = (
            "Findings are associational, not causal. "
            "The comparison is based on observational data and does not imply causal superiority."
        )
    
    try:
        with open(report_path, 'w') as f:
            yaml.dump(comparison_report, f, default_flow_style=False)
        logger.info(f"Comparison report saved to {report_path}")
        return report_path
    except Exception as e:
        logger.error(f"Failed to save comparison report: {e}")
        raise

def save_all_artifacts(
    xgboost_model: Any,
    linear_model: Any,
    xgboost_metrics: Dict[str, Any],
    linear_metrics: Dict[str, Any],
    vif_results: List[Dict[str, Any]],
    shap_summary: Dict[str, Any],
    comparison_report: Dict[str, Any]
) -> Dict[str, Path]:
    """Save all model artifacts, metrics, and diagnostics in one call."""
    results = {}
    
    # Save models
    results['xgboost_model'] = save_model(xgboost_model, 'xgboost_model')
    results['linear_model'] = save_model(linear_model, 'linear_model')
    
    # Save metrics with FR-007 warnings
    results['xgboost_metrics'] = save_metrics(xgboost_metrics, 'xgboost_metrics')
    results['linear_metrics'] = save_metrics(linear_metrics, 'linear_metrics')
    
    # Save diagnostics
    results['vif_report'] = save_vif_results(vif_results)
    results['shap_ranking'] = save_shap_summary(shap_summary)
    results['comparison_report'] = save_comparison_report(comparison_report)
    
    logger.info("All model artifacts saved successfully.")
    return results

def main():
    """Main entry point for T031 - Model Saver."""
    logger.info("Starting T031: Save model artifacts, metrics, and diagnostics")
    
    # This function is typically called by the pipeline after training and evaluation.
    # It expects the caller to provide the trained models and computed metrics.
    # For testing purposes, we verify the directories exist.
    
    models_dir = get_models_dir()
    processed_dir = get_data_processed_dir()
    
    logger.info(f"Models directory: {models_dir}")
    logger.info(f"Processed data directory: {processed_dir}")
    
    # Ensure directories exist
    models_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("T031 completed successfully - directories ready for artifact saving.")

if __name__ == "__main__":
    main()
