import os
import sys
import json
import logging
import warnings
from pathlib import Path
from typing import Dict, List, Any, Tuple

import pandas as pd
import numpy as np
from statsmodels.discrete.discrete_model import NegativeBinomial
from statsmodels.genmod.generalized_linear_model import GLM
from statsmodels.genmod.families import NegativeBinomial as NBFamily
from scipy.stats import chi2

# Ensure project root is in path for relative imports if run as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import ensure_directories
from data.schemas import get_schema, validate_dataframe

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / 'logs' / 'robustness.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def calculate_shannon_entropy(author_counts: pd.Series) -> float:
    """
    Calculate Shannon entropy of author contributions for a single repo.
    Formula: -sum(p * log(p)) where p is the proportion of lines by an author.
    """
    total_lines = author_counts.sum()
    if total_lines == 0:
        return 0.0
    
    proportions = author_counts / total_lines
    # Filter out zero proportions to avoid log(0)
    proportions = proportions[proportions > 0]
    
    entropy = -np.sum(proportions * np.log(proportions))
    return float(entropy)

def prepare_data_with_entropy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Shannon entropy for each repo based on author line counts.
    Assumes the input df has a column 'author_line_counts' which is a list/dict of {author: lines}.
    If 'author_line_counts' is missing or invalid, entropy is set to 0.
    """
    def safe_entropy(row):
        try:
            counts = row.get('author_line_counts', {})
            if not counts:
                return 0.0
            # Convert dict to series if needed
            if isinstance(counts, dict):
                s = pd.Series(counts)
            else:
                s = pd.Series(counts)
            return calculate_shannon_entropy(s)
        except Exception as e:
            logger.warning(f"Could not calculate entropy for {row.get('url', 'unknown')}: {e}")
            return 0.0

    df['entropy'] = df.apply(safe_entropy, axis=1)
    return df

def filter_zero_kloc(df: pd.DataFrame) -> pd.DataFrame:
    """Filter out rows where kloc is 0 (log(0) undefined)."""
    initial_count = len(df)
    df = df[df['kloc'] > 0].copy()
    filtered_count = initial_count - len(df)
    if filtered_count > 0:
        logger.warning(f"Filtered out {filtered_count} rows with kloc=0.")
    return df

def fit_negative_binomial_glm(df: pd.DataFrame, 
                              formula: str, 
                              offset_col: str = None) -> Tuple[Any, Dict[str, Any]]:
    """
    Fit a Negative Binomial GLM.
    Returns the fitted model and a dictionary of convergence status.
    """
    try:
        # Prepare data
        data = df.copy()
        
        # Handle offset if provided
        if offset_col:
            if offset_col not in data.columns:
                raise ValueError(f"Offset column '{offset_col}' not found in data.")
            # statsmodels offset expects log of the exposure/offset
            data['_offset'] = np.log(data[offset_col])
        
        # Fit model using GLM with NBFamily
        # Note: statsmodels GLM with NBFamily is the standard way to fit NB regression
        family = NBFamily()
        if offset_col:
            model = GLM.from_formula(formula, data=data, family=family, offset=data['_offset'])
        else:
            model = GLM.from_formula(formula, data=data, family=family)
        
        result = model.fit()
        return result, {"converged": True}
    except Exception as e:
        logger.error(f"GLM fitting failed: {e}")
        return None, {"converged": False, "error": str(e)}

def extract_results(result: Any, model_type: str) -> Dict[str, Any]:
    """
    Extract coefficients, standard errors, p-values, and confidence intervals.
    """
    if result is None:
        return {}
    
    params = result.params
    bse = result.bse
    pvalues = result.pvalues
    conf_int = result.conf_int()
    
    results_dict = {
        "model_type": model_type,
        "converged": True,
        "coefficients": {},
        "standard_errors": {},
        "p_values": {},
        "confidence_intervals_95": {}
    }
    
    for var in params.index:
        results_dict["coefficients"][var] = float(params[var])
        results_dict["standard_errors"][var] = float(bse[var])
        results_dict["p_values"][var] = float(pvalues[var])
        results_dict["confidence_intervals_95"][var] = [float(conf_int[var][0]), float(conf_int[var][1])]
    
    return results_dict

def benjamini_hochberg(p_values: Dict[str, float]) -> Dict[str, float]:
    """
    Apply Benjamini-Hochberg correction to a dictionary of p-values.
    Returns a dictionary of adjusted p-values.
    """
    if not p_values:
        return {}
    
    m = len(p_values)
    sorted_keys = sorted(p_values.keys(), key=lambda k: p_values[k])
    
    adjusted = {}
    prev_adj = 1.0
    
    # Iterate backwards
    for i, key in enumerate(reversed(sorted_keys)):
        rank = m - i
        raw_p = p_values[key]
        # BH formula: p * m / rank
        adj_p = raw_p * m / rank
        # Ensure monotonicity (non-decreasing from smallest rank to largest)
        # Since we iterate backwards (largest rank to smallest), we take min with previous
        adj_p = min(adj_p, prev_adj)
        adjusted[key] = min(adj_p, 1.0)
        prev_adj = adjusted[key]
    
    return adjusted

def run_subsample_analysis(df: pd.DataFrame, 
                           target_languages: List[str] = None,
                           offset_col: str = 'kloc',
                           formula: str = None) -> Dict[str, Any]:
    """
    Run GLM analysis on subsamples of the data by programming language.
    """
    if target_languages is None:
        target_languages = ['Python', 'JavaScript']
    
    if formula is None:
        formula = 'cve_count ~ author_count + project_age + release_count'
    
    results = {
        "subsample_analysis": {},
        "metadata": {
            "formula": formula,
            "offset_column": offset_col,
            "languages_analyzed": target_languages
        }
    }
    
    for lang in target_languages:
        logger.info(f"Processing subsample for language: {lang}")
        subsample = df[df['language'] == lang]
        
        if len(subsample) < 5:
            logger.warning(f"Insufficient data for language {lang} ({len(subsample)} rows). Skipping.")
            results["subsample_analysis"][lang] = {"error": "Insufficient data", "n_rows": len(subsample)}
            continue
        
        subsample = filter_zero_kloc(subsample)
        
        model_result, status = fit_negative_binomial_glm(
            subsample, 
            formula, 
            offset_col=offset_col
        )
        
        if model_result:
            extracted = extract_results(model_result, f"Subsample_{lang}")
            # Apply BH correction to p-values
            if 'p_values' in extracted:
                extracted['adjusted_p_values'] = benjamini_hochberg(extracted['p_values'])
            results["subsample_analysis"][lang] = extracted
        else:
            results["subsample_analysis"][lang] = {"error": "Model fitting failed", **status}
    
    return results

def run_entropy_analysis(df: pd.DataFrame, 
                         offset_col: str = 'kloc',
                         formula_entropy: str = None) -> Dict[str, Any]:
    """
    Run GLM analysis using Shannon entropy as the diversity predictor.
    """
    if formula_entropy is None:
        # Replace author_count with entropy
        formula_entropy = 'cve_count ~ entropy + project_age + release_count'
    
    logger.info("Preparing data with entropy metric...")
    df_with_entropy = prepare_data_with_entropy(df)
    df_with_entropy = filter_zero_kloc(df_with_entropy)
    
    logger.info(f"Fitting entropy-based GLM with {len(df_with_entropy)} rows...")
    model_result, status = fit_negative_binomial_glm(
        df_with_entropy,
        formula_entropy,
        offset_col=offset_col
    )
    
    results = {
        "entropy_analysis": {},
        "metadata": {
            "formula": formula_entropy,
            "offset_column": offset_col,
            "n_rows": len(df_with_entropy)
        }
    }
    
    if model_result:
        extracted = extract_results(model_result, "Entropy_Model")
        if 'p_values' in extracted:
            extracted['adjusted_p_values'] = benjamini_hochberg(extracted['p_values'])
        results["entropy_analysis"] = extracted
    else:
        results["entropy_analysis"] = {"error": "Model fitting failed", **status}
    
    return results

def main():
    """
    Main entry point for robustness analysis.
    Loads repo_metrics.csv, runs subsample and entropy analyses, and saves results.
    """
    logger.info("Starting Robustness Analysis (T024)...")
    
    # Paths
    metrics_path = Path(project_root) / 'data' / 'processed' / 'repo_metrics.csv'
    output_path = Path(project_root) / 'data' / 'processed' / 'robustness_results.json'
    
    ensure_directories()
    
    if not metrics_path.exists():
        logger.error(f"Input file not found: {metrics_path}")
        sys.exit(1)
    
    logger.info(f"Loading data from {metrics_path}")
    df = pd.read_csv(metrics_path)
    
    # Validate basic schema
    required_cols = ['url', 'language', 'author_count', 'kloc', 'cve_count', 'project_age', 'release_count']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        sys.exit(1)
    
    # Rename author_count to author_count if needed (ensure consistency)
    if 'unique_authors' in df.columns and 'author_count' not in df.columns:
        df['author_count'] = df['unique_authors']
    
    # Run Subsample Analysis
    logger.info("Running Subsample Analysis...")
    subsample_results = run_subsample_analysis(df)
    
    # Run Entropy Analysis
    logger.info("Running Entropy Analysis...")
    entropy_results = run_entropy_analysis(df)
    
    # Compile final results
    final_results = {
        "generated_at": pd.Timestamp.now().isoformat(),
        "input_file": str(metrics_path),
        "subsample_results": subsample_results,
        "entropy_results": entropy_results
    }
    
    # Save results
    logger.info(f"Saving results to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(final_results, f, indent=2)
    
    logger.info("Robustness analysis completed successfully.")
    return final_results

if __name__ == '__main__':
    main()