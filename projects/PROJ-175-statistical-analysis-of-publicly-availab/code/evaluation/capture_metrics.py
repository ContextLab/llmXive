import os
import sys
import json
from pathlib import Path
from data.split import load_subset_size

# Ensure project root is in path for imports if run as script
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def load_json_safe(filepath: str) -> dict:
    """Load a JSON file safely. Returns empty dict if file missing or invalid."""
    path = Path(filepath)
    if not path.exists():
        print(f"Warning: File not found: {filepath}")
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Warning: Invalid JSON in {filepath}: {e}")
        return {}

def extract_pipeline_metrics(log_path: str) -> dict:
    """Extract metrics from pipeline execution log."""
    data = load_json_safe(log_path)
    if not data:
        return {
            "pipeline_status": "MISSING",
            "runtime_seconds": 0.0,
            "peak_ram_mb": 0.0,
            "artifacts_created_count": 0
        }
    
    status = data.get('status', 'UNKNOWN')
    runtime = data.get('runtime_seconds', 0.0)
    peak_ram = data.get('peak_ram_mb', 0.0)
    artifacts = data.get('artifacts_created', [])
    
    return {
        "pipeline_status": status,
        "runtime_seconds": float(runtime),
        "peak_ram_mb": float(peak_ram),
        "artifacts_created_count": len(artifacts),
        "artifacts_list": artifacts
    }

def extract_logistic_metrics(log_path: str) -> dict:
    """Extract metrics from logistic model fitting log."""
    data = load_json_safe(log_path)
    if not data:
        return {
            "logistic_status": "MISSING",
            "convergence": False,
            "auc": 0.0,
            "coefficients_count": 0
        }
    
    return {
        "logistic_status": data.get('status', 'UNKNOWN'),
        "convergence": data.get('convergence', False),
        "auc": float(data.get('auc', 0.0)),
        "coefficients_count": len(data.get('coefficients', {})),
        "regularization_type": data.get('regularization', 'l2')
    }

def extract_bayesian_metrics(log_path: str) -> dict:
    """Extract metrics from Bayesian model fitting log."""
    data = load_json_safe(log_path)
    if not data:
        return {
            "bayesian_status": "MISSING",
            "convergence": False,
            "r_hat": 0.0,
            "ess": 0
        }
    
    return {
        "bayesian_status": data.get('status', 'UNKNOWN'),
        "convergence": data.get('convergence', False),
        "r_hat": float(data.get('r_hat', 0.0)),
        "ess": int(data.get('ess', 0)),
        "runtime_seconds": float(data.get('runtime_seconds', 0.0))
    }

def extract_vif_metrics(log_path: str) -> dict:
    """Extract VIF metrics from initial diagnostic log."""
    data = load_json_safe(log_path)
    if not data:
        return {
            "vif_status": "MISSING",
            "max_vif": 0.0,
            "dropped_predictors": []
        }
    
    predictors = data.get('predictors', {})
    max_vif = float(data.get('max_vif', 0.0))
    dropped = data.get('dropped', [])
    
    return {
        "vif_status": "COMPUTED",
        "max_vif": max_vif,
        "dropped_predictors": dropped,
        "predictor_count": len(predictors)
    }

def extract_auc_delta_metrics(log_path: str) -> dict:
    """Extract AUC delta metrics from evaluation log."""
    data = load_json_safe(log_path)
    if not data:
        return {
            "auc_full": 0.0,
            "auc_baseline": 0.0,
            "delta": 0.0,
            "p_value": 0.0,
            "ci_95": [0.0, 0.0],
            "test_method": "MISSING"
        }
    
    ci = data.get('ci_95', [0.0, 0.0])
    if not isinstance(ci, list) or len(ci) != 2:
        ci = [0.0, 0.0]
        
    return {
        "auc_full": float(data.get('auc_full', 0.0)),
        "auc_baseline": float(data.get('auc_baseline', 0.0)),
        "delta": float(data.get('delta', 0.0)),
        "p_value": float(data.get('p_value', 0.0)),
        "ci_95": [float(ci[0]), float(ci[1])],
        "test_method": data.get('test_method', 'UNKNOWN'),
        "threshold": float(data.get('threshold', 0.05))
    }

def extract_lrt_vif_corrected(log_path: str) -> dict:
    """Extract Likelihood Ratio Test results with VIF correction."""
    data = load_json_safe(log_path)
    if not data:
        return {
            "lrt_status": "MISSING",
            "p_value": 0.0,
            "chi2_statistic": 0.0,
            "multicollinearity_flag": False
        }
    
    return {
        "lrt_status": data.get('status', 'UNKNOWN'),
        "p_value": float(data.get('p_value', 0.0)),
        "chi2_statistic": float(data.get('chi2_statistic', 0.0)),
        "multicollinearity_flag": data.get('multicollinearity_flag', False),
        "df": int(data.get('df', 0))
    }

def extract_bayesian_convergence(log_path: str) -> dict:
    """Extract Bayesian convergence log status."""
    data = load_json_safe(log_path)
    if not data:
        return {
            "convergence_status": "MISSING",
            "r_hat": 0.0,
            "ess": 0
        }
    
    return {
        "convergence_status": data.get('status', 'UNKNOWN'),
        "r_hat": float(data.get('metrics', {}).get('R_hat', 0.0)),
        "ess": int(data.get('metrics', {}).get('ESS', 0))
    }

def extract_vif_test_set(log_path: str) -> dict:
    """Extract VIF metrics from test set check."""
    data = load_json_safe(log_path)
    if not data:
        return {
            "test_vif_status": "MISSING",
            "max_vif_test": 0.0,
            "unstable_flag": False
        }
    
    max_vif = float(data.get('max_vif', 0.0))
    return {
        "test_vif_status": "COMPUTED",
        "max_vif_test": max_vif,
        "unstable_flag": max_vif > 5.0
    }

def main():
    """Main entry point to capture all metrics into final_validation_report.json."""
    base_dir = Path(__file__).parent.parent.parent
    data_dir = base_dir / 'data'
    
    # Define input paths based on task dependencies
    pipeline_log = data_dir / 'pipeline_execution_log.json'
    model_fitting_log = data_dir / 'model_fitting_log.json'
    evaluation_log = data_dir / 'evaluation_log.json'
    vif_initial_log = data_dir / 'vif_scores_initial.json'
    auc_delta_log = data_dir / 'auc_delta_metrics.json'
    lrt_vif_corrected_log = data_dir / 'lrt_result_vif_corrected.json'
    bayesian_convergence_log = data_dir / 'bayesian_convergence_log.json'
    vif_test_set_log = data_dir / 'vif_scores_test_set.json'
    
    # Extract metrics
    pipeline_metrics = extract_pipeline_metrics(str(pipeline_log))
    
    # Parse model fitting log which contains both logistic and bayesian info
    model_fitting_data = load_json_safe(str(model_fitting_log))
    logistic_metrics = extract_logistic_metrics(str(model_fitting_log))
    bayesian_metrics = extract_bayesian_metrics(str(model_fitting_log))
    
    # Extract diagnostics
    vif_metrics = extract_vif_metrics(str(vif_initial_log))
    vif_test_metrics = extract_vif_test_set(str(vif_test_set_log))
    lrt_metrics = extract_lrt_vif_corrected(str(lrt_vif_corrected_log))
    
    # Extract evaluation
    auc_delta_metrics = extract_auc_delta_metrics(str(auc_delta_log))
    
    # Extract convergence
    bayesian_conv = extract_bayesian_convergence(str(bayesian_convergence_log))
    
    # Construct final report
    final_report = {
        "timestamp": json.dumps(__import__('datetime').datetime.now().isoformat()),
        "summary": {
            "pipeline_success": pipeline_metrics['pipeline_status'] == 'SUCCESS',
            "model_fitting_success": (
                logistic_metrics['logistic_status'] == 'SUCCESS' and 
                bayesian_metrics['bayesian_status'] == 'SUCCESS'
            ),
            "evaluation_success": auc_delta_metrics['test_method'] != 'MISSING',
            "overall_status": "PASS" if (
                pipeline_metrics['pipeline_status'] == 'SUCCESS' and
                logistic_metrics['logistic_status'] == 'SUCCESS' and
                bayesian_metrics['bayesian_status'] == 'SUCCESS'
            ) else "FAIL"
        },
        "pipeline": pipeline_metrics,
        "logistic_model": logistic_metrics,
        "bayesian_model": bayesian_metrics,
        "vif_analysis": {
            "initial": vif_metrics,
            "test_set": vif_test_metrics,
            "stability_check_passed": vif_test_metrics['max_vif_test'] <= 5.0
        },
        "likelihood_ratio_test": lrt_metrics,
        "auc_delta_analysis": auc_delta_metrics,
        "bayesian_convergence": bayesian_conv,
        "sample_size": load_subset_size()
    }
    
    # Write output
    output_path = data_dir / 'final_validation_report.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_report, f, indent=2)
    
    print(f"Final validation report generated: {output_path}")
    print(f"Overall Status: {final_report['summary']['overall_status']}")
    
    return final_report

if __name__ == '__main__':
    main()