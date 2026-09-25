"""
Data Harmonization module.

Responsible for merging, cleaning, validating, and preparing datasets.
This module contains NO data generation logic.
"""
import os
import sys
import json
import logging
import hashlib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Tuple, List
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import get_project_root
from utils.checksum import update_artifact_hash

logger = logging.getLogger(__name__)

def calculate_cronbach_alpha(data: pd.DataFrame, item_cols: List[str]) -> float:
    """Calculates Cronbach's alpha for a list of item columns."""
    if len(item_cols) < 2:
        return 0.0
    
    # Ensure only numeric columns
    item_data = data[item_cols].dropna()
    if item_data.empty:
        return 0.0
        
    # Cronbach's alpha formula
    n_items = item_data.shape[1]
    variances = item_data.var(axis=0)
    total_var = item_data.var(axis=1).sum()
    sum_variances = variances.sum()
    
    if total_var == 0:
        return 0.0
        
    alpha = (n_items / (n_items - 1)) * (1 - (sum_variances / total_var))
    return alpha

def harmonize_datasets(data_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Merges, validates, and cleans the generated datasets.
    
    Args:
        data_dict: Dictionary with keys 'discounting', 'procrastination', 'nback', 'demographics'.
        
    Returns:
        Final harmonized DataFrame.
        
    Raises:
        SystemExit: If critical validation checks fail (ID mismatch, reliability).
    """
    project_root = get_project_root()
    processed_dir = project_root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Extract DataFrames
    discounting_df = data_dict["discounting"]
    procrastination_df = data_dict["procrastination"]
    nback_df = data_dict["nback"]
    demographics_df = data_dict["demographics"]
    
    # 2. Aggregate Participant IDs for Mismatch Check
    initial_ids = set(discounting_df["participant_id"].unique())
    initial_ids.update(procrastination_df["participant_id"].unique())
    initial_ids.update(nback_df["participant_id"].unique())
    initial_ids.update(demographics_df["participant_id"].unique())
    
    # 3. Merge DataFrames (Inner Join)
    merged_df = discounting_df.merge(procrastination_df, on="participant_id", how="inner")
    merged_df = merged_df.merge(nback_df, on="participant_id", how="inner")
    merged_df = merged_df.merge(demographics_df, on="participant_id", how="inner")
    
    final_ids = set(merged_df["participant_id"].unique())
    
    # 4. ID Mismatch Check
    mismatch_rate = 1 - (len(final_ids) / len(initial_ids))
    logger.info(f"ID mismatch rate: {mismatch_rate:.4f}")
    
    if mismatch_rate > 0.10:
        # Check if core constructs are affected (they are if mismatch > 0)
        # Since we are doing inner join on all, any mismatch means core constructs missing for those IDs
        halt_log = {
            "reason": "ID Mismatch > 10% for Core Constructs",
            "mismatch_rate": mismatch_rate,
            "initial_count": len(initial_ids),
            "final_count": len(final_ids)
        }
        with open(processed_dir / "halt_log.json", 'w') as f:
            json.dump(halt_log, f, indent=2)
        logger.error("CRITICAL: ID mismatch rate exceeds 10% for core constructs.")
        raise SystemExit(1)
    
    # 5. Reliability Check (Cronbach's Alpha)
    proc_items = [f"procrastination_item_{i}" for i in range(1, 11)]
    alpha_proc = calculate_cronbach_alpha(merged_df, proc_items)
    logger.info(f"Cronbach's Alpha (Procrastination): {alpha_proc:.4f}")
    
    if alpha_proc < 0.7:
        halt_log = {
            "reason": "CRITICAL: Data reliability below threshold (alpha < 0.7) - DGP failure",
            "alpha_procrastination": alpha_proc
        }
        with open(processed_dir / "halt_log.json", 'w') as f:
            json.dump(halt_log, f, indent=2)
        logger.error(f"CRITICAL: Reliability check failed. Alpha = {alpha_proc}")
        raise SystemExit(1)
        
    # Log reliability
    reliability_log = {"alpha_procrastination": alpha_proc}
    with open(processed_dir / "reliability_log.json", 'w') as f:
        json.dump(reliability_log, f, indent=2)
    
    # 6. Calculate Derived Metrics
    # Aggregate procrastination score (mean of items)
    merged_df["procrastination_score"] = merged_df[proc_items].mean(axis=1)
    
    # 7. Missing Data Handling (Covariates)
    covariates = ["age", "gender", "education"]
    missing_mask = merged_df[covariates].isnull().any(axis=1)
    missing_rate = missing_mask.sum() / len(merged_df)
    
    logger.info(f"Missing covariate rate: {missing_rate:.4f}")
    
    model_config = {"reduced_model": False, "excluded_covariates": [], "imputation_method": "mean"}
    
    if missing_rate > 0.10:
        model_config["reduced_model"] = True
        model_config["excluded_covariates"] = ["age", "gender", "education"]
        model_config["imputation_method"] = "listwise_deletion"
        merged_df = merged_df.dropna(subset=covariates)
        logger.warning("High missingness in covariates. Using listwise deletion.")
    else:
        # Mean imputation for numeric, mode for categorical
        for col in covariates:
            if col in merged_df.columns:
                if merged_df[col].dtype in ['int64', 'float64']:
                    fill_val = merged_df[col].mean()
                    merged_df[col].fillna(fill_val, inplace=True)
                    model_config["imputation_log"] = model_config.get("imputation_log", {})
                    model_config["imputation_log"][col] = fill_val
                else:
                    fill_val = merged_df[col].mode()[0]
                    merged_df[col].fillna(fill_val, inplace=True)
                    model_config["imputation_log"] = model_config.get("imputation_log", {})
                    model_config["imputation_log"][col] = fill_val
    
    # Write model config
    with open(processed_dir / "model_config.json", 'w') as f:
        json.dump(model_config, f, indent=2)
        
    # 8. Write Data Source Flag
    # Calculate hash of DGP params (from previous step or hardcoded)
    dgp_params_path = processed_dir / "dgp_params.log"
    dgp_hash = "N/A"
    if dgp_params_path.exists():
        with open(dgp_params_path, 'rb') as f:
            dgp_hash = hashlib.sha256(f.read()).hexdigest()
            
    data_source_flag = {
        "source": "synthetic_dgp",
        "n": len(merged_df),
        "methodology": "Methodological Validation",
        "dgp_params_hash": dgp_hash
    }
    with open(processed_dir / "data_source_flag.json", 'w') as f:
        json.dump(data_source_flag, f, indent=2)
        
    # 9. Write Final Dataset
    output_path = processed_dir / "harmonized_dataset.parquet"
    merged_df.to_parquet(output_path, index=False)
    logger.info(f"Harmonized dataset written to {output_path}")
    
    # 10. Update Checksums
    update_artifact_hash(str(output_path))
    update_artifact_hash(str(processed_dir / "model_config.json"))
    update_artifact_hash(str(processed_dir / "data_source_flag.json"))
    
    return merged_df
