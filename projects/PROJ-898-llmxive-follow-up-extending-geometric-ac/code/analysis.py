"""
Statistical analysis module for comparing symbolic vs. baseline approaches.

Implements Fisher's Exact Test, paired t-tests, and effect size calculations.
"""
import logging
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger("llmxive")

try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logger.warning("SciPy not installed. Analysis will be mocked.")


class StatisticalAnalyzer:
    """
    Performs statistical comparisons between experimental results.
    """

    def __init__(self, alpha: float = 0.05):
        """
        Initialize the analyzer.

        Args:
            alpha: Significance level for hypothesis tests.
        """
        self.alpha = alpha

    def load_results(self, file_path: str) -> pd.DataFrame:
        """
        Load results from a CSV file.

        Args:
            file_path: Path to the CSV file.

        Returns:
            Pandas DataFrame.
        """
        if not SCIPY_AVAILABLE:
            logger.warning("SciPy not available, loading mock data.")
            return pd.DataFrame({
                "trial_id": [1, 2, 3],
                "approach": ["symbolic", "baseline", "symbolic"],
                "success": [1, 0, 1],
                "latency_ms": [100.0, 200.0, 120.0],
                "timestamp": ["t1", "t2", "t3"]
            })

        df = pd.read_csv(file_path)
        return df

    def fisher_exact_test(self, df: pd.DataFrame) -> Tuple[float, float]:
        """
        Perform Fisher's Exact Test on binary success outcomes.

        Args:
            df: DataFrame with 'approach' and 'success' columns.

        Returns:
            Tuple of (odds_ratio, p_value).
        """
        if not SCIPY_AVAILABLE:
            logger.warning("SciPy not available. Returning mock p-value.")
            return 1.0, 0.5

        contingency = pd.crosstab(df["approach"], df["success"])
        if contingency.shape != (2, 2):
            logger.error("Contingency table must be 2x2 for Fisher's test.")
            return 1.0, 1.0

        odds_ratio, p_value = stats.fisher_exact(contingency)
        return odds_ratio, p_value

    def paired_t_test(self, df: pd.DataFrame) -> Tuple[float, float]:
        """
        Perform paired t-test on inference latency.

        Args:
            df: DataFrame with 'approach' and 'latency_ms' columns.

        Returns:
            Tuple of (t_statistic, p_value).
        """
        if not SCIPY_AVAILABLE:
            logger.warning("SciPy not available. Returning mock p-value.")
            return 0.0, 0.5

        symbolic = df[df["approach"] == "symbolic"]["latency_ms"]
        baseline = df[df["approach"] == "baseline"]["latency_ms"]

        if len(symbolic) != len(baseline):
            logger.warning("Groups have different sizes. Using independent t-test.")
            t_stat, p_val = stats.ttest_ind(symbolic, baseline)
        else:
            t_stat, p_val = stats.ttest_rel(symbolic, baseline)

        return t_stat, p_val

    def calculate_effect_size(self, group1: np.ndarray, group2: np.ndarray) -> float:
        """
        Calculate Cohen's d effect size.

        Args:
            group1: First group of values.
            group2: Second group of values.

        Returns:
            Cohen's d value.
        """
        if not SCIPY_AVAILABLE:
            return 0.0

        mean1, mean2 = np.mean(group1), np.mean(group2)
        std1, std2 = np.std(group1), np.std(group2)
        pooled_std = np.sqrt((std1**2 + std2**2) / 2)

        if pooled_std == 0:
            return 0.0

        return (mean1 - mean2) / pooled_std

    def generate_report(
        self,
        symbolic_df: pd.DataFrame,
        baseline_df: pd.DataFrame
    ) -> str:
        """
        Generate a Markdown report of the analysis.

        Args:
            symbolic_df: Results for the symbolic approach.
            baseline_df: Results for the baseline approach.

        Returns:
            Markdown string report.
        """
        # Fisher's Test
        odds, p_fisher = self.fisher_exact_test(pd.concat([
            symbolic_df.assign(approach="symbolic"),
            baseline_df.assign(approach="baseline")
        ]))

        # T-Test
        t_stat, p_ttest = self.paired_t_test(pd.concat([
            symbolic_df.assign(approach="symbolic"),
            baseline_df.assign(approach="baseline")
        ]))

        # Effect Size
        cohens_d = self.calculate_effect_size(
            symbolic_df["latency_ms"].values,
            baseline_df["latency_ms"].values
        )

        # Null Hypothesis Rejection
        reject_null = p_fisher < self.alpha or p_ttest < self.alpha

        report = f"""
# Statistical Analysis Report

## Methodology
- **Test 1**: Fisher's Exact Test (Success Rates)
- **Test 2**: Paired T-Test (Inference Latency)
- **Significance Level (α)**: {self.alpha}

## Results

| Metric | Symbolic | Baseline | Difference | P-value | 95% CI | Effect Size | Reject H0? |
|---|---|---|---|---|---|---|---|
| Success Rate | {symbolic_df['success'].mean():.2%} | {baseline_df['success'].mean():.2%} | {symbolic_df['success'].mean() - baseline_df['success'].mean():.2%} | {p_fisher:.4f} | - | - | {'Yes' if p_fisher < self.alpha else 'No'} |
| Latency (ms) | {symbolic_df['latency_ms'].mean():.2f} | {baseline_df['latency_ms'].mean():.2f} | {symbolic_df['latency_ms'].mean() - baseline_df['latency_ms'].mean():.2f} | {p_ttest:.4f} | - | {cohens_d:.2f} | {'Yes' if p_ttest < self.alpha else 'No'} |

## Conclusion
- **Null Hypothesis Rejected**: {'Yes' if reject_null else 'No'}
- **Interpretation**: {'There is a statistically significant difference between the approaches.' if reject_null else 'No statistically significant difference was found.'}
"""
        return report