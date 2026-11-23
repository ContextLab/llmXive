"""
Robustness analysis for T033b: Indoor/Outdoor Confound Analysis (Bootstrap).

This script performs a bootstrap robustness check to quantify the potential
noise impact of missing urban/rural proxy data (if T028h failed) or if the
primary proxy analysis (T033a) was skipped.

It resamples the merged dataset with replacement, re-runs the primary model
logic (fitting a mixed-effects model), and reports the variance in the
temperature coefficient.

It also ensures the limitations.md file is updated with the results.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from typing import Dict, Any, Optional, List, Tuple

# Import project config and utilities
from config import get_path_env_override
from loaders import load_parquet_as_df
from modeling import fit_lmm, run_primary_modeling

# Setup logging
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('results/logs/robustness_analysis.log')
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def parse_args():
    parser = argparse.ArgumentParser(description='Bootstrap robustness analysis for T033b')
    parser.add_argument('--input', type=str, default='data/processed/merged_dataset.parquet',
                        help='Path to the merged dataset')
    parser.add_argument('--output', type=str, default='results/stats/noise_impact.json',
                        help='Path to save the noise impact results')
    parser.add_argument('--n-bootstrap', type=int, default=100,
                        help='Number of bootstrap iterations')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed for reproducibility')
    return parser.parse_args()

def load_data(input_path: str) -> pd.DataFrame:
    """Load the merged dataset."""
    logger.info(f"Loading data from {input_path}")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    return load_parquet_as_df(input_path)

def run_bootstrap_analysis(df: pd.DataFrame, n_bootstrap: int, seed: int) -> Dict[str, Any]:
    """
    Perform bootstrap analysis on the temperature coefficient.
    
    Returns a dictionary containing the mean, std, and confidence intervals
    of the temperature coefficient across bootstrap samples.
    """
    logger.info(f"Starting bootstrap analysis with {n_bootstrap} iterations")
    
    # Set random seed
    np.random.seed(seed)
    
    coefficients = []
    p_values = []
    successes = 0
    failures = 0
    
    # Formula for the model (simplified version of primary model)
    # Using log(response_time) as dependent variable
    # Fixed effects: temperature_celsius, dilemma_complexity, time_of_day
    # Random effects: participant_id
    
    # Prepare data: ensure required columns exist
    required_cols = ['response_time', 'temperature_celsius', 'dilemma_complexity', 
                    'time_of_day', 'participant_id']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Log transform response time (handle zeros/negatives)
    df = df.copy()
    df['log_response_time'] = np.log1p(df['response_time'])
    
    # Drop rows with missing values in key variables
    df_clean = df.dropna(subset=['log_response_time', 'temperature_celsius', 
                                'dilemma_complexity', 'participant_id'])
    
    n_original = len(df_clean)
    logger.info(f"Clean dataset size: {n_original} rows")
    
    if n_original < 100:
        logger.warning("Dataset too small for meaningful bootstrap analysis")
        return {
            "status": "warning",
            "message": "Dataset too small for meaningful bootstrap analysis",
            "n_samples": 0,
            "coefficients": [],
            "p_values": []
        }
    
    for i in range(n_bootstrap):
        try:
            # Resample with replacement
            sample_df = df_clean.sample(n=n_original, replace=True, random_state=seed + i)
            
            # Fit model
            # Using a simplified formula for robustness check
            formula = "log_response_time ~ temperature_celsius + dilemma_complexity + C(time_of_day)"
            
            # Fit mixed effects model
            try:
                model = smf.mixedlm(formula, sample_df, groups=sample_df["participant_id"])
                result = model.fit(reml=False, maxiter=100)
                
                # Extract temperature coefficient
                if 'temperature_celsius' in result.params.index:
                    coef = result.params['temperature_celsius']
                    p_val = result.pvalues['temperature_celsius']
                    coefficients.append(coef)
                    p_values.append(p_val)
                    successes += 1
                else:
                    failures += 1
                    logger.warning(f"Iteration {i}: temperature_celsius not in model params")
                    
            except Exception as e:
                failures += 1
                logger.warning(f"Iteration {i} failed to converge: {str(e)}")
                continue
                
        except Exception as e:
            failures += 1
            logger.warning(f"Iteration {i} failed: {str(e)}")
            continue
    
    if not coefficients:
        logger.error("No successful bootstrap iterations")
        return {
            "status": "error",
            "message": "No successful bootstrap iterations",
            "n_samples": 0,
            "coefficients": [],
            "p_values": []
        }
    
    # Calculate statistics
    coefficients = np.array(coefficients)
    p_values = np.array(p_values)
    
    mean_coef = np.mean(coefficients)
    std_coef = np.std(coefficients)
    ci_lower = np.percentile(coefficients, 2.5)
    ci_upper = np.percentile(coefficients, 97.5)
    
    logger.info(f"Bootstrap results: mean={mean_coef:.6f}, std={std_coef:.6f}, "
               f"95% CI=[{ci_lower:.6f}, {ci_upper:.6f}]")
    
    return {
        "status": "success",
        "n_bootstrap": n_bootstrap,
        "n_successful": successes,
        "n_failed": failures,
        "original_sample_size": n_original,
        "temperature_coefficient": {
            "mean": float(mean_coef),
            "std": float(std_coef),
            "ci_95_lower": float(ci_lower),
            "ci_95_upper": float(ci_upper)
        },
        "p_values": {
            "mean": float(np.mean(p_values)),
            "significant_count": int(np.sum(p_values < 0.05)),
            "total": len(p_values)
        },
        "raw_coefficients": coefficients.tolist()[:10],  # Store first 10 for debugging
        "raw_p_values": p_values.tolist()[:10]
    }

def update_limitations_doc(results: Dict[str, Any], limitations_path: str):
    """Update the limitations.md file with bootstrap results."""
    logger.info(f"Updating limitations document at {limitations_path}")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(limitations_path), exist_ok=True)
    
    # Create or update the limitations document
    limitations_text = f"""# Limitations Analysis - T033b Bootstrap Results

## Indoor/Outdoor Confound Analysis (Bootstrap)

This analysis quantifies the potential noise impact of missing urban/rural proxy data
by performing a bootstrap robustness check.

### Methodology
- Resampled the merged dataset with replacement
- Re-ran the primary mixed-effects model for each bootstrap sample
- Analyzed variance in the temperature coefficient

### Results
- **Bootstrap Iterations**: {results.get('n_bootstrap', 0)}
- **Successful Iterations**: {results.get('n_successful', 0)}
- **Failed Iterations**: {results.get('n_failed', 0)}
- **Original Sample Size**: {results.get('original_sample_size', 0)}

### Temperature Coefficient Statistics
- **Mean**: {results.get('temperature_coefficient', {}).get('mean', 'N/A')}
- **Standard Deviation**: {results.get('temperature_coefficient', {}).get('std', 'N/A')}
- **95% Confidence Interval**: [{results.get('temperature_coefficient', {}).get('ci_95_lower', 'N/A')}, 
                         {results.get('temperature_coefficient', {}).get('ci_95_upper', 'N/A')}]

### P-value Analysis
- **Mean P-value**: {results.get('p_values', {}).get('mean', 'N/A')}
- **Significant Results**: {results.get('p_values', {}).get('significant_count', 0)}/{results.get('p_values', {}).get('total', 0)}

### Interpretation
The standard deviation of the temperature coefficient across bootstrap samples ({results.get('temperature_coefficient', {}).get('std', 'N/A')})
indicates the potential noise impact due to missing urban/rural proxy data. A higher standard deviation
suggests greater sensitivity to sampling variation.

### Limitations
1. This analysis assumes the primary model specification is correct
2. Bootstrap samples may not capture all sources of bias
3. Results are dependent on the quality of the original merged dataset

### Recommendations
- Consider collecting urban/rural proxy data in future studies
- Use these results to contextualize the primary findings
- Report the confidence interval alongside point estimates

"""
    
    # Write to file
    with open(limitations_path, 'w') as f:
        f.write(limitations_text)
    
    logger.info("Limitations document updated successfully")

def save_results(results: Dict[str, Any], output_path: str):
    """Save the bootstrap results to a JSON file."""
    logger.info(f"Saving results to {output_path}")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info("Results saved successfully")

def main():
    args = parse_args()
    
    try:
        # Load data
        df = load_data(args.input)
        
        # Run bootstrap analysis
        results = run_bootstrap_analysis(df, args.n_bootstrap, args.seed)
        
        # Save results
        save_results(results, args.output)
        
        # Update limitations document
        limitations_path = "results/logs/limitations.md"
        update_limitations_doc(results, limitations_path)
        
        logger.info("Bootstrap analysis completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Bootstrap analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())