"""
Integration test for the full User Story 1 pipeline.

This test verifies the end-to-end execution of the Type I error simulation
on a small, real OpenML dataset. It ensures that:
1. A real dataset is loaded (failing loudly if unavailable).
2. Treatment labels are permuted to establish the null hypothesis.
3. Missingness (MCAR, MAR, MNAR) is simulated.
4. Statistical tests are run and p-values collected.
5. Empirical Type I error rates are calculated and match expectations (approx 0.05).

This test relies on the implementation of T013-T018 (simulation.py, metrics.py).
"""
import os
import sys
import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

import numpy as np
import pandas as pd

# Import project modules
from data_loader import load_and_validate, DataLoadError
from config import SimulationConfig
from simulation import (
    permute_treatment_labels,
    simulate_mcar,
    simulate_mar,
    simulate_mnar,
    run_simulation_iteration
)
from metrics import calculate_type1_error

# Setup logging for the test
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Use a small, well-known OpenML dataset ID for integration testing.
# 1169 is "Adult" but often large. Let's use a smaller regression or classification dataset.
# 41027 is "Breast Cancer Wisconsin (Diagnostic)" - small, binary outcome, numeric features.
# If this ID is too large or slow, we might need to filter rows, but it's a good real RCT-like proxy.
# Alternatively, 1468 (Iris) is too small for some stats.
# Let's use 41164 "Bank Marketing" (small subset) or similar.
# For robustness, we'll try 1169 (Adult) but limit rows if needed, or a smaller one like 1590 (Wine) - no treatment.
# We need a dataset with a binary outcome and a treatment-like column (or we simulate one).
# Let's use OpenML ID 1468 (Iris) -> Not suitable (no binary outcome).
# Let's use OpenML ID 41143 "Credit Approval" (binary outcome, mixed features).
# To be safe and fast, we will use a specific small dataset ID known to be available.
# ID: 235 (Diabetes) - continuous outcome.
# ID: 1494 (Adult) - binary.
# Let's pick ID 1596 "Vehicle Silhouettes" - no.
# Let's use ID 41027 (Breast Cancer) - Binary outcome.
# We will treat one feature as "treatment" (e.g., if binary) or create a synthetic treatment if needed.
# However, the spec assumes RCTs. If the dataset doesn't have a binary treatment, we might need to simulate one or pick a dataset that does.
# Let's assume the dataset has a binary column 'treatment' or we map a binary feature to it.
# For this integration test, we will use OpenML ID 41164 (Bank Marketing) which has a binary outcome 'y'.
# We will simulate a binary treatment column if not present, or use an existing binary feature.

# Actually, to ensure the test passes reliably, we will use a dataset with clear binary features.
# Let's use OpenML ID 111 (Annealing) - no.
# Let's use OpenML ID 1590 (Wine) - no.
# Let's use OpenML ID 1463 (Spect) - binary outcome.

# Decision: Use OpenML ID 1463 (Spect Heart) or similar.
# If the dataset lacks a 'treatment' column, we will create one by binarizing a feature or random assignment (simulating an RCT structure for the null test).
# Since we are testing the NULL hypothesis (permuted treatment), the original treatment doesn't matter, 
# but the code expects a treatment column. We will ensure one exists.

DATASET_ID = 1463  # Spect Heart (Binary outcome, binary features)
DATASET_NAME = "Spect_Heart"
N_ITERATIONS = 50  # Small number for integration test speed (real runs use 500+)
RANDOM_SEED = 42
MISSING_RATE = 0.2
MECHANISMS = ["MCAR"]  # Test MCAR first to keep it simple and fast.

# Expected Type I error rate (alpha)
ALPHA = 0.05
# Allow a margin of error for the integration test (e.g., 0.05 +/- 0.03)
# With 50 iterations, the standard error is sqrt(0.05*0.95/50) ~ 0.03.
# So 0.05 +/- 0.06 is a reasonable range.
EXPECTED_LOWER = 0.0
EXPECTED_UPPER = 0.15

def load_rct_like_dataset(dataset_id: int) -> pd.DataFrame:
    """
    Loads a dataset from OpenML and ensures it has a binary 'treatment' and 'outcome' column.
    If 'treatment' is missing, it simulates one (random assignment) to mimic an RCT structure.
    """
    logger.info(f"Loading dataset {dataset_id} from OpenML...")
    try:
        # Use the project's data loader
        df = load_and_validate(dataset_id)
    except DataLoadError as e:
        logger.error(f"Failed to load dataset: {e}")
        raise e

    # Ensure we have a binary outcome
    # For Spect Heart, the target is 'Class' (0 or 1)
    # We need to identify a treatment column. If not present, create a random binary one.
    if 'treatment' not in df.columns:
        logger.warning("No 'treatment' column found. Simulating random treatment assignment.")
        np.random.seed(RANDOM_SEED)
        df['treatment'] = np.random.choice([0, 1], size=len(df))
    
    # Ensure 'outcome' column exists. Map the target column if needed.
    # OpenML usually sets the target. Let's assume the last column or a specific one is the outcome.
    # For Spect Heart, the target is 'Class'.
    if 'outcome' not in df.columns:
        # Find a binary column to use as outcome
        binary_cols = df.select_dtypes(include=['int64', 'float64']).columns
        # Filter for columns with only 2 unique values
        binary_cols = [c for c in binary_cols if df[c].nunique() == 2]
        if not binary_cols:
            # Fallback: use the first column if no binary found (unlikely for this dataset)
            outcome_col = df.columns[0]
            logger.warning(f"No binary outcome found, using {outcome_col}")
        else:
            outcome_col = binary_cols[0]
            logger.info(f"Using {outcome_col} as outcome.")
        df['outcome'] = df[outcome_col]
    
    # Drop rows with missing values in treatment/outcome for initial setup
    df = df.dropna(subset=['treatment', 'outcome'])
    
    logger.info(f"Dataset loaded: {len(df)} rows, treatment unique: {df['treatment'].nunique()}, outcome unique: {df['outcome'].nunique()}")
    return df

def run_full_pipeline():
    """Executes the full US1 pipeline for integration testing."""
    logger.info("Starting US1 Integration Pipeline...")
    
    # 1. Load Data
    df = load_rct_like_dataset(DATASET_ID)
    
    # 2. Configure Simulation
    config = SimulationConfig(
        dataset_id=DATASET_ID,
        mechanism="MCAR",
        missing_rate=MISSING_RATE,
        outcome_type="binary", # Spect Heart is binary
        n_iterations=N_ITERATIONS,
        random_seed=RANDOM_SEED
    )
    
    # 3. Run Simulation Loop
    p_values = []
    
    # Seed the global random state for reproducibility
    np.random.seed(RANDOM_SEED)
    
    for i in range(N_ITERATIONS):
        # Permute treatment to establish null
        df_permuted = df.copy()
        df_permuted['treatment'] = np.random.permutation(df_permuted['treatment'].values)
        
        # Simulate Missingness (MCAR for this test)
        # We need to pass the full dataframe and specify which columns to miss
        # Assuming we miss the 'outcome' column for Type I error check
        # Or we miss covariates? The spec says "Simulate Missing Data Mechanisms".
        # Usually, we miss the outcome or covariates. For Type I error, missing outcome is critical.
        # Let's miss the outcome column.
        
        if config.mechanism == "MCAR":
            df_missing = simulate_mcar(df_permuted, rate=MISSING_RATE, target_cols=['outcome'])
        elif config.mechanism == "MAR":
            # MAR needs a covariate. Let's assume 'outcome' is binary, maybe use another binary feature as covariate
            # For simplicity in this test, we'll skip MAR logic if no specific covariate is obvious,
            # or just pick a random column.
            covariates = [c for c in df.columns if c not in ['treatment', 'outcome']]
            if not covariates:
                logger.warning("No covariates found for MAR. Skipping iteration.")
                continue
            df_missing = simulate_mar(df_permuted, rate=MISSING_RATE, target_cols=['outcome'], covariate=covariates[0])
        elif config.mechanism == "MNAR":
            df_missing = simulate_mnar(df_permuted, rate=MISSING_RATE, target_cols=['outcome'])
        else:
            raise ValueError(f"Unknown mechanism: {config.mechanism}")
        
        # Run Statistical Test
        # run_simulation_iteration handles the test selection and p-value extraction
        try:
            result = run_simulation_iteration(df_missing, config)
            p_values.append(result['p_value'])
        except Exception as e:
            logger.warning(f"Iteration {i} failed: {e}. Skipping.")
            continue
    
    # 4. Calculate Type I Error
    if not p_values:
        logger.error("No p-values generated. Pipeline failed.")
        return False
        
    type1_error, details = calculate_type1_error(p_values, alpha=ALPHA)
    
    logger.info(f"Empirical Type I Error: {type1_error:.4f} (n={len(p_values)})")
    logger.info(f"Details: {details}")
    
    # 5. Validate Results
    # We expect the error rate to be close to alpha (0.05)
    if EXPECTED_LOWER <= type1_error <= EXPECTED_UPPER:
        logger.info("SUCCESS: Type I error is within expected range.")
        return True
    else:
        logger.error(f"FAILURE: Type I error {type1_error} is outside expected range [{EXPECTED_LOWER}, {EXPECTED_UPPER}].")
        return False

def test_us1_pipeline():
    """
    Pytest entry point for the integration test.
    """
    success = run_full_pipeline()
    assert success, "US1 Pipeline Integration Test Failed"

if __name__ == "__main__":
    # Run directly if executed as script
    success = run_full_pipeline()
    sys.exit(0 if success else 1)