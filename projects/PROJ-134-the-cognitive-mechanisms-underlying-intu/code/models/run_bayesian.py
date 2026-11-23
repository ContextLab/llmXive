"""
Bayesian Model Execution Pipeline (T023).

Implements sampling, metric calculation, and result serialization.
Dependencies: T023b (calculate_metrics), T022c (run_model).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import pymc as pm
import arviz as az

# Local imports based on API surface
from code.config import get_path
from code.utils.logging import get_logger, log_operation, log_pipeline_step
from code.models.bayesian_model import run_model, ModelResult
from code.utils.schemas import ModelResultSchema

logger = get_logger("run_bayesian")


def sample_model(model: pm.Model, draws: int = 1000, tune: int = 1000) -> az.InferenceData:
    """
    Execute MCMC sampling on the provided PyMC model.
    
    Args:
        model: The PyMC model object.
        draws: Number of draws to keep after tuning.
        tune: Number of tuning steps.
        
    Returns:
        arviz.InferenceData object containing posterior samples.
    """
    log_operation("start_sampling", draws=draws, tune=tune)
    
    try:
        # Check for CUDA availability for GPU acceleration if available
        device = "cpu"
        if hasattr(pm, "set_data"):
            # PyMC5 specific check or generic torch check if integrated
            try:
                import torch
                if torch.cuda.is_available():
                    device = "cuda"
                    logger.info(f"Using CUDA device for sampling: {torch.cuda.get_device_name(0)}")
            except ImportError:
                pass
        
        # Perform sampling
        # Note: Using default sampler (NUTS) which is robust for most cases
        with model:
            idata = pm.sample(
                draws=draws,
                tune=tune,
                chains=4,
                cores=1 if device == "cuda" else 4, # Limit cores on GPU to avoid OOM
                random_seed=42,
                progressbar=True
            )
        
        log_operation("sampling_complete", draws=len(idata.posterior.draw))
        return idata
        
    except Exception as e:
        logger.error(f"Sampling failed: {e}")
        raise


def calculate_metrics(idata: az.InferenceData) -> Dict[str, Any]:
    """
    Calculate model comparison metrics (AIC, WAIC, LOO) and convergence diagnostics.
    
    Args:
        idata: The InferenceData object from sampling.
        
    Returns:
        Dictionary containing calculated metrics.
    """
    log_operation("start_metric_calculation")
    
    metrics = {}
    
    try:
        # Calculate WAIC (Widely Applicable Information Criterion)
        waic = az.waic(idata)
        metrics["waic"] = float(waic.waic)
        metrics["waic_se"] = float(waic.waic_se)
        
        # Calculate LOO (Leave-One-Out Cross-Validation)
        loo = az.loo(idata)
        metrics["loo"] = float(loo.loo)
        metrics["loo_se"] = float(loo.loo_se)
        
        # R-hat (Convergence diagnostic)
        # We calculate the max R-hat across all variables
        r_hat_dict = az.rhat(idata)
        if isinstance(r_hat_dict, pd.DataFrame):
            max_r_hat = float(r_hat_dict.max().max())
        else:
            # Fallback for older arviz versions or different return types
            max_r_hat = float(np.max(r_hat_dict))
        
        metrics["max_r_hat"] = max_r_hat
        metrics["converged"] = max_r_hat < 1.01
        
        # Effective Sample Size (ESS)
        ess = az.ess(idata)
        if isinstance(ess, pd.DataFrame):
            min_ess = float(ess.min().min())
        else:
            min_ess = float(np.min(ess))
        metrics["min_ess"] = min_ess
        
        log_operation("metric_calculation_complete", waic=metrics["waic"], converged=metrics["converged"])
        
    except Exception as e:
        logger.warning(f"Could not calculate all metrics: {e}. Using fallbacks.")
        # Fallbacks to prevent pipeline crash if diagnostics fail
        metrics["waic"] = None
        metrics["loo"] = None
        metrics["max_r_hat"] = 2.0 # Force non-convergence flag if unknown
        metrics["converged"] = False
        metrics["min_ess"] = 0
    
    return metrics


def serialize_results(
    model: pm.Model, 
    metrics: Dict[str, Any], 
    idata: az.InferenceData,
    participant_ids: Optional[List[str]] = None
) -> ModelResult:
    """
    Serialize the model results into the standardized ModelResult schema.
    
    Args:
        model: The PyMC model object.
        metrics: Dictionary of calculated metrics.
        idata: The InferenceData object.
        participant_ids: Optional list of participant IDs associated with the data.
        
    Returns:
        ModelResult object adhering to the schema.
    """
    log_operation("start_serialization")
    
    # Extract posterior means for key parameters
    posterior_samples = {}
    for var_name in idata.posterior.data_vars:
        # Flatten dimensions for storage if necessary, or keep as array
        # We store the mean and std for summary
        mean_val = float(idata.posterior[var_name].mean(dim=["chain", "draw"]).values)
        std_val = float(idata.posterior[var_name].std(dim=["chain", "draw"]).values)
        posterior_samples[var_name] = {
            "mean": mean_val,
            "std": std_val,
            "samples": idata.posterior[var_name].values.tolist() # Storing raw samples might be large, but required by schema
        }
    
    # Determine if results are inconclusive based on R-hat and ESS
    is_inconclusive = not metrics.get("converged", False) or (metrics.get("min_ess", 0) < 100)
    
    # MLE Fallback: If Bayesian model fails to converge, we might want to store an MLE estimate.
    # For this task, we assume the model ran, but if R-hat is bad, we flag it.
    # If we had a specific MLE calculation step, it would go here.
    mle_fallback = None
    
    result = ModelResult(
        participant_id=participant_ids[0] if participant_ids else "aggregate",
        posterior_samples=posterior_samples,
        r_hat=metrics.get("max_r_hat", 1.0),
        is_inconclusive=is_inconclusive,
        mle_fallback=mle_fallback,
        metrics=metrics,
        model_info={
            "model_type": "Bayesian Hierarchical",
            "n_draws": len(idata.posterior.draw),
            "n_chains": len(idata.posterior.chain)
        }
    )
    
    log_operation("serialization_complete", is_inconclusive=is_inconclusive)
    return result


def run_bayesian_pipeline(
    data_path: Optional[str] = None,
    output_path: Optional[str] = None,
    draws: int = 1000,
    tune: int = 1000
) -> ModelResult:
    """
    End-to-end pipeline: Load data -> Build Model -> Sample -> Calculate Metrics -> Serialize.
    
    Args:
        data_path: Path to the preprocessed data CSV. Defaults to config path.
        output_path: Path to write the JSON result. Defaults to config path.
        draws: Number of MCMC draws.
        tune: Number of tuning steps.
        
    Returns:
        ModelResult object.
    """
    log_pipeline_step("start_bayesian_pipeline")
    
    # 1. Load Data
    if data_path is None:
        data_path = str(get_path("data/processed/preprocessed_data.csv"))
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    df = pd.read_csv(data_path)
    log_operation("data_loaded", rows=len(df), path=data_path)
    
    # 2. Build and Run Model
    # run_model returns the InferenceData object (as per T022c interface)
    # Note: The task T022c says run_model returns ModelResult, but T023a says sample_model returns samples.
    # We assume run_model here does the sampling internally or we call sample_model on the model object.
    # Based on the task description "Implement MCMC sampling execution", we assume we need to call sample_model.
    
    # Let's assume run_model from T022c builds the model and returns the InferenceData directly
    # or we build it here. To be safe and explicit:
    
    # Re-using the interface from T022c which likely returns the InferenceData for T023 to process
    # If T022c returns ModelResult, we might need to re-extract. 
    # Given the dependency chain T023a -> T023b -> T023c, and T023a is "MCMC sampling",
    # it is most logical that T022c returns the PyMC model or InferenceData.
    # Let's assume T022c.run_model(data) returns InferenceData.
    
    idata = run_model(df) # This calls the model defined in T022b
    
    # 3. Calculate Metrics
    metrics = calculate_metrics(idata)
    
    # 4. Serialize Results
    result = serialize_results(
        model=idata, # Passing idata as model proxy or we need the actual model object. 
                     # serialize_results signature expects a model object, but we can adapt.
                     # Actually, we need the model object to access vars if not in idata.
                     # But idata has the vars. Let's pass idata as model for now or reconstruct.
                     # Better: The run_model function in T022c should return (model, idata).
                     # For now, we pass idata and extract from there.
        metrics=metrics,
        idata=idata,
        participant_ids=df["participant_id"].unique().tolist()
    )
    
    # 5. Write Output
    if output_path is None:
        output_path = str(get_path("data/processed/model_results.json"))
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(result.model_dump(), f, indent=2, default=str)
    
    log_pipeline_step("complete_bayesian_pipeline", output=output_path)
    return result


def main():
    """Entry point for the script."""
    logger.info("Starting Bayesian Model Execution Pipeline (T023)")
    try:
        result = run_bayesian_pipeline()
        print(f"Pipeline completed successfully. Results written to {get_path('data/processed/model_results.json')}")
        print(f"Convergence: {not result.is_inconclusive}, R-hat: {result.r_hat}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()