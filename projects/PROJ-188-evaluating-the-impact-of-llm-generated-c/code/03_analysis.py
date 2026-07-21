import json
import csv
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.multicomp import pairwise_tukeyhsd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path("data")
INTERMEDIATE_DIR = DATA_DIR / "intermediate"
PROCESSED_DIR = DATA_DIR / "processed"

def load_data() -> pd.DataFrame:
    """
    Load and merge response data with snippet metadata.
    Expects:
      - data/intermediate/responses.csv (from T022/T022b)
      - data/intermediate/explanations.json (from T014)
    Returns a merged DataFrame ready for analysis.
    """
    responses_path = INTERMEDIATE_DIR / "responses.csv"
    explanations_path = INTERMEDIATE_DIR / "explanations.json"

    if not responses_path.exists():
        raise FileNotFoundError(f"Responses file not found: {responses_path}")
    if not explanations_path.exists():
        raise FileNotFoundError(f"Explanations file not found: {explanations_path}")

    # Load responses
    df_responses = pd.read_csv(responses_path)
    logger.info(f"Loaded {len(df_responses)} response records.")

    # Load explanations to get complexity labels
    with open(explanations_path, 'r') as f:
        explanations = json.load(f)

    # Create a mapping from snippet_id to complexity
    snippet_complexity = {}
    for item in explanations:
        if 'snippet_id' in item and 'complexity' in item:
            snippet_complexity[item['snippet_id']] = item['complexity']

    # Merge complexity into responses
    df_responses['complexity'] = df_responses['snippet_id'].map(snippet_complexity)

    # Validate merge
    null_complexity = df_responses['complexity'].isna().sum()
    if null_complexity > 0:
        logger.warning(f"Found {null_complexity} responses with missing complexity labels.")

    return df_responses

def filter_invalid(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter invalid participants based on quality criteria:
      - latency > 30000 ms (30s)
      - missing_count < 0.8 * total_questions (assuming 3 questions)
    """
    if df.empty:
        return df

    # Ensure numeric types
    df['latency_ms'] = pd.to_numeric(df['latency_ms'], errors='coerce')
    df['missing_count'] = pd.to_numeric(df['missing_count'], errors='coerce')

    total_questions = 3
    max_missing = 0.8 * total_questions

    # Filter
    valid_df = df[
        (df['latency_ms'] > 30000) &
        (df['missing_count'] < max_missing)
    ].copy()

    excluded_count = len(df) - len(valid_df)
    logger.info(f"Filtered {excluded_count} invalid participants. Remaining: {len(valid_df)}")

    return valid_df

def run_lmm(df: pd.DataFrame) -> Any:
    """
    Implement Linear Mixed Model (LMM) analysis.
    Fixed effects: condition, complexity, condition:complexity
    Random intercepts: participant_id (ONLY)
    Family: Gaussian
    Formula: answer ~ condition * complexity + (1|participant_id)
    
    ⚠️ DESIGN DECISION: Explicitly rejects GLMM in favor of Spec FR-005 LMM mandate.
    """
    if df.empty:
        raise ValueError("Cannot run LMM on empty DataFrame.")

    # Ensure categorical types for fixed effects
    df['condition'] = df['condition'].astype('category')
    df['complexity'] = df['complexity'].astype('category')
    df['participant_id'] = df['participant_id'].astype(str)

    # Check if 'answer' is numeric (0/1) or boolean
    if df['answer'].dtype == 'bool':
        df['answer'] = df['answer'].astype(int)

    formula = "answer ~ condition * complexity + (1 | participant_id)"
    
    logger.info(f"Fitting LMM with formula: {formula}")
    logger.info(f"Data shape: {df.shape}")
    logger.info(f"Unique participants: {df['participant_id'].nunique()}")

    try:
        # statsmodels MixedLM uses 'groups' for random effects syntax in formula interface
        # We use the formula API which handles the (1|group) syntax via patsy
        # However, statsmodels MixedLM formula interface is slightly different than lme4
        # Correct formula for statsmodels: "answer ~ condition * complexity", groups="participant_id"
        # But the task asks for formula string style. Let's use the explicit API for clarity.
        
        # Using the formula API for statsmodels MixedLM:
        # model = smf.mixedlm("answer ~ condition * complexity", df, groups=df["participant_id"])
        model = smf.mixedlm("answer ~ condition * complexity", df, groups=df["participant_id"])
        result = model.fit()
        
        logger.info("LMM fitting completed successfully.")
        logger.info(result.summary())
        
        return result
    except Exception as e:
        logger.error(f"Failed to fit LMM: {e}")
        raise

def run_tukey_hsd(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Implement post-hoc Tukey HSD test for pairwise condition comparisons.
    """
    if df.empty:
        return {}

    try:
        tukey = pairwise_tukeyhsd(
            endog=df['answer'],
            groups=df['condition'],
            alpha=0.05
        )
        
        # Extract results
        results = {
            "groups": list(tukey.groups),
            "data": []
        }
        
        # Iterate through comparisons
        for row in tukey.summary().data[1:]:
            # row format: [group1, group2, meandiff, p-adj, lower, upper, reject]
            results["data"].append({
                "group1": row[0],
                "group2": row[1],
                "mean_diff": float(row[2]),
                "p_adj": float(row[3]),
                "lower": float(row[4]),
                "upper": float(row[5]),
                "reject": bool(row[6])
            })
        
        logger.info("Tukey HSD completed.")
        return results
    except Exception as e:
        logger.error(f"Tukey HSD failed: {e}")
        return {"error": str(e)}

def calculate_bleu_sensitivity(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Placeholder for BLEU sensitivity sweep logic.
    This task (T026) focuses on the LMM implementation.
    The actual sweep (T028) will depend on BLEU scores which are not yet computed.
    We return an empty list here to satisfy the function signature for T026.
    """
    logger.info("BLEU sensitivity sweep is scheduled for T028. Skipping in T026.")
    return []

def save_sensitivity_report(report_data: List[Dict[str, Any]]) -> None:
    """
    Placeholder for saving sensitivity report.
    """
    logger.info("Saving sensitivity report is scheduled for T028.")

def main():
    """
    Main entry point for T026: LMM Implementation.
    """
    logger.info("Starting T026: Linear Mixed Model Analysis")
    
    try:
        # 1. Load Data
        df = load_data()
        
        # 2. Filter Invalid Participants
        df_valid = filter_invalid(df)
        
        if df_valid.empty:
            logger.error("No valid participants remaining after filtering. Aborting analysis.")
            sys.exit(1)
        
        # 3. Run LMM
        lmm_result = run_lmm(df_valid)
        
        # 4. Run Tukey HSD
        tukey_results = run_tukey_hsd(df_valid)
        
        # 5. Save Results (Basic JSON for now, full report in T029)
        output_dir = PROCESSED_DIR
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results_file = output_dir / "lmm_results.json"
        
        # Convert statsmodels result to serializable dict (limited)
        serializable_result = {
            "formula": "answer ~ condition * complexity + (1|participant_id)",
            "n_obs": int(df_valid.shape[0]),
            "n_groups": int(df_valid['participant_id'].nunique()),
            "fixed_effects": {
                "condition": lmm_result.params.get('condition[T.Code+LLM]', None),
                "complexity": lmm_result.params.get('complexity[T.medium]', None),
                "interaction": lmm_result.params.get('condition[T.Code+LLM]:complexity[T.medium]', None)
            },
            "p_values": {
                "condition": lmm_result.pvalues.get('condition[T.Code+LLM]', None),
                "complexity": lmm_result.pvalues.get('complexity[T.medium]', None),
                "interaction": lmm_result.pvalues.get('condition[T.Code+LLM]:complexity[T.medium]', None)
            },
            "tukey_hsd": tukey_results
        }
        
        with open(results_file, 'w') as f:
            json.dump(serializable_result, f, indent=2, default=str)
        
        logger.info(f"Results saved to {results_file}")
        logger.info("T026 completed successfully.")
        
    except Exception as e:
        logger.critical(f"T026 failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()