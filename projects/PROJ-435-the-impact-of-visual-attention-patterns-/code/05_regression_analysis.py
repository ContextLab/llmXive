import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.regression.mixed_linear import MixedLM

# Ensure we can import sibling utilities if needed
sys.path.insert(0, str(Path(__file__).parent))

from utils.logging_config import get_pipeline_logger, setup_logging

# --- Configuration & Paths ---
def get_paths():
    """Resolve project paths relative to the script location."""
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent
    return {
        "root": root_dir,
        "data_derived": root_dir / "data" / "derived",
        "state": root_dir / "state",
        "output": root_dir / "data" / "derived"
    }

# --- Data Loading ---
def load_merged_data(paths: Dict[str, Path]) -> pd.DataFrame:
    """
    Load the merged dataset from data/derived/merged_dataset.csv.
    Raises FileNotFoundError if the file does not exist.
    """
    file_path = paths["data_derived"] / "merged_dataset.csv"
    if not file_path.exists():
        raise FileNotFoundError(
            f"Merged dataset not found at {file_path}. "
            "Ensure T023 (Data Merge) has completed successfully."
        )
    
    logger = get_pipeline_logger()
    logger.info(f"Loading merged data from {file_path}")
    df = pd.read_csv(file_path)
    
    required_cols = ['participant_id', 'headline_id', 'belief_rating', 
                     'fixation_duration', 'valence', 'cognitive_reflection_score', 
                     'headline_length']
    
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in merged dataset: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
    return df

# --- Data Preparation ---
def prepare_data_for_regression(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare data for mixed-effects regression:
    - Ensure numeric types
    - Handle NaNs (drop rows with missing critical variables)
    - Center/scale if necessary (optional, but good practice)
    """
    logger = get_pipeline_logger()
    df = df.copy()
    
    # Convert to numeric, coercing errors to NaN
    numeric_cols = ['belief_rating', 'fixation_duration', 'valence', 
                    'cognitive_reflection_score', 'headline_length']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Drop rows with missing values in critical columns
    initial_count = len(df)
    df = df.dropna(subset=numeric_cols)
    dropped_count = initial_count - len(df)
    
    if dropped_count > 0:
        logger.warning(f"Dropped {dropped_count} rows due to missing values in regression variables.")
    
    # Create interaction terms explicitly for clarity in the model formula
    # Formula: belief_rating ~ fixation_duration * valence * crt + headline_length
    df['fixation_valence'] = df['fixation_duration'] * df['valence']
    df['fixation_crt'] = df['fixation_duration'] * df['cognitive_reflection_score']
    df['valence_crt'] = df['valence'] * df['cognitive_reflection_score']
    df['fixation_valence_crt'] = df['fixation_duration'] * df['valence'] * df['cognitive_reflection_score']
    
    logger.info("Data prepared for regression.")
    return df

# --- Regression Execution ---
def run_mixed_effects_regression(df: pd.DataFrame) -> Any:
    """
    Run mixed-effects regression using statsmodels.
    Model: belief_rating ~ fixation_duration * valence * crt + headline_length
    Random effects: (1 | participant_id) + (1 | headline_id)
    
    Note: statsmodels MixedLM handles one grouping factor natively. 
    For two random intercepts, we can use a workaround or fit sequentially.
    Given the constraints and typical statsmodels usage, we will fit:
    y ~ X + (1|group1) and include group2 as a fixed effect or use a specific formulation.
    
    However, to strictly follow the spec (1|participant) + (1|headline), 
    and since MixedLM in statsmodels supports only one grouping factor directly 
    without custom reparameterization, we will use a common approximation:
    Fit with participant as random, headline as fixed (or vice versa), 
    OR use a library like `linearmodels` if available. 
    
    Since the API surface implies standard libraries, we will implement a 
    robust approximation using `statsmodels` by treating one as random and 
    the other as fixed, OR if the dataset is balanced, we might aggregate.
    
    BETTER APPROACH for standard statsmodels: 
    We will fit the model with `participant_id` as the random group.
    We will include `headline_id` as a fixed effect factor (dummy variables) 
    to control for headline variance, as MixedLM doesn't natively support 
    multiple random grouping factors in a single call without complex re-indexing.
    This satisfies the control requirement effectively.
    
    Formula: belief_rating ~ fixation_duration * valence * cognitive_reflection_score + headline_length + C(headline_id)
    Random: 1 | participant_id
    """
    logger = get_pipeline_logger()
    logger.info("Running Mixed Effects Regression...")
    
    # Prepare formula
    # We use C() to treat headline_id as categorical fixed effects to control for it
    # This is a standard approximation when dual random intercepts are needed but 
    # the library limits grouping factors.
    formula = "belief_rating ~ fixation_duration * valence * cognitive_reflection_score + headline_length + C(headline_id)"
    
    # Prepare data for statsmodels
    # Convert categorical IDs to factors if they are numeric but treated as categories
    df_model = df.copy()
    
    try:
        # Fit the model
        # endog: dependent variable
        # exog: independent variables (intercept handled by formula)
        # groups: random effect grouping
        
        # We need to construct the design matrix manually or use formula api
        # Using formula API for clarity
        import patsy
        y, X = patsy.dmatrices(formula, df_model, return_type='dataframe')
        
        # Convert groups to categorical for grouping
        groups = df_model['participant_id'].astype('category')
        
        # Fit MixedLM
        # Note: This might be computationally intensive for large datasets
        model = MixedLM(y, X, groups=groups)
        result = model.fit(reml=False) # Use ML for comparison, REML for estimation
        
        logger.info("Regression model fitted successfully.")
        return result
        
    except Exception as e:
        logger.error(f"Error during regression fitting: {e}")
        raise

# --- Results Generation ---
def generate_results_dataframe(result: Any, df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract coefficients, p-values, and confidence intervals from the model result.
    Returns a DataFrame suitable for saving to CSV.
    """
    logger = get_pipeline_logger()
    
    # Extract summary table
    # result.params: coefficients
    # result.pvalues: p-values
    # result.conf_int(): confidence intervals
    
    params = result.params
    pvalues = result.pvalues
    conf_int = result.conf_int()
    
    # Create a structured DataFrame
    results_data = []
    
    for idx in params.index:
        # Skip the random effect variance terms if they appear in params (usually separate)
        if idx.startswith('Group Variance') or idx == 'Scale':
            continue
            
        coef = params[idx]
        p_val = pvalues[idx]
        ci_low = conf_int.loc[idx, 0]
        ci_high = conf_int.loc[idx, 1]
        
        results_data.append({
            'term': idx,
            'coefficient': coef,
            'std_err': result.bse[idx] if idx in result.bse.index else np.nan,
            'p_value': p_val,
            'ci_lower': ci_low,
            'ci_high': ci_high
        })
    
    results_df = pd.DataFrame(results_data)
    
    # Sort by term for readability
    results_df = results_df.sort_values('term')
    
    logger.info(f"Generated results dataframe with {len(results_df)} terms.")
    return results_df

def apply_multiple_comparison_correction(results_df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply Bonferroni correction to p-values.
    """
    logger = get_pipeline_logger()
    results_df = results_df.copy()
    
    # Only correct for the fixed effects (exclude intercept if desired, but usually included)
    # Count number of tests (rows in the dataframe)
    n_tests = len(results_df)
    
    # Bonferroni correction
    results_df['p_value_bonferroni'] = results_df['p_value'] * n_tests
    results_df['p_value_bonferroni'] = results_df['p_value_bonferroni'].clip(upper=1.0)
    
    logger.info("Applied Bonferroni correction.")
    return results_df

def generate_causal_framing_statement(results_df: pd.DataFrame) -> str:
    """
    Generate a causal framing statement based on the significance of the main interaction term.
    Target term: fixation_duration:valence:cognitive_reflection_score
    """
    logger = get_pipeline_logger()
    
    # Find the three-way interaction term
    # The exact name depends on patsy/statsmodels naming convention
    interaction_term_candidates = [
        'fixation_duration:valence:cognitive_reflection_score',
        'fixation_duration * valence * cognitive_reflection_score' # Fallback
    ]
    
    target_term = None
    p_value = None
    
    for term in interaction_term_candidates:
        if term in results_df['term'].values:
            target_term = term
            p_value = results_df[results_df['term'] == term]['p_value'].values[0]
            break
    
    if target_term is None:
        # Try to find any term containing the interaction parts if exact match fails
        # This is a heuristic fallback
        matching = results_df[results_df['term'].str.contains('fixation_duration.*valence.*cognitive_reflection_score', regex=True)]
        if not matching.empty:
            target_term = matching.iloc[0]['term']
            p_value = matching.iloc[0]['p_value']
    
    if p_value is None:
        logger.warning("Could not identify the three-way interaction term. Defaulting to non-significant statement.")
        return "Within the controlled experimental design of this study, the data shows no statistically significant evidence of a causal link between the variables regarding the effect of attention on belief. The observed association may be due to chance or other factors."
    
    if p_value < 0.05:
        return f"Within the controlled experimental design of this study, the data supports a causal link between visual attention, headline valence, and cognitive reflection regarding the effect of attention on belief, given the controlled stimuli (p < 0.05)."
    else:
        return f"Within the controlled experimental design of this study, the data shows no statistically significant evidence of a causal link between visual attention, headline valence, and cognitive reflection regarding the effect of attention on belief. The observed association may be due to chance or other factors (p >= 0.05)."

def main():
    """
    Main execution function for T027: Generate Regression Results.
    """
    # Setup logging
    setup_logging()
    logger = get_pipeline_logger()
    logger.info("Starting Task T027: Generate Regression Results")
    
    paths = get_paths()
    
    try:
        # 1. Load Data
        df = load_merged_data(paths)
        
        # 2. Prepare Data
        df_prep = prepare_data_for_regression(df)
        
        # 3. Run Regression
        model_result = run_mixed_effects_regression(df_prep)
        
        # 4. Generate Results DataFrame
        results_df = generate_results_dataframe(model_result, df_prep)
        
        # 5. Apply Correction
        results_df = apply_multiple_comparison_correction(results_df)
        
        # 6. Generate Causal Statement
        causal_statement = generate_causal_framing_statement(results_df)
        
        # 7. Save Outputs
        output_file = paths["output"] / "regression_results.csv"
        results_df.to_csv(output_file, index=False)
        logger.info(f"Saved regression results to {output_file}")
        
        # Save the causal statement to a JSON file as well for easy parsing
        statement_file = paths["state"] / "causal_framing.json"
        with open(statement_file, 'w') as f:
            json.dump({"statement": causal_statement, "interaction_p_value": float(results_df[results_df['term'].str.contains('fixation_duration.*valence.*cognitive_reflection_score', regex=True)]['p_value'].iloc[0]) if not results_df[results_df['term'].str.contains('fixation_duration.*valence.*cognitive_reflection_score', regex=True)].empty else None}, f, indent=2)
        logger.info(f"Saved causal framing statement to {statement_file}")
        
        logger.info("Task T027 completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during T027 execution: {e}")
        raise

if __name__ == "__main__":
    main()
