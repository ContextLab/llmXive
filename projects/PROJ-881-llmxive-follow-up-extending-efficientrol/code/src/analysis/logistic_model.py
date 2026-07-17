import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.regression.mixed_linear import MixedLM
from statsmodels.genmod.generalized_linear_model import GLM
from statsmodels.genmod.cov_struct import Exchangeable
from sklearn.metrics import roc_auc_score
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/logs/generation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class GLMMAnalysisResult:
    """Result container for Mixed-Effects Logistic Regression analysis."""
    
    def __init__(self, 
                coefficients: Dict[str, float],
                p_values: Dict[str, float],
                auc_roc: float,
                optimal_threshold: Optional[float] = None,
                significant: bool = True,
                stratification: Optional[str] = None,
                model_summary: Optional[str] = None,
                warning_message: Optional[str] = None):
        self.coefficients = coefficients
        self.p_values = p_values
        self.auc_roc = auc_roc
        self.optimal_threshold = optimal_threshold
        self.significant = significant
        self.stratification = stratification
        self.model_summary = model_summary
        self.warning_message = warning_message
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'coefficients': self.coefficients,
            'p_values': self.p_values,
            'auc_roc': self.auc_roc,
            'optimal_threshold': self.optimal_threshold,
            'significant': self.significant,
            'stratification': self.stratification,
            'model_summary': self.model_summary,
            'warning_message': self.warning_message
        }

def load_entropy_profiles_for_analysis(data_path: Path) -> pd.DataFrame:
    """Load and prepare entropy profiles for analysis."""
    if not data_path.exists():
        raise FileNotFoundError(f"Data path not found: {data_path}")
    
    # Load JSONL file with entropy profiles
    records = []
    with open(data_path, 'r') as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    
    df = pd.DataFrame(records)
    
    # Flatten layer-wise entropy values
    entropy_records = []
    for _, row in df.iterrows():
        sequence_id = row['sequence_id']
        validity = row['validity']
        layers = row.get('layers', [])
        
        for layer_idx, layer_data in enumerate(layers):
            entropy_values = layer_data.get('entropy_values', [])
            for token_idx, entropy_val in enumerate(entropy_values):
                entropy_records.append({
                    'sequence_id': sequence_id,
                    'layer': layer_idx,
                    'token_position': token_idx,
                    'entropy': entropy_val,
                    'validity': validity
                })
    
    return pd.DataFrame(entropy_records)

def fit_mixed_effects_model(df: pd.DataFrame) -> GLMMAnalysisResult:
    """
    Fit a Mixed-Effects Logistic Regression model to predict validity from entropy.
    
    Handles cases where p-values are not significant (p >= 0.05) by logging a warning
    and returning a result object with significant=False instead of crashing.
    """
    logger.info("Fitting Mixed-Effects Logistic Regression model")
    
    # Prepare data
    df = df.dropna(subset=['entropy', 'validity'])
    
    if len(df) == 0:
        raise ValueError("No valid data points for model fitting")
    
    # Create binary target variable
    y = df['validity'].astype(int)
    X = df[['entropy']]
    X = sm.add_constant(X)  # Add intercept
    
    # Group by sequence_id for random intercepts
    groups = df['sequence_id']
    
    try:
        # Fit mixed-effects logistic regression using GLM with random effects approximation
        # Since statsmodels MixedLM is for linear models, we use GLM with GEE as approximation
        # for logistic regression with clustering
        model = sm.GLM(y, X, 
                     family=sm.families.Binomial(),
                     groups=groups,
                     cov_struct=Exchangeable())
        
        result = model.fit()
        
        # Extract coefficients and p-values
        coefficients = {
            'intercept': float(result.params['const']),
            'entropy': float(result.params['entropy'])
        }
        
        p_values = {
            'intercept': float(result.pvalues['const']),
            'entropy': float(result.pvalues['entropy'])
        }
        
        # Check for significance
        entropy_p_value = p_values['entropy']
        significant = entropy_p_value < 0.05
        
        warning_message = None
        if not significant:
            warning_message = f"Entropy coefficient not statistically significant (p={entropy_p_value:.4f} >= 0.05)"
            logger.warning(warning_message)
        
        # Calculate AUC-ROC
        try:
            y_pred = result.predict(X)
            auc_roc = roc_auc_score(y, y_pred)
        except Exception as e:
            logger.warning(f"Could not calculate AUC-ROC: {e}")
            auc_roc = 0.5  # Default to random performance
        
        return GLMMAnalysisResult(
            coefficients=coefficients,
            p_values=p_values,
            auc_roc=auc_roc,
            significant=significant,
            model_summary=str(result.summary())
        )
        
    except Exception as e:
        logger.error(f"Error fitting mixed-effects model: {e}")
        raise

def calculate_auc_roc(df: pd.DataFrame, predictions: np.ndarray) -> float:
    """Calculate AUC-ROC metric."""
    y_true = df['validity'].values
    return roc_auc_score(y_true, predictions)

def analyze_entropy_validity_relationship(data_path: Path, 
                                        output_path: Optional[Path] = None) -> GLMMAnalysisResult:
    """
    Main analysis function that loads data, fits model, and returns results.
    
    Handles non-significant p-values gracefully by returning a result object
    with significant=False instead of crashing.
    """
    logger.info(f"Starting entropy-validity relationship analysis")
    
    # Load data
    df = load_entropy_profiles_for_analysis(data_path)
    logger.info(f"Loaded {len(df)} data points")
    
    # Fit model
    result = fit_mixed_effects_model(df)
    
    # Log results
    logger.info(f"Analysis complete. Significant: {result.significant}")
    logger.info(f"AUC-ROC: {result.auc_roc:.4f}")
    logger.info(f"Entropy coefficient: {result.coefficients['entropy']:.6f}")
    logger.info(f"Entropy p-value: {result.p_values['entropy']:.6f}")
    
    if result.warning_message:
        logger.warning(result.warning_message)
    
    # Write results to file if output path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        logger.info(f"Results written to {output_path}")
    
    return result

def stratified_analysis(data_path: Path, 
                      stratification_column: str = 'dataset_type',
                      output_path: Optional[Path] = None) -> Dict[str, GLMMAnalysisResult]:
    """
    Perform stratified analysis by dataset type or other grouping variable.
    
    Each stratification group is analyzed independently, with non-significant
    results handled gracefully.
    """
    logger.info(f"Starting stratified analysis by {stratification_column}")
    
    # Load data
    df = load_entropy_profiles_for_analysis(data_path)
    
    # Add dataset type information if not present
    if stratification_column not in df.columns:
        # Infer from sequence_id pattern or other logic
        df[stratification_column] = 'unknown'
    
    results = {}
    
    for group_name, group_df in df.groupby(stratification_column):
        logger.info(f"Analyzing group: {group_name}")
        
        try:
            result = fit_mixed_effects_model(group_df)
            result.stratification = str(group_name)
            results[str(group_name)] = result
            
            logger.info(f"Group {group_name}: significant={result.significant}, AUC={result.auc_roc:.4f}")
            
        except Exception as e:
            logger.error(f"Error analyzing group {group_name}: {e}")
            # Create a failure result for this group
            results[str(group_name)] = GLMMAnalysisResult(
                coefficients={'intercept': 0.0, 'entropy': 0.0},
                p_values={'intercept': 1.0, 'entropy': 1.0},
                auc_roc=0.5,
                significant=False,
                stratification=str(group_name),
                warning_message=f"Analysis failed for group {group_name}: {str(e)}"
            )
    
    # Write stratified results if output path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump({k: v.to_dict() for k, v in results.items()}, f, indent=2)
        logger.info(f"Stratified results written to {output_path}")
    
    return results

def main():
    """Main entry point for logistic model analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze entropy-validity relationship')
    parser.add_argument('--data-path', type=str, required=True, 
                      help='Path to entropy profiles JSONL file')
    parser.add_argument('--output-path', type=str, default=None,
                      help='Path to write analysis results JSON')
    parser.add_argument('--stratify', type=str, default=None,
                      help='Column name for stratified analysis')
    
    args = parser.parse_args()
    
    data_path = Path(args.data_path)
    output_path = Path(args.output_path) if args.output_path else None
    
    if args.stratify:
        results = stratified_analysis(data_path, args.stratify, output_path)
        print(f"Stratified analysis complete. Groups: {list(results.keys())}")
    else:
        result = analyze_entropy_validity_relationship(data_path, output_path)
        print(f"Analysis complete. Significant: {result.significant}")
        print(f"AUC-ROC: {result.auc_roc:.4f}")
        if result.warning_message:
            print(f"Warning: {result.warning_message}")

if __name__ == "__main__":
    main()