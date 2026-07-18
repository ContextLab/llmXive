"""
Validation script for T044: Run quickstart.md validation to ensure end-to-end reproducibility.

This script executes the core pipeline steps defined in the project's quickstart logic:
1. Verify directory structure.
2. Load configuration.
3. Generate synthetic data (Null and Alternative hypotheses).
4. Apply scaling methods (Standardize, MinMax, Robust).
5. Run statistical tests (T-test).
6. Calculate aggregate metrics.
7. Verify output artifacts exist.
"""

import os
import sys
import time
import logging
import json
import csv
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import existing modules based on API surface
from simulation.config import SimulationConfig, get_default_config
from simulation.generator import generate_synthetic_data
from simulation.logger import setup_logger
from preprocessing.scaling import standardize_data, min_max_scale, robust_scale
from analysis.tests import run_scaled_t_test, ScalingMethod
from analysis.metrics import calculate_aggregate_metrics, save_aggregate_metrics
from setup_directories import create_directories

# Setup logging
logger = setup_logger("quickstart_validation")

def check_directories() -> bool:
    """Verify required directory structure exists."""
    logger.info("Checking directory structure...")
    dirs = [
        "code", "data", "results", "logs",
        "data/raw", "data/scaled", "data/scaled/standardized",
        "data/scaled/minmax", "data/scaled/robust",
        "results/figures"
    ]
    for d in dirs:
        path = PROJECT_ROOT / d
        if not path.exists():
            logger.warning(f"Directory missing: {path}. Creating...")
            path.mkdir(parents=True, exist_ok=True)
    return True

def run_synthetic_generation() -> Dict[str, Any]:
    """Run synthetic data generation for Null and Alternative hypotheses."""
    logger.info("Generating synthetic data (Null Hypothesis)...")
    
    # Null Hypothesis Config
    null_config = SimulationConfig(
        n_samples=1000,
        mean_diff=0.0,
        std_dev=1.0,
        distribution_type="normal",
        skewness=0.0,
        heteroscedasticity=1.0,
        seed=42
    )
    
    null_data, null_valid, null_msg = generate_synthetic_data(null_config)
    if not null_valid:
        raise RuntimeError(f"Null hypothesis generation failed: {null_msg}")
    
    logger.info(f"Null hypothesis generated: {null_data.shape}, valid={null_valid}")

    logger.info("Generating synthetic data (Alternative Hypothesis)...")
    # Alternative Hypothesis Config
    alt_config = SimulationConfig(
        n_samples=1000,
        mean_diff=1.0,
        std_dev=1.0,
        distribution_type="normal",
        skewness=0.0,
        heteroscedasticity=1.0,
        seed=43
    )
    
    alt_data, alt_valid, alt_msg = generate_synthetic_data(alt_config)
    if not alt_valid:
        raise RuntimeError(f"Alternative hypothesis generation failed: {alt_msg}")
    
    logger.info(f"Alternative hypothesis generated: {alt_data.shape}, valid={alt_valid}")

    return {
        "null": null_data,
        "alt": alt_data,
        "null_valid": null_valid,
        "alt_valid": alt_valid
    }

def run_scaling_pipeline(data: Dict[str, Any]) -> Dict[str, Any]:
    """Apply scaling methods to generated data."""
    logger.info("Applying scaling methods...")
    scaled_results = {}
    
    for key, df in data.items():
        if df is None:
            continue
        
        # Standardize
        std_df = standardize_data(df)
        # Verify mean ~ 0, std ~ 1
        if not (abs(std_df.mean().mean()) < 0.01 and abs(std_df.std().mean() - 1.0) < 0.01):
            logger.warning(f"Standardization check failed for {key}")
        
        # MinMax
        mm_df = min_max_scale(df)
        # Verify min ~ 0, max ~ 1
        if not (abs(mm_df.min().min()) < 0.01 and abs(mm_df.max().max() - 1.0) < 0.01):
            logger.warning(f"MinMax check failed for {key}")

        # Robust
        robust_df = robust_scale(df)
        # Robust scaling doesn't guarantee 0-1, but should transform
        
        scaled_results[key] = {
            "standardized": std_df,
            "minmax": mm_df,
            "robust": robust_df
        }
    
    return scaled_results

def run_statistical_tests(scaled_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Run statistical tests on scaled data."""
    logger.info("Running statistical tests...")
    results = []
    
    # We run t-tests on the 'standardized' data for both hypotheses
    # Note: In a real scenario, we would run on all scaling methods.
    # Here we focus on the pipeline flow.
    
    for key, scaling_dict in scaled_data.items():
        std_df = scaling_dict["standardized"]
        
        # Assuming first two columns are group A and group B
        if std_df.shape[1] < 2:
            logger.warning(f"Not enough columns in {key} for t-test")
            continue
            
        group_a = std_df.iloc[:, 0]
        group_b = std_df.iloc[:, 1]
        
        # Run t-test
        test_result = run_scaled_t_test(group_a, group_b, ScalingMethod.STANDARDIZE)
        
        results.append({
            "hypothesis": key,
            "method": test_result.method,
            "p_value": test_result.p_value,
            "statistic": test_result.statistic,
            "significant": test_result.significant,
            "alpha": 0.05
        })
        
        logger.info(f"Test Result ({key}): p={test_result.p_value:.4f}, sig={test_result.significant}")
    
    return results

def run_aggregation(test_results: List[Dict[str, Any]]) -> None:
    """Aggregate metrics and save."""
    logger.info("Calculating aggregate metrics...")
    
    if not test_results:
        logger.warning("No test results to aggregate")
        return

    # Convert to DataFrame for metrics calculation
    import pandas as pd
    df_results = pd.DataFrame(test_results)
    
    # Calculate metrics (Type I error, Power, etc.)
    metrics = calculate_aggregate_metrics(df_results)
    
    # Save metrics
    save_aggregate_metrics(metrics, PROJECT_ROOT / "results" / "aggregate_metrics.json")
    logger.info("Aggregate metrics saved.")

def verify_artifacts() -> bool:
    """Verify that expected output artifacts exist."""
    logger.info("Verifying output artifacts...")
    
    required_files = [
        PROJECT_ROOT / "results" / "aggregate_metrics.json",
        PROJECT_ROOT / "logs" / "simulation.log"
    ]
    
    all_exist = True
    for f in required_files:
        if f.exists():
            logger.info(f"Found: {f}")
        else:
            logger.error(f"Missing: {f}")
            all_exist = False
    
    return all_exist

def main():
    """Main validation entry point."""
    start_time = time.time()
    logger.info("Starting Quickstart Validation (T044)...")
    
    try:
        # 1. Setup
        check_directories()
        
        # 2. Generate Data
        synthetic_data = run_synthetic_generation()
        
        # 3. Scale Data
        scaled_data = run_scaling_pipeline(synthetic_data)
        
        # 4. Run Tests
        test_results = run_statistical_tests(scaled_data)
        
        # 5. Aggregate
        run_aggregation(test_results)
        
        # 6. Verify
        success = verify_artifacts()
        
        elapsed = time.time() - start_time
        logger.info(f"Validation completed in {elapsed:.2f} seconds.")
        
        if success:
            logger.info("SUCCESS: All quickstart steps executed and artifacts verified.")
            return 0
        else:
            logger.error("FAILURE: Some artifacts missing.")
            return 1
            
    except Exception as e:
        logger.exception(f"Validation failed with exception: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
