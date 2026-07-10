import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Any, List, Optional
from utils.logger import get_logger
import os

logger = get_logger(__name__)

class StatUtils:
    """
    Utility class for statistical analysis methods required by the study.
    """

    @staticmethod
    def shapiro_wilk(data: pd.Series) -> Dict[str, float]:
        """
        Perform Shapiro-Wilk normality test.

        Args:
            data: Series of difference scores.

        Returns:
            Dict with 'statistic' and 'pvalue'.
        """
        if len(data) < 3:
            logger.warning("Shapiro-Wilk requires at least 3 samples.")
            return {"statistic": np.nan, "pvalue": np.nan}

        stat, p_value = stats.shapiro(data)
        return {"statistic": float(stat), "pvalue": float(p_value)}

    @staticmethod
    def repeated_measures_anova(df: pd.DataFrame, 
                                within_subject_col: str, 
                                between_subject_col: str, 
                                value_col: str) -> Dict[str, Any]:
        """
        Perform Repeated Measures ANOVA using pingouin-style logic 
        but implemented with scipy/numpy to avoid extra dependencies.
        
        Note: For a true repeated measures ANOVA, we typically need
        the 'pingouin' library. Since we are constrained to scipy/stats,
        we will implement a simplified version or use a paired t-test
        approach if only two conditions exist (Traditional vs Explainable).
        
        Given the study design (Traditional vs Explainable), we have exactly
        2 conditions. Therefore, a Paired T-Test on the difference is 
        statistically equivalent to a 1-way Repeated Measures ANOVA with 2 levels.
        
        However, to satisfy the task requirement of "Repeated Measures ANOVA",
        we will attempt to use scipy's f_oneway if we treat it as independent
        (which is incorrect for within-subjects) OR we will calculate the 
        F-statistic manually for the 2-level case.
        
        For 2 levels: F = t^2 where t is the paired t-statistic.
        
        Args:
            df: DataFrame with columns for subject, condition, and value.
            within_subject_col: Column name for the condition (e.g., 'interface_type').
            between_subject_col: Column name for the participant ID.
            value_col: Column name for the metric.
        
        Returns:
            Dict with 'F', 'p_value', 'dof', 'dof_error', 'ss_between', 'ss_within'.
        """
        # Pivot to wide format for paired test
        wide_df = df.pivot_table(
            index=between_subject_col, 
            columns=within_subject_col, 
            values=value_col
        )
        
        # Drop rows with missing data in either condition
        wide_df = wide_df.dropna()
        
        if wide_df.shape[0] < 2:
            logger.error("Not enough participants with complete data for ANOVA.")
            return {
                "F": np.nan, "p_value": np.nan, "dof": np.nan, 
                "dof_error": np.nan, "ss_between": np.nan, "ss_within": np.nan,
                "method": "insufficient_data"
            }
        
        # Extract the two columns (assuming exactly two conditions)
        if wide_df.shape[1] != 2:
            # Fallback for >2 conditions would require a more complex manual implementation
            # or external library. For this study, we expect 2.
            logger.warning(f"Expected 2 conditions, found {wide_df.shape[1]}. Using t-test logic for 2 groups only.")
            # If somehow more, we can't easily do RM-ANOVA with just scipy without complex matrix math.
            # We will assume 2 for this specific task context.
            return {
                "F": np.nan, "p_value": np.nan, "dof": np.nan, 
                "dof_error": np.nan, "ss_between": np.nan, "ss_within": np.nan,
                "method": "unsupported_levels"
            }

        col1, col2 = wide_df.columns
        x = wide_df[col1].values
        y = wide_df[col2].values

        # Paired t-test
        t_stat, p_val = stats.ttest_rel(x, y)
        
        # For 2 conditions, F = t^2
        f_stat = t_stat ** 2
        
        # Degrees of freedom
        n = len(x)
        dof = 1  # k - 1 where k=2
        dof_error = n - 1
        
        # Sum of Squares (simplified for 2 groups)
        # SS_total = sum((x - grand_mean)^2) + ...
        # SS_between = n * sum((group_mean - grand_mean)^2)
        # SS_within = SS_total - SS_between
        
        grand_mean = np.mean(np.concatenate([x, y]))
        mean1, mean2 = np.mean(x), np.mean(y)
        
        ss_between = n * ((mean1 - grand_mean)**2 + (mean2 - grand_mean)**2)
        
        # SS_within is the sum of squared deviations within each group from their mean
        ss_within = np.sum((x - mean1)**2) + np.sum((y - mean2)**2)
        
        return {
            "F": float(f_stat),
            "p_value": float(p_val),
            "dof": int(dof),
            "dof_error": int(dof_error),
            "ss_between": float(ss_between),
            "ss_within": float(ss_within),
            "method": "paired_t_squared"
        }

    @staticmethod
    def holm_bonferroni(p_values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
        """
        Apply Holm-Bonferroni correction for multiple comparisons.
        
        The Holm-Bonferroni method is a step-down procedure that is 
        more powerful than the standard Bonferroni correction.
        
        Steps:
        1. Sort p-values in ascending order.
        2. For the i-th smallest p-value (i=1 to m), compare to alpha / (m - i + 1).
        3. If p_i > alpha / (m - i + 1), stop; all remaining are non-significant.
        4. Otherwise, reject the null hypothesis for this test.
        
        Args:
            p_values: List of raw p-values from statistical tests.
            alpha: Significance level (default 0.05).
        
        Returns:
            Dict containing:
            - 'adjusted_p_values': List of adjusted p-values (or bounds).
            - 'significant': List of booleans indicating significance.
            - 'method': 'holm_bonferroni'
        """
        if not p_values:
            return {
                "adjusted_p_values": [],
                "significant": [],
                "method": "holm_bonferroni"
            }

        m = len(p_values)
        
        # Create a list of (original_index, p_value)
        indexed_p_values = list(enumerate(p_values))
        
        # Sort by p-value
        sorted_p_values = sorted(indexed_p_values, key=lambda x: x[1])
        
        adjusted_p_values = [0.0] * m
        significant = [False] * m
        
        # Calculate adjusted p-values
        # The adjusted p-value for the i-th sorted p-value is max( (m-i+1)*p_i, adjusted_p_{i-1} )
        # But for the boolean decision, we can just use the threshold comparison.
        
        # We need to map back to original order for the return
        # Let's compute the adjusted p-values first
        
        # Step 1: Sort
        sorted_indices = [i for i, p in sorted_p_values]
        sorted_vals = [p for i, p in sorted_p_values]
        
        # Step 2: Compute adjusted p-values (monotonicity constraint)
        # Holm's adjusted p-value for rank i (1-based) is (m - i + 1) * p_i
        # But must be non-decreasing.
        
        adj_vals = []
        current_max = 0.0
        
        for i, p in enumerate(sorted_vals):
            # i is 0-based rank. Rank in formula is i+1.
            # Factor = m - (i+1) + 1 = m - i
            factor = m - i
            adj_p = p * factor
            if adj_p > 1.0:
                adj_p = 1.0
            if adj_p < current_max:
                adj_p = current_max
            current_max = adj_p
            adj_vals.append(adj_p)
        
        # Map back to original order
        final_adj_p = [0.0] * m
        final_sig = [False] * m
        
        for idx, adj_p in zip(sorted_indices, adj_vals):
            final_adj_p[idx] = adj_p
            final_sig[idx] = adj_p < alpha
        
        return {
            "adjusted_p_values": final_adj_p,
            "significant": final_sig,
            "method": "holm_bonferroni"
        }

    @staticmethod
    def calculate_effect_size_r_squared(ss_between: float, ss_within: float) -> float:
        """
        Calculate partial eta-squared (effect size) for ANOVA.
        eta^2 = SS_between / (SS_between + SS_within)
        """
        if ss_within + ss_between == 0:
            return 0.0
        return ss_between / (ss_between + ss_within)

def main():
    """
    Main entry point for testing statistical utilities.
    """
    logger.info("Running StatUtils main() for demonstration.")
    
    # Example usage of Holm-Bonferroni
    sample_p_values = [0.001, 0.02, 0.04, 0.06, 0.10]
    result = StatUtils.holm_bonferroni(sample_p_values)
    
    logger.info(f"Raw p-values: {sample_p_values}")
    logger.info(f"Adjusted p-values: {result['adjusted_p_values']}")
    logger.info(f"Significant (alpha=0.05): {result['significant']}")
    
    # Example usage of ANOVA
    # Create dummy data
    data = {
        'participant_id': [1, 2, 3, 4, 5],
        'interface_type': ['Traditional', 'Explainable', 'Traditional', 'Explainable', 'Traditional'],
        'completion_time': [10, 8, 12, 9, 11] * 2 # Simplified
    }
    # Re-construct for proper wide format
    df = pd.DataFrame({
        'participant_id': [1, 1, 2, 2, 3, 3],
        'interface_type': ['Traditional', 'Explainable'] * 3,
        'value': [10, 8, 12, 9, 11, 10]
    })
    
    anova_res = StatUtils.repeated_measures_anova(
        df, 
        within_subject_col='interface_type', 
        between_subject_col='participant_id', 
        value_col='value'
    )
    
    logger.info(f"ANOVA Result: {anova_res}")

if __name__ == "__main__":
    main()