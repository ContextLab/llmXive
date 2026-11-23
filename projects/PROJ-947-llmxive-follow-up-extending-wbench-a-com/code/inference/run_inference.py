"""
Pipeline script for User Story 2: Execute CPU-Optimized Inference on Stratified Data.

This script orchestrates the inference process across a set of cases, 3 variants per case,
and N registered CPU-compatible models. It reads stratified samples and variants generated
in US1, loads registered models, runs inference with RAM profiling, and logs results.
"""
import os
import sys
import json
import time
import traceback
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional

# Project imports based on API surface
from config import get_config
from utils.logging import get_logger, log_info, log_error, log_exception
from utils.errors import fail_loudly, ResourceLimitError, SyntheticFallbackForbiddenError
from inference.models import get_registered_models, load_registered_models_from_file, ModelSpec
from inference.runner import run_inference_pipeline, get_current_ram_usage_gb, estimate_model_ram_requirement
from inference.failure_handler import handle_inference_failure

logger = get_logger(__name__)

def load_variants_input() -> pd.DataFrame:
    """
    Load the stratified variants from US1 generation step.
    Expected path: data/processed/variants.csv
    """
    variants_path = Path("data/processed/variants.csv")
    if not variants_path.exists():
        fail_loudly(
            f"Input file {variants_path} not found. "
            "Run US1 pipeline (code/entropy/run_pipeline.py) first."
        )
    df = pd.read_csv(variants_path)
    required_cols = ["case_id", "variant_type", "entropy_score"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        fail_loudly(f"Missing required columns in variants.csv: {missing}")
    return df

def load_validity_flags() -> pd.DataFrame:
    """
    Load validity flags from US1 validation step.
    Expected path: data/processed/validity_flags.csv
    """
    validity_path = Path("data/processed/validity_flags.csv")
    if not validity_path.exists():
        log_warning(f"Validity flags file {validity_path} not found. Proceeding without validity filtering.")
        return pd.DataFrame()
    df = pd.read_csv(validity_path)
    required_cols = ["case_id", "variant_type", "is_valid"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        log_warning(f"Missing required columns in validity_flags.csv: {missing}. Proceeding without filtering.")
        return pd.DataFrame()
    return df

def filter_valid_variants(variants_df: pd.DataFrame, validity_df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter variants to only include those marked as valid (is_valid=True).
    If validity_df is empty, return all variants.
    """
    if validity_df.empty:
        return variants_df
    
    valid_mask = validity_df["is_valid"] == True
    valid_variants = validity_df[valid_mask][["case_id", "variant_type"]]
    
    # Merge to keep only valid combinations
    merged = variants_df.merge(valid_variants, on=["case_id", "variant_type"], how="inner")
    log_info(f"Filtered to {len(merged)} valid variants out of {len(variants_df)} total.")
    return merged

def ensure_output_directories():
    """Ensure output directories exist."""
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    Path("results").mkdir(parents=True, exist_ok=True)

def run_inference_pipeline_task():
    """
    Main pipeline execution logic for T023.
    Processes cases × 3 variants × N models.
    """
    logger.info("Starting Inference Pipeline (T023)")
    ensure_output_directories()

    # Load configuration
    config = get_config()
    ram_limit_gb = config.get("ram_limit_gb", 6.5)
    max_models = config.get("max_models", 10)
    
    # Load input data
    log_info("Loading stratified variants from US1...")
    variants_df = load_variants_input()
    log_info(f"Loaded {len(variants_df)} variants.")

    # Load validity flags and filter
    log_info("Loading validity flags...")
    validity_df = load_validity_flags()
    filtered_variants = filter_valid_variants(variants_df, validity_df)
    if filtered_variants.empty:
        fail_loudly("No valid variants found after filtering. Cannot proceed with inference.")

    # Load registered models
    log_info("Loading registered CPU-compatible models...")
    models = load_registered_models_from_file()
    if not models:
        fail_loudly("No registered models found in code/inference/models.json. "
                   "Run model registration (T020) first.")
    
    # Filter models by RAM limit
    valid_models = []
    for model_spec in models:
        try:
            ram_req = estimate_model_ram_requirement(model_spec)
            if ram_req <= ram_limit_gb:
                valid_models.append(model_spec)
            else:
                log_info(f"Skipping model {model_spec['model_id']} (RAM: {ram_req:.2f} GB > {ram_limit_gb} GB)")
        except Exception as e:
            log_error(f"Could not estimate RAM for {model_spec['model_id']}: {e}")
    
    if len(valid_models) < 3:
        fail_loudly(f"Only {len(valid_models)} models meet RAM requirements. "
                   f"Minimum 3 required (per T024). Add more models or increase RAM limit.")
    
    log_info(f"Proceeding with {len(valid_models)} models: {[m['model_id'] for m in valid_models]}")

    # Run the actual inference pipeline
    # This calls the runner.py implementation which handles the per-case/per-model logic
    log_info(f"Running inference on {len(filtered_variants)} variants × {len(valid_models)} models...")
    
    results = run_inference_pipeline(
        variants_df=filtered_variants,
        models=valid_models,
        ram_limit_gb=ram_limit_gb
    )
    
    # Save results
    output_path = Path("data/processed/inference_results.csv")
    results.to_csv(output_path, index=False)
    log_info(f"Saved inference results to {output_path}")
    
    # Generate summary
    summary = {
        "total_cases": len(filtered_variants["case_id"].unique()),
        "total_variants": len(filtered_variants),
        "models_used": len(valid_models),
        "total_inferences": len(results),
        "success_count": len(results[results["status"] == "success"]),
        "proxy_count": len(results[results["status"] == "proxy"]),
        "failed_count": len(results[results["status"] == "failed"])
    }
    
    summary_path = Path("results/inference_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    log_info(f"Saved summary to {summary_path}")
    
    logger.info("Inference Pipeline completed successfully.")
    return results

def main():
    """Entry point for the pipeline."""
    try:
        run_inference_pipeline_task()
    except Exception as e:
        log_exception(e)
        fail_loudly(f"Pipeline failed: {e}")

if __name__ == "__main__":
    main()