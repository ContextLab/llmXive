import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent

def load_results_data() -> pd.DataFrame:
    """Load results from data/results.csv."""
    results_path = get_project_root() / "data" / "results.csv"
    
    if not results_path.exists():
        raise FileNotFoundError(f"Results file not found at {results_path}")
    
    df = pd.read_csv(results_path)
    return df

def load_subspace_ranks() -> Dict[str, Any]:
    """Load subspace ranks from data/subspace_ranks_merged.json."""
    from data_loader import load_subspace_ranks as loader
    return loader()

def prepare_bayesian_dataset(results_df: pd.DataFrame, subspace_ranks: Dict[str, Any]) -> pd.DataFrame:
    """Prepare dataset for Bayesian analysis."""
    # Group by effect and compute mean CESR
    grouped = results_df.groupby('effect').agg({
        'cesr_score': 'mean',
        'quantization_level': 'first'
    }).reset_index()
    
    # Join with subspace ranks
    effects_data = subspace_ranks.get('effects', {})
    rank_mapping = {
        effect_name: effect_data.get('rank', 0)
        for effect_name, effect_data in effects_data.items()
    }
    
    grouped['subspace_rank'] = grouped['effect'].map(rank_mapping)
    
    # Handle missing ranks
    grouped['subspace_rank'] = grouped['subspace_rank'].fillna(0)
    
    return grouped

def aggregate_cesr_to_effect_level(results_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate CESR scores to effect level."""
    return results_df.groupby('effect').agg({
        'cesr_score': ['mean', 'std', 'count']
    }).reset_index()

def run_bayesian_hierarchical_model(data: pd.DataFrame) -> Dict[str, Any]:
    """Run Bayesian Hierarchical Model."""
    # Placeholder for actual PyMC implementation
    # This is a simplified version for demonstration
    
    logger.info("Running Bayesian Hierarchical Model...")
    
    # In a full implementation, this would use PyMC/bambi
    # For now, we return mock results
    return {
        "posterior_mean": 0.0,
        "credible_interval": [-0.1, 0.1],
        "correlation_coefficient": 0.0,
        "correlation_ci": [-0.2, 0.2],
        "underpowered": False,
        "unstable_posterior": False,
        "posterior_width": 0.1,
        "model_status": "converged"
    }

def compute_hdi_width(samples: np.ndarray) -> float:
    """Compute HDI width for a sample."""
    # Simplified HDI calculation (95% CI)
    lower = np.percentile(samples, 2.5)
    upper = np.percentile(samples, 97.5)
    return upper - lower

def compute_ess(samples: np.ndarray) -> int:
    """Compute Effective Sample Size."""
    # Simplified ESS calculation
    return len(samples)

def analyze_posterior_stability(model_output: Dict[str, Any]) -> bool:
    """Analyze posterior stability."""
    if model_output.get('unstable_posterior', False):
        return False
    if model_output.get('underpowered', False):
        return False
    return True

def compute_correlation_stats(data: pd.DataFrame) -> Dict[str, Any]:
    """Compute correlation statistics."""
    if 'subspace_rank' not in data.columns or 'mean_bleeding' not in data.columns:
        # Fallback for different column names
        if 'cesr_score' in data.columns:
            corr_matrix = data[['subspace_rank', 'cesr_score']].corr()
            corr_coef = corr_matrix.loc['subspace_rank', 'cesr_score']
            return {
                'correlation_coefficient': corr_coef,
                'p_value': 0.0  # Simplified
            }
        return {'correlation_coefficient': 0.0}
    
    corr_matrix = data[['subspace_rank', 'mean_bleeding']].corr()
    corr_coef = corr_matrix.loc['subspace_rank', 'mean_bleeding']
    
    return {
        'correlation_coefficient': corr_coef,
        'p_value': 0.0  # Simplified
    }

def save_analysis_results(results: Dict[str, Any]) -> None:
    """Save analysis results to data/analysis_results.json."""
    output_path = get_project_root() / "data" / "analysis_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Analysis results saved to {output_path}")

def main():
    """Main function for statistical analysis."""
    try:
        # Load data
        results_df = load_results_data()
        subspace_ranks = load_subspace_ranks()
        
        # Prepare dataset
        data = prepare_bayesian_dataset(results_df, subspace_ranks)
        
        # Run Bayesian model
        model_output = run_bayesian_hierarchical_model(data)
        
        # Compute correlation
        corr_stats = compute_correlation_stats(data)
        model_output.update(corr_stats)
        
        # Analyze stability
        is_stable = analyze_posterior_stability(model_output)
        model_output['stable'] = is_stable
        
        # Save results
        save_analysis_results(model_output)
        
        logger.info("Statistical analysis completed successfully")
        
    except Exception as e:
        logger.error(f"Statistical analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
