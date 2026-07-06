"""
T029: Calculate individual Pearson correlation coefficients (r) for each descriptor vs. Seebeck.

This script loads the engineered features dataset and computes Pearson correlation
coefficients between each compositional descriptor and the Seebeck coefficient.
Results are saved to data/processed/correlations.csv.
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Ensure the code directory is in the path for imports
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils.periodic_data import get_element, get_atomic_radius, get_electronegativity, get_valence_electrons, get_atomic_number


def load_engineered_data(filepath: str) -> pd.DataFrame:
    """Load the engineered features dataset."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Engineered data file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    
    required_cols = ['Seebeck', 'mean_atomic_radius', 'electronegativity_variance', 
                     'vec', 'atomic_number_variance', 'temperature', 'material_family']
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in engineered data: {missing_cols}")
    
    return df


def compute_correlations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Pearson correlation coefficients between each descriptor and Seebeck.
    
    Parameters:
        df: DataFrame with engineered features and Seebeck values
        
    Returns:
        DataFrame with columns: feature, correlation_coefficient, p_value, n_samples
    """
    # Select only numeric columns that are descriptors (not target or categorical)
    descriptor_cols = ['mean_atomic_radius', 'electronegativity_variance', 
                     'vec', 'atomic_number_variance', 'temperature']
    
    correlations = []
    
    for col in descriptor_cols:
        if col not in df.columns:
            continue
        
        # Remove rows with NaN in either the descriptor or Seebeck
        valid_data = df[[col, 'Seebeck']].dropna()
        
        if len(valid_data) < 2:
            # Not enough data points to compute correlation
            correlations.append({
                'feature': col,
                'correlation_coefficient': np.nan,
                'p_value': np.nan,
                'n_samples': len(valid_data)
            })
            continue
        
        # Compute Pearson correlation
        corr_matrix = valid_data[[col, 'Seebeck']].corr()
        r = corr_matrix.loc[col, 'Seebeck']
        
        # Compute p-value for the correlation
        # Using scipy.stats.pearsonr would be ideal, but we'll compute it manually
        # to avoid additional dependencies
        n = len(valid_data)
        if abs(r) >= 1.0:
            # Perfect correlation
            p_value = 0.0 if r != 0 else 1.0
        else:
            # t-statistic for correlation
            t_stat = r * np.sqrt((n - 2) / (1 - r**2))
            # Two-tailed p-value from t-distribution
            # Using scipy if available, otherwise approximate
            try:
                from scipy import stats
                p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))
            except ImportError:
                # Fallback: approximate p-value using normal distribution for large n
                # This is less accurate but avoids hard dependency on scipy
                if n > 30:
                    z = abs(t_stat)
                    p_value = 2 * (1 - 0.5 * (1 + np.erf(z / np.sqrt(2))))
                else:
                    # For small samples, use a rough approximation
                    p_value = 1.0 / (1 + abs(t_stat))
        
        correlations.append({
            'feature': col,
            'correlation_coefficient': r,
            'p_value': p_value,
            'n_samples': n
        })
    
    return pd.DataFrame(correlations)


def save_correlations(correlations_df: pd.DataFrame, output_path: str):
    """Save correlation results to CSV."""
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    correlations_df.to_csv(output_path, index=False)
    print(f"Correlations saved to: {output_path}")


def main():
    """Main entry point for the correlation computation task."""
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    input_path = project_root / 'data' / 'processed' / 'final_features.csv'
    output_path = project_root / 'data' / 'processed' / 'correlations.csv'
    
    print(f"Loading engineered data from: {input_path}")
    
    try:
        df = load_engineered_data(str(input_path))
        print(f"Loaded {len(df)} records")
        
        print("Computing Pearson correlations...")
        correlations_df = compute_correlations(df)
        
        print("\nCorrelation Results:")
        print(correlations_df.to_string(index=False))
        
        save_correlations(correlations_df, str(output_path))
        
        # Also save a summary to JSON for easy parsing
        summary = {
            'total_features': len(correlations_df),
            'significant_correlations': int((correlations_df['p_value'] < 0.05).sum()),
            'correlations': correlations_df.to_dict('records')
        }
        
        json_output_path = str(output_path).replace('.csv', '_summary.json')
        with open(json_output_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"\nSummary saved to: {json_output_path}")
        
        print("\nTask T029 completed successfully.")
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
