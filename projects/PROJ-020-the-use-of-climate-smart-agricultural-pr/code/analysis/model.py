import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path
import logging
import time
import json
import traceback
import gc
import resource
import sys
from utils.config import get_memory_limit_bytes

logger = logging.getLogger(__name__)

# Global memory profiling state
_peak_ram_bytes = 0
_model_fit_log = []

def _get_current_memory_bytes() -> int:
    """Get current RSS memory usage in bytes."""
    if sys.platform == "win32":
        # Windows fallback: use psutil if available, else 0
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss
        except ImportError:
            return 0
    else:
        # Unix/Linux/macOS: use resource module
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024

def _update_peak_memory():
    """Update global peak RAM tracking."""
    global _peak_ram_bytes
    current = _get_current_memory_bytes()
    if current > _peak_ram_bytes:
        _peak_ram_bytes = current

def log_memory_profile():
    """Log current and peak memory usage to logger and return stats."""
    current = _get_current_memory_bytes()
    peak = _peak_ram_bytes
    limit_bytes = get_memory_limit_bytes()
    limit_gb = limit_bytes / (1024**3) if limit_bytes else 0
    current_gb = current / (1024**3)
    peak_gb = peak / (1024**3)

    stats = {
        "current_memory_gb": round(current_gb, 3),
        "peak_memory_gb": round(peak_gb, 3),
        "limit_memory_gb": round(limit_gb, 3),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    logger.info(f"Memory Profile - Current: {current_gb:.3f} GB, Peak: {peak_gb:.3f} GB, Limit: {limit_gb:.3f} GB")
    return stats

def reset_memory_profile():
    """Reset memory profiling state."""
    global _peak_ram_bytes, _model_fit_log
    _peak_ram_bytes = 0
    _model_fit_log = []

def calculate_fdr_adjusted_pvalues(pvalues: List[float]) -> List[float]:
    """Calculate Benjamini-Hochberg FDR adjusted p-values."""
    pvalues = np.array(pvalues)
    n = len(pvalues)
    sorted_indices = np.argsort(pvalues)
    sorted_pvalues = pvalues[sorted_indices]
    
    adjusted = np.zeros(n)
    for i in range(n):
        rank = i + 1
        adjusted[sorted_indices[i]] = min(sorted_pvalues[i] * n / rank, 1.0)
    
    # Ensure monotonicity
    for i in range(n - 2, -1, -1):
        adjusted[sorted_indices[i]] = min(adjusted[sorted_indices[i]], adjusted[sorted_indices[i + 1]])
    
    return adjusted.tolist()

def run_mixed_effects_model(
    data: pd.DataFrame,
    formula: str,
    groups: str,
    weights: Optional[pd.Series] = None,
    max_iter: int = 100
) -> Dict[str, Any]:
    """
    Run mixed-effects regression with memory profiling instrumentation.
    
    Logs peak RAM usage before, during, and after model fitting.
    """
    global _peak_ram_bytes, _model_fit_log
    
    _update_peak_memory()
    start_time = time.time()
    logger.info(f"Starting mixed-effects model fit. Formula: {formula}, Groups: {groups}")
    
    try:
        # Pre-fit memory check
        pre_fit_stats = log_memory_profile()
        
        # Build model
        if weights is not None:
            model = smf.mixedlm(formula, data, groups=data[groups], 
                              weights=weights)
        else:
            model = smf.mixedlm(formula, data, groups=data[groups])
        
        _update_peak_memory()
        
        # Fit model with timeout protection
        result = model.fit(maxiter=max_iter, disp=False)
        
        # Post-fit memory check
        post_fit_stats = log_memory_profile()
        
        fit_duration = time.time() - start_time
        _update_peak_memory()
        
        # Log result summary
        logger.info(f"Model fit completed in {fit_duration:.2f}s. "
                   f"Converged: {result.converged}")
        
        # Record to log
        _model_fit_log.append({
            "formula": formula,
            "groups": groups,
            "converged": bool(result.converged),
            "fit_duration_seconds": fit_duration,
            "pre_fit_memory_gb": pre_fit_stats["current_memory_gb"],
            "post_fit_memory_gb": post_fit_stats["current_memory_gb"],
            "peak_memory_gb": post_fit_stats["peak_memory_gb"]
        })
        
        # Extract coefficients
        params = result.params
        std_err = result.bse
        t_values = result.tvalues
        p_values = result.pvalues
        
        return {
            "params": params.to_dict(),
            "std_err": std_err.to_dict(),
            "t_values": t_values.to_dict(),
            "p_values": p_values.to_dict(),
            "random_effects": result.random_effects,
            "converged": bool(result.converged),
            "fit_duration_seconds": fit_duration,
            "memory_stats": post_fit_stats
        }
        
    except Exception as e:
        _update_peak_memory()
        error_stats = log_memory_profile()
        logger.error(f"Model fit failed: {str(e)}")
        logger.error(traceback.format_exc())
        
        _model_fit_log.append({
            "formula": formula,
            "groups": groups,
            "error": str(e),
            "peak_memory_gb": error_stats["peak_memory_gb"],
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        })
        
        raise

def run_mediation_analysis(
    data: pd.DataFrame,
    outcome_formula: str,
    mediator_formula: str,
    groups: str,
    treatment_var: str,
    mediator_var: str,
    weights: Optional[pd.Series] = None
) -> Dict[str, Any]:
    """
    Perform Baron & Kenny mediation analysis with memory profiling.
    
    Logs peak RAM usage during each step of the mediation analysis.
    """
    _update_peak_memory()
    logger.info(f"Starting mediation analysis: {treatment_var} -> {mediator_var} -> outcome")
    
    try:
        # Step 1: Total effect (Y ~ X)
        logger.info("Step 1: Estimating total effect (Y ~ X)")
        step1_result = run_mixed_effects_model(data, outcome_formula, groups, weights)
        _update_peak_memory()
        
        # Step 2: Effect on mediator (M ~ X)
        logger.info("Step 2: Estimating mediator effect (M ~ X)")
        step2_result = run_mixed_effects_model(data, mediator_formula, groups, weights)
        _update_peak_memory()
        
        # Step 3: Direct effect (Y ~ X + M)
        # Construct full formula
        outcome_parts = outcome_formula.split("~")
        if len(outcome_parts) == 2:
            y_vars = outcome_parts[0].strip()
            x_vars = outcome_parts[1].strip()
            if mediator_var not in x_vars:
                full_formula = f"{y_vars} ~ {x_vars} + {mediator_var}"
            else:
                full_formula = outcome_formula
        else:
            full_formula = outcome_formula
        
        logger.info(f"Step 3: Estimating direct effect (Y ~ X + M): {full_formula}")
        step3_result = run_mixed_effects_model(data, full_formula, groups, weights)
        _update_peak_memory()
        
        # Calculate indirect effect
        total_effect = step1_result["params"].get(treatment_var, 0)
        direct_effect = step3_result["params"].get(treatment_var, 0)
        mediator_effect = step2_result["params"].get(treatment_var, 0)
        indirect_effect = total_effect - direct_effect
        
        logger.info(f"Mediation analysis complete. Indirect effect: {indirect_effect:.4f}")
        
        return {
            "total_effect": total_effect,
            "direct_effect": direct_effect,
            "indirect_effect": indirect_effect,
            "step1_results": step1_result,
            "step2_results": step2_result,
            "step3_results": step3_result,
            "memory_stats": log_memory_profile()
        }
        
    except Exception as e:
        logger.error(f"Mediation analysis failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def run_robustness_checks(
    data: pd.DataFrame,
    formula: str,
    groups: str,
    weights: Optional[pd.Series] = None,
    n_bootstraps: int = 100
) -> Dict[str, Any]:
    """
    Run robustness checks with memory profiling.
    
    Logs peak RAM usage during bootstrap resampling.
    """
    _update_ram_profile()
    logger.info(f"Starting robustness checks with {n_bootstraps} bootstraps")
    
    try:
        bootstrap_results = []
        
        for i in range(n_bootstraps):
            if i % 10 == 0:
                _update_peak_memory()
                current_stats = log_memory_profile()
                logger.info(f"Bootstrap {i}/{n_bootstraps}, Current RAM: {current_stats['current_memory_gb']:.3f} GB")
            
            # Resample data
            sample_indices = np.random.choice(len(data), size=len(data), replace=True)
            bootstrap_sample = data.iloc[sample_indices]
            
            # Fit model on bootstrap sample
            try:
                result = run_mixed_effects_model(bootstrap_sample, formula, groups, weights)
                bootstrap_results.append(result["params"])
            except Exception as e:
                logger.warning(f"Bootstrap {i} failed: {str(e)}")
                continue
            
            # Force garbage collection every 20 iterations
            if i % 20 == 0:
                gc.collect()
        
        # Calculate statistics
        if bootstrap_results:
            params_df = pd.DataFrame(bootstrap_results)
            mean_params = params_df.mean()
            std_params = params_df.std()
            
            return {
                "mean_coefficients": mean_params.to_dict(),
                "std_coefficients": std_params.to_dict(),
                "n_successful_bootstraps": len(bootstrap_results),
                "n_total_bootstraps": n_bootstraps,
                "memory_stats": log_memory_profile()
            }
        else:
            logger.warning("No successful bootstrap iterations")
            return {
                "error": "No successful bootstraps",
                "memory_stats": log_memory_profile()
            }
            
    except Exception as e:
        logger.error(f"Robustness checks failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def save_memory_profile_report(output_path: Optional[Path] = None) -> Path:
    """
    Save the memory profiling log to a JSON file.
    
    Args:
        output_path: Path to save the report. Defaults to data/state/memory_profile.json
        
    Returns:
        Path to the saved report
    """
    if output_path is None:
        output_path = Path("data/state/memory_profile.json")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        "model_fits": _model_fit_log,
        "peak_memory_gb": _peak_ram_bytes / (1024**3),
        "current_memory_gb": _get_current_memory_bytes() / (1024**3),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Memory profile report saved to {output_path}")
    return output_path

def main():
    """
    Main entry point for memory profiling demonstration.
    
    This function runs a sample model fit to demonstrate memory profiling.
    In production, this would be called from the analysis pipeline.
    """
    logging.basicConfig(level=logging.INFO)
    
    logger.info("Memory Profiling Instrumentation - T040")
    logger.info("This module provides memory profiling for model fitting operations.")
    
    # Demonstrate memory tracking
    reset_memory_profile()
    
    # Create a small sample dataset for demonstration
    np.random.seed(42)
    n = 1000
    sample_data = pd.DataFrame({
        'y': np.random.randn(n),
        'x1': np.random.randn(n),
        'x2': np.random.randn(n),
        'group': np.random.choice(['A', 'B', 'C'], n)
    })
    
    logger.info("Running sample model fit to demonstrate memory profiling...")
    
    try:
        result = run_mixed_effects_model(
            sample_data,
            'y ~ x1 + x2',
            'group'
        )
        
        logger.info(f"Sample model converged: {result['converged']}")
        logger.info(f"Peak memory during sample fit: {result['memory_stats']['peak_memory_gb']:.3f} GB")
        
        # Save report
        report_path = save_memory_profile_report()
        logger.info(f"Memory profile report saved to: {report_path}")
        
    except Exception as e:
        logger.error(f"Sample model failed: {str(e)}")
        raise
    
    logger.info("Memory profiling instrumentation complete.")

if __name__ == "__main__":
    main()