"""
Statistical analysis module for the llmXive follow-up project.

Implements Beta regression of Fidelity Loss on Structural Metrics (FR-006).
Fidelity Loss is defined as (1 - CompressedAccuracy) and is strictly bounded in (0, 1).
"""
import os
import json
import sys
import warnings
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.regression.linear_model import WLS
from scipy import stats

from config import get_config


class BetaRegressionAnalyzer:
    """
    Performs Beta regression analysis to model Fidelity Loss as a function of
    Structural Metrics (Sequence Entropy, Tool Repetition Frequency, Argument Variance).
    
    Fidelity Loss = 1 - CompressedAccuracy
    
    Since Fidelity Loss is a proportion bounded in (0, 1), Beta regression is the
    appropriate statistical model.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.results: Optional[Any] = None
        self.df: Optional[pd.DataFrame] = None
        self.model: Optional[Any] = None
        self.summary: Dict[str, Any] = {}

    def load_data(self, metrics_path: str, scores_path: str) -> pd.DataFrame:
        """
        Load and merge structural metrics with compressibility scores.
        
        Args:
            metrics_path: Path to feature_matrix.csv
            scores_path: Path to per_trace_scores.csv
            
        Returns:
            Merged DataFrame ready for analysis
        """
        # Load structural metrics
        metrics_df = pd.read_csv(metrics_path)
        
        # Load compressibility scores and fidelity data
        scores_df = pd.read_csv(scores_path)
        
        # Merge on trace_id
        self.df = pd.merge(
            metrics_df,
            scores_df,
            on='trace_id',
            how='inner'
        )
        
        # Calculate Fidelity Loss: 1 - CompressedAccuracy
        # Ensure CompressedAccuracy is in (0, 1)
        if 'compressed_accuracy' in self.df.columns:
            self.df['fidelity_loss'] = 1.0 - self.df['compressed_accuracy']
        elif 'fidelity_loss' in self.df.columns:
            # Already computed
            pass
        else:
            raise ValueError(
                "Neither 'compressed_accuracy' nor 'fidelity_loss' found in scores data. "
                "Ensure T026 has been completed successfully."
            )
        
        # Handle edge cases: Beta regression requires values strictly in (0, 1)
        # Apply a small transformation to push values away from boundaries
        epsilon = 1e-6
        self.df['fidelity_loss'] = self.df['fidelity_loss'].clip(epsilon, 1 - epsilon)
        
        return self.df

    def prepare_variables(self, 
                        predictor_cols: List[str], 
                        target_col: str = 'fidelity_loss') -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare predictor and target variables for regression.
        
        Args:
            predictor_cols: List of structural metric column names
            target_col: Name of the fidelity loss column
            
        Returns:
            Tuple of (X, y) arrays
        """
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        # Ensure all predictor columns exist
        missing_cols = [col for col in predictor_cols if col not in self.df.columns]
        if missing_cols:
            raise ValueError(f"Missing predictor columns: {missing_cols}")
        
        X = self.df[predictor_cols].values
        y = self.df[target_col].values
        
        # Add constant for intercept
        X = sm.add_constant(X)
        
        return X, y

    def run_beta_regression(self, 
                          predictor_cols: List[str], 
                          target_col: str = 'fidelity_loss') -> Dict[str, Any]:
        """
        Run Beta regression of Fidelity Loss on Structural Metrics.
        
        Note: Since statsmodels doesn't have native Beta regression in all versions,
        we use GLM with Beta family if available, or fall back to transformed OLS.
        
        Args:
            predictor_cols: Structural metrics to use as predictors
            target_col: Fidelity loss column name
            
        Returns:
            Dictionary containing regression results and summary statistics
        """
        X, y = self.prepare_variables(predictor_cols, target_col)
        
        # Try to use Beta regression via GLM if statsmodels supports it
        try:
            from statsmodels.genmod.generalized_linear_model import GLM
            from statsmodels.genmod import families
            
            # Beta distribution for GLM
            # Note: This requires statsmodels >= 0.12
            model = GLM(y, X, family=families.Beta())
            results = model.fit()
            
            self.results = results
            self.model = model
            
            # Extract coefficients and p-values
            summary = {
                'method': 'GLM_Beta',
                'coefficients': dict(zip(predictor_cols + ['const'], results.params)),
                'p_values': dict(zip(predictor_cols + ['const'], results.pvalues)),
                'deviance': results.deviance,
                'pearson_chi2': results.pearson_chi2,
                'aic': results.aic,
                'bic': results.bic,
                'n_obs': results.nobs,
                'converged': results.converged
            }
            
            self.summary = summary
            return summary
            
        except (ImportError, AttributeError) as e:
            # Fallback: Use transformed OLS with logit transformation
            # This is a common approximation when Beta GLM is not available
            warnings.warn(
                f"Beta GLM not available ({e}), using logit-transformed OLS approximation. "
                "Install statsmodels>=0.12 for native Beta regression."
            )
            
            # Apply logit transformation to y
            y_transformed = np.log(y / (1 - y))
            
            model = WLS(y_transformed, X)
            results = model.fit()
            
            self.results = results
            self.model = model
            
            summary = {
                'method': 'WLS_LogitApprox',
                'coefficients': dict(zip(predictor_cols + ['const'], results.params)),
                'p_values': dict(zip(predictor_cols + ['const'], results.pvalues)),
                'r_squared': results.rsquared,
                'adj_r_squared': results.rsquared_adj,
                'f_pvalue': results.f_pvalue,
                'aic': results.aic,
                'bic': results.bic,
                'n_obs': results.nobs,
                'converged': True
            }
            
            self.summary = summary
            return summary

    def run_spearman_correlation(self, 
                               predictor_cols: List[str], 
                               target_col: str = 'fidelity_loss') -> Dict[str, Any]:
        """
        Calculate Spearman rank correlations between structural metrics and fidelity loss.
        
        Args:
            predictor_cols: Structural metric columns
            target_col: Fidelity loss column
            
        Returns:
            Dictionary of correlation coefficients and p-values
        """
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        correlations = {}
        
        for col in predictor_cols:
            if col in self.df.columns:
                corr, pval = stats.spearmanr(
                    self.df[col].dropna(),
                    self.df[target_col].dropna()
                )
                correlations[col] = {
                    'spearman_rho': corr,
                    'p_value': pval
                }
        
        return correlations

    def generate_report(self, output_path: str) -> None:
        """
        Save regression results to a JSON file.
        
        Args:
            output_path: Path to save the results JSON
        """
        if not self.summary:
            raise ValueError("No regression results available. Run run_beta_regression() first.")
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        report = {
            'analysis_type': 'Beta_Regression_Fidelity_Loss',
            'description': 'Regression of Fidelity Loss (1 - CompressedAccuracy) on Structural Metrics',
            'config': self.config,
            'summary': self.summary,
            'data_info': {
                'n_samples': len(self.df) if self.df is not None else 0,
                'columns': list(self.df.columns) if self.df is not None else []
            }
        }
        
        # Add correlation results if available
        if hasattr(self, '_correlations'):
            report['correlations'] = self._correlations
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

    def print_summary(self) -> None:
        """Print a formatted summary of the regression results."""
        if not self.summary:
            print("No regression results available.")
            return
        
        print("\n" + "="*60)
        print("BETA REGRESSION ANALYSIS: FIDELITY LOSS vs STRUCTURAL METRICS")
        print("="*60)
        print(f"Method: {self.summary['method']}")
        print(f"Observations: {self.summary['n_obs']}")
        print(f"Converged: {self.summary.get('converged', 'N/A')}")
        print("-"*60)
        print("Coefficients:")
        
        for var, coef in self.summary['coefficients'].items():
            pval = self.summary['p_values'].get(var, 'N/A')
            sig = "***" if pval < 0.001 else "**" if pval < 0.01 else "*" if pval < 0.05 else ""
            print(f"  {var:30s}: {coef:10.4f} (p={pval:.4f}) {sig}")
        
        print("-"*60)
        if 'deviance' in self.summary:
            print(f"Deviance: {self.summary['deviance']:.4f}")
            print(f"Pearson Chi2: {self.summary['pearson_chi2']:.4f}")
        if 'r_squared' in self.summary:
            print(f"R-squared: {self.summary['r_squared']:.4f}")
            print(f"Adj R-squared: {self.summary['adj_r_squared']:.4f}")
        
        print("="*60 + "\n")


def run_beta_regression_analysis(
    metrics_path: str,
    scores_path: str,
    output_path: str,
    predictor_cols: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Main function to run the complete Beta regression analysis.
    
    Args:
        metrics_path: Path to feature_matrix.csv
        scores_path: Path to per_trace_scores.csv
        output_path: Path to save results JSON
        predictor_cols: List of structural metrics to use (default: all available)
        
    Returns:
        Dictionary containing analysis results
    """
    config = get_config()
    analyzer = BetaRegressionAnalyzer(config)
    
    # Load and prepare data
    df = analyzer.load_data(metrics_path, scores_path)
    
    # Determine predictor columns
    if predictor_cols is None:
        # Default structural metrics
        predictor_cols = [
            'sequence_entropy',
            'tool_repetition_frequency',
            'argument_variance'
        ]
        # Filter to only columns that exist
        predictor_cols = [col for col in predictor_cols if col in df.columns]
    
    if not predictor_cols:
        raise ValueError("No valid predictor columns found in the data.")
    
    # Run Beta regression
    regression_results = analyzer.run_beta_regression(predictor_cols)
    
    # Run Spearman correlation
    correlations = analyzer.run_spearman_correlation(predictor_cols)
    analyzer._correlations = correlations
    
    # Generate report
    analyzer.generate_report(output_path)
    
    # Print summary
    analyzer.print_summary()
    
    return {
        'regression': regression_results,
        'correlations': correlations,
        'output_file': output_path
    }


def main():
    """Main entry point for the stats analysis script."""
    config = get_config()
    
    # Define paths
    metrics_path = config.get('paths', {}).get('feature_matrix', 'data/processed/feature_matrix.csv')
    scores_path = config.get('paths', {}).get('per_trace_scores', 'data/processed/per_trace_scores.csv')
    output_path = config.get('paths', {}).get('stats_results', 'data/processed/beta_regression_results.json')
    
    print(f"Loading data from: {metrics_path}, {scores_path}")
    
    try:
        results = run_beta_regression_analysis(
            metrics_path=metrics_path,
            scores_path=scores_path,
            output_path=output_path
        )
        
        print(f"\nAnalysis complete. Results saved to: {output_path}")
        
        # Return exit code 0 on success
        return 0
        
    except FileNotFoundError as e:
        print(f"ERROR: Required data file not found: {e}")
        print("Ensure T022 (feature_matrix.csv) and T026 (per_trace_scores.csv) are completed first.")
        return 1
    except Exception as e:
        print(f"ERROR: Analysis failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())