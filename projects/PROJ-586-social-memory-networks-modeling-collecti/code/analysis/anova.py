"""
ANOVA analysis module for social memory network experiments.

Implements two-way ANOVA with Context × Metric factors and Bonferroni correction
for family-wise error rate control.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, asdict
from pathlib import Path
import sys
from scipy import stats

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

@dataclass
class ANOVAOutput:
    """
    Container for ANOVA analysis results including Bonferroni-corrected values.
    
    Attributes:
        f_statistic: F-statistic value from ANOVA
        p_value: Raw p-value from ANOVA
        p_value_corrected: Bonferroni-corrected p-value
        alpha: Original significance level
        alpha_corrected: Bonferroni-corrected significance level
        degrees_of_freedom: Tuple of (df_between, df_within)
        effect_size: Partial eta-squared effect size
        significant: Whether result is significant at corrected alpha
        test_count: Number of tests in family for Bonferroni correction
        summary: Human-readable summary string
    """
    f_statistic: float
    p_value: float
    p_value_corrected: float
    alpha: float
    alpha_corrected: float
    degrees_of_freedom: Tuple[int, int]
    effect_size: float
    significant: bool
    test_count: int
    summary: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

def load_experiment_results(results_dir: Path) -> pd.DataFrame:
    """
    Load experiment results from CSV files.
    
    Args:
        results_dir: Path to directory containing results CSV files
        
    Returns:
        Combined DataFrame with all experiment results
    """
    all_results = []
    
    # Look for both full and limited context results
    for csv_file in results_dir.glob("results_*.csv"):
        df = pd.read_csv(csv_file)
        all_results.append(df)
    
    if not all_results:
        raise FileNotFoundError(f"No results CSV files found in {results_dir}")
    
    combined = pd.concat(all_results, ignore_index=True)
    return combined
    
def prepare_data_for_anova(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare data for two-way ANOVA with Context × Metric factors.
    
    Args:
        df: DataFrame with experiment results
        
    Returns:
        Melted DataFrame ready for ANOVA with columns:
        - context_condition: The context condition (full/limited)
        - metric_type: The metric type (specialization/retrieval)
        - value: The metric value
    """
    # Filter to required columns
    required_cols = ['context_condition', 'specialization_index', 'retrieval_efficiency']
    available_cols = [c for c in required_cols if c in df.columns]
    
    if len(available_cols) < 2:
        raise ValueError(f"DataFrame missing required columns. Found: {df.columns.tolist()}")
    
    # Melt to long format for two-way ANOVA
    melted = df.melt(
        id_vars=['context_condition'],
        value_vars=['specialization_index', 'retrieval_efficiency'],
        var_name='metric_type',
        value_name='value'
    )
    
    return melted
    
def compute_two_way_anova(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute two-way ANOVA with Context × Metric interaction.
    
    Args:
        df: Melted DataFrame from prepare_data_for_anova
        
    Returns:
        Dictionary with ANOVA results
    """
    # Create pivot table for ANOVA
    pivot = df.pivot_table(
        values='value',
        index='context_condition',
        columns='metric_type',
        aggfunc='mean'
    )
    
    # Perform two-way ANOVA using scipy
    # We need to reshape data for stats.anova_lm
    from statsmodels.stats.anova import AnovaRM
    
    model = AnovaRM(df, 'value', 'context_condition', within=['metric_type'])
    result = model.fit()
    
    # Extract F-statistic and p-value for main effects and interaction
    anova_table = result.anova_table
    
    # Get the interaction term p-value (most important for this analysis)
    interaction_p = None
    interaction_f = None
    
    for idx in anova_table.index:
        if 'context_condition:metric_type' in str(idx) or 'C(metric_type):C(context_condition)' in str(idx):
            interaction_p = float(anova_table.loc[idx, 'PR(>F)'])
            interaction_f = float(anova_table.loc[idx, 'F value'])
            break
    
    # If interaction not found, use first available p-value
    if interaction_p is None:
        interaction_p = float(anova_table.iloc[0]['PR(>F)'])
        interaction_f = float(anova_table.iloc[0]['F value'])
    
    return {
        'f_statistic': interaction_f,
        'p_value': interaction_p,
        'anova_table': anova_table
    }
    
def apply_bonferroni_correction(p_value: float, test_count: int, alpha: float = 0.05) -> Tuple[float, float, bool]:
    """
    Apply Bonferroni correction for family-wise error rate control.
    
    The Bonferroni correction divides the significance level by the number
    of tests to maintain the overall Type I error rate.
    
    Args:
        p_value: Raw p-value from hypothesis test
        test_count: Number of tests in the family
        alpha: Original significance level (default 0.05)
        
    Returns:
        Tuple of (corrected_p_value, corrected_alpha, is_significant)
    """
    if test_count < 1:
        raise ValueError("test_count must be at least 1")
    
    # Bonferroni-corrected alpha
    alpha_corrected = alpha / test_count
    
    # Bonferroni-corrected p-value (multiply by number of tests)
    p_value_corrected = min(p_value * test_count, 1.0)
    
    # Check significance with corrected alpha
    is_significant = p_value < alpha_corrected
    
    return p_value_corrected, alpha_corrected, is_significant
    
def run_anova_analysis(df: pd.DataFrame, alpha: float = 0.05) -> ANOVAOutput:
    """
    Run complete ANOVA analysis with Bonferroni correction.
    
    For this experiment, we test:
    - Main effect of Context (full vs limited)
    - Main effect of Metric (specialization vs retrieval)  
    - Interaction effect (Context × Metric)
    
    This gives us 3 hypothesis tests, so we apply Bonferroni correction
    with test_count=3.
    
    Args:
        df: Melted DataFrame from prepare_data_for_anova
        alpha: Significance level (default 0.05)
        
    Returns:
        ANOVAOutput with all results and Bonferroni-corrected values
    """
    # Compute two-way ANOVA
    anova_results = compute_two_way_anova(df)
    
    # Number of hypothesis tests (main effects + interaction)
    test_count = 3
    
    # Apply Bonferroni correction
    p_corrected, alpha_corrected, significant = apply_bonferroni_correction(
        anova_results['p_value'],
        test_count,
        alpha
    )
    
    # Calculate effect size (partial eta-squared)
    f_stat = anova_results['f_statistic']
    df_between, df_within = 1, len(df) - 2  # Simplified degrees of freedom
    effect_size = (f_stat * df_between) / (f_stat * df_between + df_within)
    
    # Generate summary
    summary = (
        f"Two-way ANOVA with Bonferroni correction (α={alpha}, "
        f"m={test_count} tests):\n"
        f"  F({df_between}, {df_within}) = {f_stat:.4f}\n"
        f"  Raw p = {anova_results['p_value']:.6f}\n"
        f"  Bonferroni-corrected α = {alpha_corrected:.6f}\n"
        f"  Bonferroni-corrected p = {p_corrected:.6f}\n"
        f"  Effect size (η²) = {effect_size:.4f}\n"
        f"  Significant at corrected α: {'Yes' if significant else 'No'}"
    )
    
    return ANOVAOutput(
        f_statistic=f_stat,
        p_value=anova_results['p_value'],
        p_value_corrected=p_corrected,
        alpha=alpha,
        alpha_corrected=alpha_corrected,
        degrees_of_freedom=(df_between, df_within),
        effect_size=effect_size,
        significant=significant,
        test_count=test_count,
        summary=summary
    )
    
def main(results_dir: str = "projects/PROJ-586-social-memory-networks-modeling-collecti/results",
         output_dir: str = "projects/PROJ-586-social-memory-networks-modeling-collecti/results",
         alpha: float = 0.05) -> ANOVAOutput:
    """
    Main entry point for ANOVA analysis with Bonferroni correction.
    
    Loads experiment results, performs two-way ANOVA, applies Bonferroni
    correction, and returns comprehensive results.
    
    Args:
        results_dir: Path to directory with results CSV files
        output_dir: Path to directory for output files
        alpha: Significance level for hypothesis testing
        
    Returns:
        ANOVAOutput with analysis results
    """
    results_path = Path(results_dir)
    output_path = Path(output_dir)
    
    # Ensure output directory exists
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load and prepare data
    df = load_experiment_results(results_path)
    df_melted = prepare_data_for_anova(df)
    
    # Run analysis
    output = run_anova_analysis(df_melted, alpha)
    
    # Save results to JSON
    import json
    output_file = output_path / "anova_results_bonferroni.json"
    with open(output_file, 'w') as f:
        json.dump(output.to_dict(), f, indent=2)
    
    # Save summary to text file
    summary_file = output_path / "anova_summary_bonferroni.txt"
    with open(summary_file, 'w') as f:
        f.write(output.summary)
    
    print(f"ANOVA analysis complete with Bonferroni correction")
    print(f"  Corrected α = {output.alpha_corrected:.6f}")
    print(f"  Test count = {output.test_count}")
    print(f"  Results saved to {output_path}")
    
    return output
