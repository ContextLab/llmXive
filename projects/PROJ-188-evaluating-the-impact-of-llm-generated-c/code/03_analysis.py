import json
import csv
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests
from utils.metrics import calculate_bleu

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/intermediate/analysis.log')
    ]
)
logger = logging.getLogger(__name__)

def load_data() -> Dict[str, Any]:
    """Load responses and explanations data."""
    logger.info("Loading data...")
    
    # Load responses
    responses_path = Path("data/intermediate/responses.csv")
    if not responses_path.exists():
        raise FileNotFoundError(f"Responses file not found: {responses_path}")
    
    df_responses = pd.read_csv(responses_path)
    logger.info(f"Loaded {len(df_responses)} response records")
    
    # Load explanations
    explanations_path = Path("data/intermediate/explanations.json")
    if not explanations_path.exists():
        raise FileNotFoundError(f"Explanations file not found: {explanations_path}")
    
    with open(explanations_path, 'r') as f:
        explanations = json.load(f)
    
    logger.info(f"Loaded {len(explanations)} explanation records")
    return {
        'responses': df_responses,
        'explanations': explanations
    }

def filter_invalid(data: Dict[str, Any]) -> pd.DataFrame:
    """Filter invalid participants based on quality criteria."""
    df = data['responses']
    
    # Filter: latency > 30s AND missing_count < 0.8 * total_questions (3)
    # total_questions = 3 per participant
    df_filtered = df[
        (df['latency_ms'] > 30000) & 
        (df['missing_count'] < 0.8 * 3)
    ].copy()
    
    logger.info(f"Filtered from {len(df)} to {len(df_filtered)} valid records")
    return df_filtered

def run_lmm(df: pd.DataFrame) -> Any:
    """Run Linear Mixed Model analysis."""
    logger.info("Running Linear Mixed Model...")
    
    # Formula: answer ~ condition * complexity + (1|participant_id)
    formula = "answer ~ condition * complexity + (1|participant_id)"
    
    # Fit LMM
    model = smf.mixedlm(formula, df, groups=df["participant_id"])
    result = model.fit()
    
    logger.info(f"LMM F-statistic: {result.f_statistic}")
    logger.info(f"LMM p-values: {result.pvalues}")
    
    return result

def run_tukey_hsd(df: pd.DataFrame) -> Dict[str, Any]:
    """Run Tukey HSD post-hoc test."""
    logger.info("Running Tukey HSD post-hoc test...")
    
    from statsmodels.stats.multicomp import pairwise_tukeyhsd
    
    tukey = pairwise_tukeyhsd(endog=df['answer'], 
                              groups=df['condition'], 
                              alpha=0.05)
    
    # Extract results
    results = {
        'groups': tukey.groups,
        'meandiffs': tukey.meandiffs,
        'pvalues': tukey.pvalues,
        'reject': tukey.reject
    }
    
    logger.info(f"Tukey HSD completed: {len(results['pvalues'])} comparisons")
    return results

def calculate_bleu_sensitivity(data: Dict[str, Any], df_filtered: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate BLEU scores for LLM explanations vs official docstrings.
    Run analysis on subsets where BLEU scores meet varying high-quality thresholds.
    """
    logger.info("Starting BLEU sensitivity sweep...")
    
    explanations = data['explanations']
    explanations_df = pd.DataFrame(explanations)
    
    # Merge with responses to get answer/latency data
    merged_df = df_filtered.merge(
        explanations_df[['snippet_id', 'explanation']], 
        left_on='snippet_id', 
        right_on='snippet_id', 
        how='inner'
    )
    
    if merged_df.empty:
        logger.warning("No merged data found for BLEU calculation")
        return pd.DataFrame(columns=['threshold', 'accuracy_mean', 'latency_mean', 'p_value_interaction'])
    
    # Calculate BLEU scores for each explanation vs docstring
    bleu_scores = []
    for _, row in merged_df.iterrows():
        # Use explanation as candidate, docstring as reference
        # Note: In real data, docstrings should be in the explanations data
        # For now, we assume 'explanation' field contains the LLM explanation
        # and we need a reference (docstring). If not available, we skip.
        
        # Check if we have a reference (docstring)
        if 'docstring' in row and pd.notna(row['docstring']):
            candidate = row['explanation'] if pd.notna(row['explanation']) else ""
            reference = row['docstring']
            
            bleu = calculate_bleu(candidate, reference)
            bleu_scores.append(bleu)
        else:
            # If no docstring available, use a placeholder or skip
            # For sensitivity analysis, we need real BLEU scores
            logger.warning(f"Missing docstring for snippet {row.get('snippet_id')}, skipping BLEU calculation")
            bleu_scores.append(None)
    
    merged_df['bleu_score'] = bleu_scores
    
    # Define thresholds for sensitivity sweep
    thresholds = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    
    results = []
    
    for threshold in thresholds:
        # Filter to samples with BLEU >= threshold
        subset = merged_df[merged_df['bleu_score'] >= threshold]
        
        if len(subset) < 5:  # Minimum sample size for meaningful analysis
            logger.info(f"Threshold {threshold}: Only {len(subset)} samples, skipping analysis")
            results.append({
                'threshold': threshold,
                'accuracy_mean': None,
                'latency_mean': None,
                'p_value_interaction': None
            })
            continue
        
        logger.info(f"Threshold {threshold}: {len(subset)} samples")
        
        # Calculate accuracy mean (answer column is boolean)
        accuracy_mean = subset['answer'].mean()
        
        # Calculate latency mean
        latency_mean = subset['latency_ms'].mean()
        
        # Run LMM on this subset to get interaction p-value
        try:
            # Check if we have enough variation in condition and complexity
            if subset['condition'].nunique() < 2 or subset['complexity'].nunique() < 2:
                logger.warning(f"Threshold {threshold}: Insufficient variation in condition or complexity")
                results.append({
                    'threshold': threshold,
                    'accuracy_mean': accuracy_mean,
                    'latency_mean': latency_mean,
                    'p_value_interaction': None
                })
                continue
            
            model = smf.mixedlm(
                "answer ~ condition * complexity + (1|participant_id)", 
                subset, 
                groups=subset["participant_id"]
            )
            result = model.fit()
            
            # Extract interaction p-value
            # The interaction term is 'condition:complexity'
            interaction_p = None
            for key, p_val in result.pvalues.items():
                if 'condition' in key and 'complexity' in key:
                    interaction_p = p_val
                    break
            
            results.append({
                'threshold': threshold,
                'accuracy_mean': accuracy_mean,
                'latency_mean': latency_mean,
                'p_value_interaction': interaction_p
            })
            
        except Exception as e:
            logger.error(f"Error running LMM for threshold {threshold}: {e}")
            results.append({
                'threshold': threshold,
                'accuracy_mean': accuracy_mean,
                'latency_mean': latency_mean,
                'p_value_interaction': None
            })
    
    return pd.DataFrame(results)

def save_sensitivity_report(df_sensitivity: pd.DataFrame, output_path: str):
    """Save sensitivity report to CSV."""
    logger.info(f"Saving sensitivity report to {output_path}")
    df_sensitivity.to_csv(output_path, index=False)
    logger.info("Sensitivity report saved successfully")

def main():
    """Main function to run BLEU sensitivity sweep."""
    logger.info("Starting BLEU sensitivity sweep (Task T028)...")
    
    try:
        # Load data
        data = load_data()
        
        # Filter invalid participants
        df_filtered = filter_invalid(data)
        
        if df_filtered.empty:
            logger.error("No valid participants after filtering. Cannot run sensitivity analysis.")
            # Create empty report with headers
            empty_report = pd.DataFrame(columns=['threshold', 'accuracy_mean', 'latency_mean', 'p_value_interaction'])
            save_sensitivity_report(empty_report, 'data/processed/sensitivity_report.csv')
            return 1
        
        # Calculate BLEU sensitivity
        df_sensitivity = calculate_bleu_sensitivity(data, df_filtered)
        
        # Save report
        save_sensitivity_report(df_sensitivity, 'data/processed/sensitivity_report.csv')
        
        logger.info("BLEU sensitivity sweep completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Error in BLEU sensitivity sweep: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())