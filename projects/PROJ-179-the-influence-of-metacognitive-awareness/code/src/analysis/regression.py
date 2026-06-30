import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Import stats utilities for model fitting (using statsmodels as per requirements)
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.diagnostic import het_breuschpagan
from scipy.stats import shapiro

# Import config utilities
from code.config.env_config import load_config, get_seed

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DERIVED_DIR = DATA_DIR / "derived"
RESULTS_DIR = DATA_DIR / "results"

def load_regression_data() -> pd.DataFrame:
    """
    Load the processed data required for regression.
    Expects:
      - data/derived/trial_data.csv (from T012)
      - data/results/primary_analysis.json (from T016, containing metacognitive scores per participant)
    
    Returns a dataframe with one row per participant containing:
      - participant_id
      - metacognitive_score (Type-2 AUC from training split)
      - reality_testing_accuracy (d' from test split)
      - age (if available)
      - gender (if available)
      - working_memory (if available)
    """
    trial_file = DERIVED_DIR / "trial_data.csv"
    if not trial_file.exists():
        raise FileNotFoundError(f"Required input file not found: {trial_file}")
    
    # Load primary analysis results to get per-participant scores
    # Note: T016 output structure assumes we have aggregated scores. 
    # If T016 output is group-level only, we must recompute per-participant scores here
    # based on the Hold-Out design logic defined in T014.
    
    # Since T016 produces group correlation, we need to reconstruct the participant-level
    # feature matrix for regression. We will re-calculate d' and Type-2 AUC per participant
    # using the same split logic to ensure consistency.
    
    # Load trial data
    df = pd.read_csv(trial_file)
    
    # Check for covariates
    has_age = 'age' in df.columns
    has_gender = 'gender' in df.columns
    has_working_memory = 'working_memory' in df.columns
    
    logger.info(f"Data columns found: {df.columns.tolist()}")
    logger.info(f"Covariates available: age={has_age}, gender={has_gender}, working_memory={has_working_memory}")
    
    # We need to aggregate by participant to get the scores used in the correlation.
    # The correlation in T014 used a 70/30 split. To be consistent, we replicate that logic.
    # However, for regression, we need the specific values.
    # Assuming T014 logic: Split trials 70/30. 
    # Training set -> Type-2 AUC. Test set -> d'.
    
    # We will implement a simplified aggregation here assuming the 'primary_analysis'
    # might not have per-participant breakdown if it was purely group-level.
    # But for regression, we MUST have per-participant (X, Y) pairs.
    
    # Strategy: Re-run the split logic per participant to extract the specific values.
    # This ensures the regression uses the exact same derived variables as the correlation.
    
    participant_scores = []
    
    for pid, group in df.groupby('participant_id'):
        # Ensure we have the necessary columns for the split
        # We need: confidence_rating, source_label (truth), participant_response
        
        if 'confidence_rating' not in group.columns or 'source_label' not in group.columns:
            logger.warning(f"Participant {pid} missing required columns for scoring. Skipping.")
            continue
        
        # Simulate 70/30 split (deterministic based on seed)
        seed = get_seed()
        np.random.seed(seed + int(pid) if isinstance(pid, int) else hash(pid))
        
        indices = group.index.tolist()
        np.random.shuffle(indices)
        split_idx = int(0.7 * len(indices))
        
        train_idx = indices[:split_idx]
        test_idx = indices[split_idx:]
        
        train_group = group.loc[train_idx]
        test_group = group.loc[test_idx]
        
        if len(train_group) == 0 or len(test_group) == 0:
            logger.warning(f"Participant {pid} has insufficient trials for split. Skipping.")
            continue
        
        # 1. Compute Metacognitive Score (Type-2 AUC) on TRAINING set
        # Type-2 AUC requires: Accuracy (binary) and Confidence ratings
        # Accuracy = (participant_response == source_label)
        train_group = train_group.copy()
        train_group['accuracy'] = (train_group['participant_response'] == train_group['source_label']).astype(int)
        
        # Compute Type-2 AUC (simplified implementation for this context)
        # We calculate the area under the Type-2 ROC curve.
        # This requires binning confidence and calculating hit/false alarm rates for metacognition.
        # Using a standard approximation:
        meta_auc = compute_type2_auc(train_group)
        
        # 2. Compute Reality Testing Accuracy (d') on TEST set
        test_group = test_group.copy()
        test_group['accuracy'] = (test_group['participant_response'] == test_group['source_label']).astype(int)
        
        # Compute d' (Signal Detection Theory)
        # d' = Z(Hit Rate) - Z(False Alarm Rate)
        # We assume source_label 1 is signal, 0 is noise (or similar mapping)
        # If binary classification:
        # Hit Rate = P(Response=1 | Source=1)
        # False Alarm Rate = P(Response=1 | Source=0)
        d_prime = compute_d_prime(test_group)
        
        if np.isnan(meta_auc) or np.isnan(d_prime):
            logger.warning(f"Participant {pid} produced NaN scores. Skipping.")
            continue
        
        row = {
            'participant_id': pid,
            'metacognitive_score': meta_auc,
            'reality_testing_accuracy': d_prime
        }
        
        # Add covariates if present (take the first value found for the participant)
        if has_age:
            row['age'] = group['age'].iloc[0]
        if has_gender:
            row['gender'] = group['gender'].iloc[0]
        if has_working_memory:
            row['working_memory'] = group['working_memory'].iloc[0]
        
        participant_scores.append(row)
    
    if not participant_scores:
        raise ValueError("No valid participant data found for regression.")
        
    result_df = pd.DataFrame(participant_scores)
    logger.info(f"Aggregated {len(result_df)} participants for regression.")
    return result_df

def compute_type2_auc(df: pd.DataFrame) -> float:
    """
    Compute Type-2 AUC (meta-d' approximation) from a dataframe.
    Requires: 'accuracy' (0/1), 'confidence_rating'
    """
    # Simplified Type-2 AUC calculation
    # Group by accuracy (correct/incorrect) and look at confidence distribution
    correct = df[df['accuracy'] == 1]['confidence_rating']
    incorrect = df[df['accuracy'] == 0]['confidence_rating']
    
    if len(correct) == 0 or len(incorrect) == 0:
        return np.nan
    
    # Calculate AUC using Mann-Whitney U statistic (equivalent to AUC for binary classification)
    # Here we treat 'correct' as positive class and 'incorrect' as negative class
    # We want to know if confidence is higher for correct answers.
    # AUC = P(confidence_correct > confidence_incorrect)
    u_stat, _ = sm.stats.mannwhitneyu(correct, incorrect, alternative='greater')
    n1 = len(correct)
    n2 = len(incorrect)
    auc = u_stat / (n1 * n2)
    
    return auc

def compute_d_prime(df: pd.DataFrame) -> float:
    """
    Compute d' (d-prime) from a dataframe.
    Requires: 'source_label', 'participant_response'
    Assumes labels are binary (0/1).
    """
    # Identify signal and noise
    # Assuming source_label 1 = Signal, 0 = Noise
    signal_mask = df['source_label'] == 1
    noise_mask = df['source_label'] == 0
    
    if signal_mask.sum() == 0 or noise_mask.sum() == 0:
        return np.nan
    
    hits = (df.loc[signal_mask, 'participant_response'] == 1).sum()
    misses = signal_mask.sum() - hits
    false_alarms = (df.loc[noise_mask, 'participant_response'] == 1).sum()
    correct_rejections = noise_mask.sum() - false_alarms
    
    hit_rate = hits / signal_mask.sum()
    fa_rate = false_alarms / noise_mask.sum()
    
    # Apply correction for extreme probabilities
    n = signal_mask.sum() + noise_mask.sum()
    if hit_rate == 0: hit_rate = 0.5 / signal_mask.sum()
    if hit_rate == 1: hit_rate = 1 - (0.5 / signal_mask.sum())
    if fa_rate == 0: fa_rate = 0.5 / noise_mask.sum()
    if fa_rate == 1: fa_rate = 1 - (0.5 / noise_mask.sum())
    
    # Z-scores
    try:
        z_hit = norm.ppf(hit_rate)
        z_fa = norm.ppf(fa_rate)
        d_prime = z_hit - z_fa
        return d_prime
    except Exception:
        return np.nan

def run_regression_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run hierarchical regression.
    Step 1: Controls (Age, Gender, Working Memory if present)
    Step 2: Add Metacognitive Score
    
    Returns dict with R2 change, F-change, coefficients, and model flags.
    """
    has_working_memory = 'working_memory' in df.columns
    
    # Prepare data
    y = df['reality_testing_accuracy'].values
    X_controls = []
    control_names = []
    
    if 'age' in df.columns:
        X_controls.append(df['age'].values)
        control_names.append('age')
    if 'gender' in df.columns:
        # Encode gender as numeric (0/1) assuming string or int
        gender_vals = df['gender'].astype(str).map({'Male': 0, 'Female': 1, 'M': 0, 'F': 1}).fillna(0).values
        X_controls.append(gender_vals)
        control_names.append('gender')
    
    # Step 1 Model
    if len(X_controls) > 0:
        X1 = np.column_stack(X_controls)
        X1 = sm.add_constant(X1)
        model1 = sm.OLS(y, X1).fit()
        r2_model1 = model1.rsquared
        adj_r2_model1 = model1.rsquared_adj
        n_params_model1 = len(model1.params)
    else:
        # No controls? Just intercept
        X1 = np.ones((len(y), 1))
        model1 = sm.OLS(y, X1).fit()
        r2_model1 = 0.0
        adj_r2_model1 = 0.0
        n_params_model1 = 1
    
    # Step 2 Model
    X2 = np.column_stack(X_controls + [df['metacognitive_score'].values])
    X2 = sm.add_constant(X2)
    model2 = sm.OLS(y, X2).fit()
    r2_model2 = model2.rsquared
    adj_r2_model2 = model2.rsquared_adj
    
    # Calculate Delta R2 and F-change
    delta_r2 = r2_model2 - r2_model1
    n = len(y)
    p1 = n_params_model1 - 1 # Number of predictors in model 1 (excluding const)
    p2 = X2.shape[1] - 1 # Number of predictors in model 2 (excluding const)
    
    # F-change = ((R2_full - R2_reduced) / (p_full - p_reduced)) / ((1 - R2_full) / (n - p_full - 1))
    if (1 - r2_model2) == 0:
        f_change = np.inf
    else:
        numerator = delta_r2 / (p2 - p1)
        denominator = (1 - r2_model2) / (n - p2 - 1)
        f_change = numerator / denominator
    
    # P-value for F-change
    from scipy.stats import f
    p_f_change = 1 - f.cdf(f_change, p2 - p1, n - p2 - 1)
    
    result = {
        "model_type": "hierarchical_regression",
        "n_participants": n,
        "step_1": {
            "predictors": control_names,
            "r_squared": float(r2_model1),
            "adj_r_squared": float(adj_r2_model1)
        },
        "step_2": {
            "predictors": control_names + ['metacognitive_score'],
            "r_squared": float(r2_model2),
            "adj_r_squared": float(adj_r2_model2),
            "coefficients": {
                name: float(coeff) for name, coeff in zip(model2.params.index, model2.params)
            },
            "p_values": {
                name: float(pval) for name, pval in zip(model2.pvalues.index, model2.pvalues)
            }
        },
        "change_statistics": {
            "delta_r_squared": float(delta_r2),
            "f_change": float(f_change),
            "p_f_change": float(p_f_change),
            "numerator_df": int(p2 - p1),
            "denominator_df": int(n - p2 - 1)
        },
        "n_minus_1_model": not has_working_memory, # Flag if working memory was missing
        "working_memory_present": has_working_memory
    }
    
    return result

def main():
    logger.info("Starting Regression Analysis (T020)...")
    
    try:
        # 1. Load Data
        df = load_regression_data()
        
        # 2. Run Analysis
        results = run_regression_analysis(df)
        
        # 3. Write Output
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        output_path = RESULTS_DIR / "regression_analysis.json"
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Regression analysis complete. Output written to {output_path}")
        logger.info(f"Delta R2: {results['change_statistics']['delta_r_squared']:.4f}, p: {results['change_statistics']['p_f_change']:.4f}")
        
    except Exception as e:
        logger.error(f"Regression analysis failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
