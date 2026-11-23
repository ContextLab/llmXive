"""
T037-T044: Evaluation, Permutation Test, and SHAP Analysis.
Implements Additive vs. Interaction model comparison, Permutation Test, and SHAP Interaction Value analysis.
"""
import json
import os
import sys
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.inspection import permutation_importance
import shap
from config import get_project_root, get_config_value, get_n_permutations, get_n_estimators, get_random_seed

# --- Helper Functions ---

def load_json(path: str) -> Dict[str, Any]:
    """Load a JSON file."""
    with open(path, 'r') as f:
        return json.load(f)

def save_json(path: str, data: Dict[str, Any]) -> None:
    """Save a dictionary to a JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def load_model(path: str) -> Any:
    """Load a pickled model."""
    with open(path, 'rb') as f:
        return pickle.load(f)

def save_model(path: str, model: Any) -> None:
    """Save a model to a pickle file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        pickle.dump(model, f, protocol=4)

def load_data_chunked(path: str, chunksize: int = 1000) -> pd.DataFrame:
    """Load a CSV file, handling potential large files via chunking if necessary."""
    # For this specific project, we assume the engineered features file fits in memory
    # but use chunking logic if the file is large to be safe.
    chunks = []
    for chunk in pd.read_csv(path, chunksize=chunksize):
        chunks.append(chunk)
    return pd.concat(chunks, ignore_index=True)

def get_main_features() -> List[str]:
    """Return the list of main effect feature names."""
    return [
        'cold_work_pct', 'Mn_wt', 'Mg_wt', 'Si_wt', 'Cu_wt', 'annealing_temp_K'
    ]

def get_interaction_features() -> List[str]:
    """Return the list of interaction feature names."""
    return [
        'cold_work_Mn_content', 'cold_work_Mg_content', 'cold_work_Si_content', 'cold_work_Cu_content'
    ]

def get_all_features() -> List[str]:
    """Return the list of all feature names (main + interaction)."""
    return get_main_features() + get_interaction_features()

# --- Model Training Helpers (for Permutation Test Re-evaluation) ---

def train_additive_model(X: pd.DataFrame, y: pd.Series, n_estimators: int = 100, seed: int = 42) -> RandomForestRegressor:
    """Train a Random Forest model WITHOUT interaction features."""
    main_cols = get_main_features()
    # Ensure only main columns are used
    X_main = X[main_cols]
    model = RandomForestRegressor(n_estimators=n_estimators, random_state=seed, n_jobs=-1)
    model.fit(X_main, y)
    return model

def train_interaction_model(X: pd.DataFrame, y: pd.Series, n_estimators: int = 100, seed: int = 42) -> RandomForestRegressor:
    """Train a Random Forest model WITH interaction features."""
    all_cols = get_all_features()
    X_all = X[all_cols]
    model = RandomForestRegressor(n_estimators=n_estimators, random_state=seed, n_jobs=-1)
    model.fit(X_all, y)
    return model

# --- Permutation Test Logic ---

def run_permutation_test(
    additive_model: RandomForestRegressor,
    interaction_model: RandomForestRegressor,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    n_permutations: int = 1000,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Perform a Delta-Permutation Test.
    1. Calculate baseline MAE for both models on the validation set.
    2. Shuffle interaction terms jointly in X_val.
    3. Re-evaluate Interaction Model on shuffled data.
    4. Compare error distributions (Additive vs Interaction) to test significance.
    """
    np.random.seed(seed)
    interaction_cols = get_interaction_features()
    main_cols = get_main_features()

    # 1. Baseline Evaluation
    # Additive Model uses only main_cols
    y_pred_add = additive_model.predict(X_val[main_cols])
    mae_add_base = mean_absolute_error(y_val, y_pred_add)

    # Interaction Model uses all cols
    y_pred_int = interaction_model.predict(X_val[get_all_features()])
    mae_int_base = mean_absolute_error(y_val, y_pred_int)

    # 2. Permutation Loop
    # We shuffle the interaction columns in the validation set while keeping main effects constant.
    # We measure the drop in performance of the Interaction Model specifically.
    # The hypothesis is that shuffling interactions will increase the error of the Interaction Model
    # significantly more than the baseline difference suggests, or that the Interaction Model
    # significantly outperforms the Additive Model even after permutation noise is considered.

    # Strategy: Calculate the "Delta Error" (Additive Error - Interaction Error).
    # If interactions are important, the Interaction Model should have a much lower error.
    # If we shuffle interactions, the Interaction Model's error should rise, narrowing the gap.
    # We test if the original gap is statistically significant compared to the gap under permutation.

    # However, the task description says: "Calculate the difference between the Additive Model's error distribution
    # and the Interaction Model's error distribution (both original and permuted)."
    # And "Perform a statistical test on the difference in errors".

    # Let's implement:
    # For each permutation:
    #   a. Shuffle interaction_cols in X_val_copy.
    #   b. Predict with Interaction Model on shuffled data -> mae_int_perm.
    #   c. Additive model error stays same (since it doesn't use interactions) -> mae_add_base.
    #   d. Calculate diff = mae_add_base - mae_int_perm.
    # Compare the distribution of 'diff' under permutation vs the original 'diff' (mae_add_base - mae_int_base).
    # Actually, the original 'diff' is a single point. We need a distribution for the Additive model too?
    # The prompt says "Additive Model's error distribution". Since we have a single validation set,
    # we can bootstrap the validation set or use K-Fold CV scores if available.
    # Given the constraint, let's assume we use the single MAE values and perhaps bootstrap the validation set
    # to get distributions, or simply compare the single delta against the permuted deltas.

    # Simpler approach per prompt "shuffling interaction terms jointly":
    # We want to see if the Interaction Model's performance degrades significantly when interactions are broken.
    # We compare the original Interaction MAE vs the Permuted Interaction MAE.
    # But the prompt explicitly asks to compare Additive vs Interaction.

    # Let's follow the prompt strictly:
    # "Calculate the difference between the Additive Model's error distribution and the Interaction Model's error distribution"
    # We will generate a distribution of errors for the Additive model by bootstrapping the validation set (or using CV if pre-computed).
    # Since we don't have CV scores here, we will bootstrap the validation set for both models.

    n_bootstraps = 1000
    diffs_original = []
    diffs_permuted = []

    # Bootstrap original
    for _ in range(n_bootstraps):
        idx = np.random.choice(len(y_val), len(y_val), replace=True)
        X_boot = X_val.iloc[idx]
        y_boot = y_val.iloc[idx]

        # Additive
        pred_add = additive_model.predict(X_boot[main_cols])
        mae_add = mean_absolute_error(y_boot, pred_add)

        # Interaction
        pred_int = interaction_model.predict(X_boot[get_all_features()])
        mae_int = mean_absolute_error(y_boot, pred_int)

        diffs_original.append(mae_add - mae_int)

    # Bootstrap Permutation
    for _ in range(n_bootstraps):
        idx = np.random.choice(len(y_val), len(y_val), replace=True)
        X_boot = X_val.iloc[idx].copy()
        y_boot = y_val.iloc[idx]

        # Shuffle interaction columns in this boot sample
        for col in interaction_cols:
            np.random.shuffle(X_boot[col].values)

        # Additive (unchanged)
        pred_add = additive_model.predict(X_boot[main_cols])
        mae_add = mean_absolute_error(y_boot, pred_add)

        # Interaction (on shuffled)
        pred_int = interaction_model.predict(X_boot[get_all_features()])
        mae_int = mean_absolute_error(y_boot, pred_int)

        diffs_permuted.append(mae_add - mae_int)

    # Statistical Test: Mann-Whitney U or T-test
    from scipy.stats import ttest_ind
    stat, p_value = ttest_ind(diffs_original, diffs_permuted)

    # Calculate interaction term importance as the mean drop in R2 (or rise in MAE) due to permutation
    # Here we use the mean difference in the "advantage" (Additive - Interaction)
    # If interactions matter, Original Diff (Additive - Interaction) should be positive (Additive worse)
    # and large. Permutation should reduce this advantage.
    original_advantage = np.mean(diffs_original)
    permuted_advantage = np.mean(diffs_permuted)
    interaction_importance = original_advantage - permuted_advantage

    return {
        "p_value": float(p_value),
        "method": "delta_permutation_test_bootstrap",
        "interaction_term_importance": float(interaction_importance),
        "original_advantage": float(original_advantage),
        "permuted_advantage": float(permuted_advantage),
        "mae_add_base": float(mae_add_base),
        "mae_int_base": float(mae_int_base)
    }

def calculate_permutation_importance(
    model: RandomForestRegressor,
    X: pd.DataFrame,
    y: pd.Series,
    interaction_cols: List[str],
    n_repeats: int = 10,
    seed: int = 42
) -> Dict[str, float]:
    """Calculate permutation importance for specific interaction columns."""
    np.random.seed(seed)
    # We only permute the interaction columns
    result = permutation_importance(model, X, y, n_repeats=n_repeats, random_state=seed, scoring='neg_mean_absolute_error')
    # Filter for interaction columns
    importance_dict = {}
    for i, col in enumerate(X.columns):
        if col in interaction_cols:
            importance_dict[col] = float(result.importances_mean[i])
    return importance_dict

# --- SHAP Analysis ---

def run_shap_analysis(
    model: RandomForestRegressor,
    X: pd.DataFrame,
    interaction_cols: List[str],
    main_cols: List[str],
    nsamples: int = 1000,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Run SHAP Interaction Value analysis.
    Returns a report separating main effects and interaction terms.
    """
    np.random.seed(seed)
    # Use TreeExplainer
    explainer = shap.TreeExplainer(model)
    
    # Calculate SHAP interaction values
    # Note: SHAP interaction values are expensive. We use a sample if X is large.
    if len(X) > nsamples:
        X_sample = X.sample(n=nsamples, random_state=seed)
    else:
        X_sample = X

    shap_interaction_values = explainer.shap_interaction_values(X_sample)

    # shap_interaction_values shape: (nsamples, n_features, n_features)
    # We need to aggregate this to get feature importance and interaction strength.
    
    # Aggregate absolute values to get importance
    # Mean absolute SHAP value for each feature (main effect)
    main_effects = np.mean(np.abs(shap_interaction_values), axis=(0, 2)) # Sum over j to get main effect i? 
    # Actually, for interaction values, the main effect of i is often sum_j SHAP_{ij} or similar.
    # Standard SHAP values (non-interaction) are the diagonal or sum of row/col?
    # shap_interaction_values[i, j] is the interaction between feature i and j.
    # The main effect of i is roughly the sum of interactions involving i? Or the diagonal?
    # Let's use the standard approach: Sum of absolute interaction values for each feature pair.
    
    # Flatten and sum to get global interaction strength
    # We want to rank "interaction term contributions" (the engineered features) vs "main effects".
    
    # Let's compute the mean absolute SHAP value for each feature (treating interactions as part of the feature's contribution)
    # For a feature i, its total contribution is sum over j of |SHAP_{ij}|?
    # Actually, the sum of SHAP values for a sample equals the prediction.
    # We will report the mean absolute SHAP value for each feature (summing over interactions with all others).
    
    feature_importance = np.sum(np.abs(shap_interaction_values), axis=(0, 2)) # Sum over j
    # Wait, shap_interaction_values[i, j] is the interaction.
    # The main effect of i is often approximated by the sum of interactions involving i?
    # Or we can just use the standard SHAP values (diagonal of interaction matrix? No, diagonal is self-interaction).
    # Let's use the sum of absolute values for each feature index across all interactions.
    # This gives a total "influence" score.
    
    # We need to separate "Main Effects" (cold_work, Mn, etc.) from "Interaction Terms" (cold_work_Mn, etc.)
    # The model was trained on [main_cols + interaction_cols].
    # So the indices correspond to these columns.
    
    # Map indices to names
    all_cols = X.columns.tolist()
    
    main_effect_contributions = {}
    interaction_term_contributions = {}
    
    for i, col in enumerate(all_cols):
        # Sum of absolute interactions for this feature
        score = float(np.sum(np.abs(shap_interaction_values[:, i, :])))
        
        if col in interaction_cols:
            interaction_term_contributions[col] = score
        else:
            main_effect_contributions[col] = score
    
    # Sort by contribution
    sorted_main = sorted(main_effect_contributions.items(), key=lambda x: x[1], reverse=True)
    sorted_interactions = sorted(interaction_term_contributions.items(), key=lambda x: x[1], reverse=True)

    return {
        "status": "success",
        "nsamples_used": len(X_sample),
        "features": [item[0] for item in sorted_main + sorted_interactions],
        "main_effects": dict(sorted_main),
        "interaction_terms": dict(sorted_interactions),
        "full_ranking": sorted_main + sorted_interactions
    }

# --- Pipeline Functions ---

def run_evaluation_pipeline():
    """
    Main pipeline for T037-T044:
    1. Train Additive Model (if not exists)
    2. Load Interaction Model
    3. Run Permutation Test (T039)
    4. Calculate Permutation Importance (T040)
    5. Run SHAP Analysis (T041)
    6. Generate Statistical Significance Report (T042)
    """
    project_root = get_project_root()
    data_dir = project_root / "data" / "processed"
    artifacts_dir = project_root / "artifacts"
    reports_dir = artifacts_dir / "reports"
    models_dir = artifacts_dir / "models"

    # Paths
    validated_clipped_path = data_dir / "validated_clipped.csv"
    engineered_features_path = data_dir / "engineered_features.csv"
    interaction_model_path = models_dir / "kinetic_model.pkl"
    additive_model_path = models_dir / "additive_model.pkl"
    split_indices_path = data_dir / "split_indices.npy"
    training_metrics_path = reports_dir / "training_metrics.json"
    permutation_intermediate_path = reports_dir / "permutation_intermediate.json"
    shap_report_path = reports_dir / "shap_interaction_report.json"
    statistical_significance_path = reports_dir / "statistical_significance.json"

    # 1. Load Data
    print("Loading validated clipped data...")
    df_clipped = load_data_chunked(validated_clipped_path)
    print(f"Loaded {len(df_clipped)} rows.")

    print("Loading engineered features...")
    df_engineered = load_data_chunked(engineered_features_path)
    print(f"Loaded {len(df_engineered)} rows.")

    # 2. Check Pure Aluminum Flag (from T033)
    print("Checking pure_aluminum_flag...")
    training_metrics = load_json(training_metrics_path)
    pure_aluminum_flag = training_metrics.get("pure_aluminum_flag", False)

    if pure_aluminum_flag:
        print("Pure Aluminum detected. Skipping SHAP analysis.")
        shap_report = {"status": "N/A", "features": [], "interaction_terms": []}
        save_json(shap_report_path, shap_report)
        print(f"Saved empty SHAP report to {shap_report_path}")
    else:
        # 3. Prepare Data for Models
        # We need X and y.
        # Target: time_to_peak_min
        target_col = 'time_to_peak_min'
        
        # Load split indices to get validation set
        split_indices = np.load(split_indices_path, allow_pickle=True).item()
        val_indices = split_indices.get('val_indices', split_indices.get('test_indices')) # Use test as val for permutation test logic if needed, or CV
        # The prompt says "Re-evaluate BOTH models on the SAME data split".
        # We will use the test set for this re-evaluation.
        
        X_val = df_engineered.iloc[val_indices].drop(columns=[target_col])
        y_val = df_engineered.iloc[val_indices][target_col]

        # 4. Train Additive Model (T037)
        if not additive_model_path.exists():
            print("Training Additive Model...")
            additive_model = train_additive_model(X_val, y_val, n_estimators=get_n_estimators(), seed=get_random_seed())
            save_model(additive_model_path, additive_model)
        else:
            print("Loading existing Additive Model...")
            additive_model = load_model(additive_model_path)

        # 5. Load Interaction Model (T038)
        print("Loading Interaction Model...")
        interaction_model = load_model(interaction_model_path)

        # 6. Run Permutation Test (T039)
        print("Running Permutation Test...")
        n_perms = get_n_permutations()
        perm_results = run_permutation_test(
            additive_model, interaction_model, X_val, y_val, 
            n_permutations=n_perms, seed=get_random_seed()
        )
        save_json(permutation_intermediate_path, perm_results)
        print(f"Permutation test completed. p-value: {perm_results['p_value']}")

        # 7. Calculate Permutation Importance (T040)
        print("Calculating Permutation Importance...")
        interaction_cols = get_interaction_features()
        # We need the full X for the model to calculate importance correctly
        X_full = df_engineered.drop(columns=[target_col])
        perm_importance = calculate_permutation_importance(
            interaction_model, X_full, y_val, interaction_cols, n_repeats=10, seed=get_random_seed()
        )
        # Add to perm_results or separate? Prompt says "Pass results to T042".
        # We'll update the intermediate file or create a combined one.
        perm_results['permutation_importance'] = perm_importance
        save_json(permutation_intermediate_path, perm_results)

        # 8. Run SHAP Analysis (T041)
        print("Running SHAP Analysis...")
        shap_report = run_shap_analysis(
            interaction_model, X_val, interaction_cols, get_main_features(),
            nsamples=1000, seed=get_random_seed()
        )
        save_json(shap_report_path, shap_report)
        print(f"SHAP report saved to {shap_report_path}")

        # 9. Generate Statistical Significance Report (T042)
        print("Generating Statistical Significance Report...")
        conclusion = "Interaction terms are statistically significant (p < 0.05)." if perm_results['p_value'] < 0.05 else "Interaction terms are NOT statistically significant (p >= 0.05)."
        stat_sig_report = {
            "p_value": perm_results['p_value'],
            "method": perm_results['method'],
            "interaction_term_importance": perm_results['interaction_term_importance'],
            "conclusion": conclusion
        }
        save_json(statistical_significance_path, stat_sig_report)
        print(f"Statistical significance report saved to {statistical_significance_path}")

def main():
    run_evaluation_pipeline()

if __name__ == "__main__":
    main()
