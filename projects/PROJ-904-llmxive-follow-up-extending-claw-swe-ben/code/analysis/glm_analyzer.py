import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np

class GLMConvergenceError(Exception):
    pass

def check_statsmodels_version():
    try:
        import statsmodels
        logging.info(f"statsmodels version: {statsmodels.__version__}")
    except ImportError:
        raise ImportError("statsmodels is required for GLM analysis")

def load_results_data(input_path: str) -> pd.DataFrame:
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Results file not found: {input_path}")
    return pd.read_csv(input_path)

def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['log_difficulty'] = np.log(df.get('line_count', 1) + 1)
    df['model_size_num'] = df['model_size'].map({'1B': 1, '7B': 7})
    return df

def fit_glm_standard(df: pd.DataFrame):
    try:
        import statsmodels.api as sm
        from statsmodels.genmod.generalized_linear_model import GLM
        from statsmodels.genmod import families

        y = df['pass_at_1'].astype(int)
        X = df[['model_size_num', 'log_difficulty']]
        X = sm.add_constant(X)
        
        model = GLM(y, X, family=families.Binomial())
        result = model.fit()
        return result
    except Exception as e:
        raise GLMConvergenceError(f"GLM fitting failed: {e}")

def fit_firth_glm(df: pd.DataFrame):
    # Fallback to standard GLM if Firth is not available
    logging.warning("Firth penalization not available, using standard GLM")
    return fit_glm_standard(df)

def fit_glm_with_interaction(df: pd.DataFrame):
    df = df.copy()
    df['interaction'] = df['model_size_num'] * df['log_difficulty']
    try:
        import statsmodels.api as sm
        from statsmodels.genmod.generalized_linear_model import GLM
        from statsmodels.genmod import families

        y = df['pass_at_1'].astype(int)
        X = df[['model_size_num', 'log_difficulty', 'interaction']]
        X = sm.add_constant(X)
        
        model = GLM(y, X, family=families.Binomial())
        result = model.fit()
        return result
    except Exception as e:
        raise GLMConvergenceError(f"GLM with interaction failed: {e}")

def calculate_pairwise_diff(df: pd.DataFrame, strategy: str) -> Tuple[float, float]:
    subset = df[df['strategy'] == strategy]
    if len(subset) == 0:
        return 0.0, 0.0
    
    mean_1b = subset[subset['model_size'] == '1B']['pass_at_1'].mean()
    mean_7b = subset[subset['model_size'] == '7B']['pass_at_1'].mean()
    
    return mean_1b - mean_7b, len(subset)

def check_significance(diff: float, p_value: float, threshold: float = 0.05) -> bool:
    return p_value < threshold

def determine_study_type(n: int) -> str:
    return "Exploratory" if n < 800 else "Confirmatory"

def calculate_odds_ratio_and_ci(df: pd.DataFrame) -> Dict[str, float]:
    # Placeholder for odds ratio calculation
    return {
        "odds_ratio": 1.0,
        "ci_lower": 0.8,
        "ci_upper": 1.2
    }

def power_analysis(n: int, effect_size: float = 0.1) -> float:
    # Simplified power calculation
    return 0.8 if n >= 800 else 0.5

def run_glm_analysis(input_path: str, output_path: str):
    df = load_results_data(input_path)
    df = prepare_features(df)
    
    result = fit_glm_with_interaction(df)
    
    analysis_results = {
        "sample_size": len(df),
        "study_type": determine_study_type(len(df)),
        "coefficients": result.params.to_dict(),
        "p_values": result.pvalues.to_dict()
    }
    
    with open(output_path, 'w') as f:
        json.dump(analysis_results, f, indent=2)
    
    logging.info(f"GLM analysis saved to {output_path}")

def generate_flags_and_report(input_path: str, output_path: str):
    df = load_results_data(input_path)
    n = len(df)
    study_type = determine_study_type(n)
    
    flags = {
        "strategy_found": False,
        "margin": 0.0,
        "p_value": 1.0,
        "odds_ratio": 1.0,
        "ci_lower": 0.0,
        "ci_upper": 0.0,
        "study_type": study_type
    }
    
    # Placeholder for actual analysis
    with open(output_path, 'w') as f:
        json.dump(flags, f, indent=2)
    
    logging.info(f"Analysis flags saved to {output_path}")

def main():
    logging.basicConfig(level=logging.INFO)
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    
    check_statsmodels_version()
    run_glm_analysis(args.input, args.output)

if __name__ == "__main__":
    main()
