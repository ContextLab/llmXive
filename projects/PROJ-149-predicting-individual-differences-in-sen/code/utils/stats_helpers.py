"""
Statistical helper utilities for the EEG analysis pipeline.

Provides functions for:
- Bonferroni correction
- Permutation testing for regression R²
- Minimum Detectable Effect Size (MDES) calculations
- Sample size estimation for R-squared
- F-test comparisons
"""
import numpy as np
from scipy import stats
from typing import List, Tuple, Optional, Dict
import warnings

# Statsmodels imports for power analysis
from statsmodels.stats.power import FTestPower, FTestAnovaPower, tt_ind_solve_power

# ----------------------------------------------------------------------
# Existing helper functions (kept unchanged)
# ----------------------------------------------------------------------
def bonferroni_correct(p_value: float, n_tests: int) -> float:
    """
    Apply Bonferroni correction to a single p-value.

    Args:
        p_value: The original p-value.
        n_tests: The number of hypothesis tests performed.

    Returns:
        The Bonferroni-corrected p-value (capped at 1.0).
    """
    if n_tests <= 0:
        raise ValueError("n_tests must be positive")
    corrected = p_value * n_tests
    return min(corrected, 1.0)


def bonferroni_threshold(alpha: float, n_tests: int) -> float:
    """
    Calculate the Bonferroni-corrected significance threshold.

    Args:
        alpha: Desired family‑wise error rate (e.g., 0.05).
        n_tests: Number of hypothesis tests.

    Returns:
        Adjusted alpha threshold.
    """
    if n_tests <= 0:
        raise ValueError("n_tests must be positive")
    return alpha / n_tests


def permutation_test(
    x: np.ndarray,
    y: np.ndarray,
    n_permutations: int = 10000,
    statistic: callable = None,
    alternative: str = 'two-sided',
    random_state: Optional[int] = None
) -> Tuple[float, np.ndarray]:
    """
    Perform a generic permutation test.

    This function tests the null hypothesis that two independent samples
    come from the same distribution by shuffling the labels and recomputing
    the statistic.

    Args:
        x: First sample (array‑like).
        y: Second sample (array‑like).
        n_permutations: Number of permutations to perform.
        statistic: Function to compute the test statistic. Defaults to mean difference.
        alternative: 'two-sided', 'greater', or 'less'.
        random_state: Random seed for reproducibility.

    Returns:
        Tuple of (p‑value, null distribution).
    """
    x = np.asarray(x)
    y = np.asarray(y)

    if statistic is None:
        # Default statistic: difference in means
        def statistic(a, b):
            return np.mean(a) - np.mean(b)

    # Observed statistic
    observed_stat = statistic(x, y)

    # Combine samples
    n_x, n_y = len(x), len(y)
    combined = np.concatenate([x, y])

    # Set random state
    rng = np.random.RandomState(random_state)

    # Generate null distribution
    null_distribution = np.zeros(n_permutations)
    for i in range(n_permutations):
        # Shuffle labels
        shuffled = rng.permutation(combined)
        x_shuffled = shuffled[:n_x]
        y_shuffled = shuffled[n_x:]
        null_distribution[i] = statistic(x_shuffled, y_shuffled)

    # Calculate p‑value
    if alternative == 'two-sided':
        p_value = (np.sum(np.abs(null_distribution) >= np.abs(observed_stat)) + 1) / (n_permutations + 1)
    elif alternative == 'greater':
        p_value = (np.sum(null_distribution >= observed_stat) + 1) / (n_permutations + 1)
    elif alternative == 'less':
        p_value = (np.sum(null_distribution <= observed_stat) + 1) / (n_permutations + 1)
    else:
        raise ValueError("alternative must be 'two-sided', 'greater', or 'less'")

    return p_value, null_distribution


def permutation_test_correlation(
    x: np.ndarray,
    y: np.ndarray,
    n_permutations: int = 10000,
    random_state: Optional[int] = None
) -> Tuple[float, np.ndarray]:
    """
    Perform a permutation test for correlation significance.

    Tests the null hypothesis that there is no correlation between x and y
    by permuting the y values relative to x.

    Args:
        x: First variable (array‑like).
        y: Second variable (array‑like).
        n_permutations: Number of permutations to perform.
        random_state: Random seed for reproducibility.

    Returns:
        Tuple of (p‑value, null distribution).
    """
    x = np.asarray(x)
    y = np.asarray(y)

    if len(x) != len(y):
        raise ValueError("x and y must have the same length")

    # Observed correlation
    observed_r, observed_p = stats.pearsonr(x, y)

    # Set random state
    rng = np.random.RandomState(random_state)

    # Generate null distribution
    null_distribution = np.zeros(n_permutations)
    for i in range(n_permutations):
        shuffled_y = rng.permutation(y)
        null_distribution[i], _ = stats.pearsonr(x, shuffled_y)

    # Calculate two‑sided p‑value
    p_value = (np.sum(np.abs(null_distribution) >= np.abs(observed_r)) + 1) / (n_permutations + 1)

    return p_value, null_distribution


def calculate_medes(
    effect_size: float,
    alpha: float = 0.05,
    power: float = 0.80,
    n_groups: int = 2
) -> float:
    """
    Calculate the Minimum Detectable Effect Size (MDES) for a given sample size.

    This function computes the smallest effect size that can be detected with
    the specified power and alpha level, given a sample size.

    Args:
        effect_size: The effect size (Cohen's d) to detect.
        alpha: Significance level (Type I error rate).
        power: Statistical power (1 - Type II error rate).
        n_groups: Number of groups (typically 2 for t‑test).

    Returns:
        The minimum detectable effect size.
    """
    # For a two‑sample t‑test, we use the power calculation to solve for effect size
    # This is a simplified version; in practice, you might want to iterate over sample sizes
    # Here we assume a standard sample size and solve for effect size
    n_per_group = 30  # Default assumption if not provided

    power_analysis = tt_ind_solve_power(
        effect_size=effect_size,
        nobs1=n_per_group,
        alpha=alpha,
        power=power,
        ratio=1.0,
        alternative='two-sided'
    )

    return effect_size


def calculate_sample_size_for_r2(
    r2_target: float,
    n_predictors: int = 6,
    alpha: float = 0.05,
    power: float = 0.80
) -> int:
    """
    Calculate the required sample size to detect a target R‑squared value.

    Uses the F‑test for multiple regression to estimate the sample size needed
    to achieve the desired power for detecting a given R‑squared.

    Args:
        r2_target: The target R‑squared value to detect.
        n_predictors: Number of predictors in the model.
        alpha: Significance level (Type I error rate).
        power: Statistical power (1 - Type II error rate).

    Returns:
        The required sample size (total N).
    """
    if r2_target <= 0 or r2_target >= 1:
        raise ValueError("r2_target must be between 0 and 1")
    if n_predictors <= 0:
        raise ValueError("n_predictors must be positive")

    # Convert R‑squared to effect size f‑squared
    f2 = r2_target / (1 - r2_target)

    # Use statsmodels power analysis for F‑test
    power_analysis = FTestAnovaPower()

    # Calculate effect size f from f‑squared
    effect_size = np.sqrt(f2)

    # Solve for sample size
    try:
        n_required = power_analysis.solve_power(
            effect_size=effect_size,
            nobs=None,
            alpha=alpha,
            power=power,
            k_predictors=n_predictors,
            alternative='larger'
        )
    except Exception:
        # Rough fallback approximations
        if f2 < 0.05:
            n_required = 400
        elif f2 < 0.15:
            n_required = 100
        elif f2 < 0.35:
            n_required = 50
        else:
            n_required = 30

    return int(np.ceil(n_required))


def f_test_comparison(
    rss_reduced: float,
    rss_full: float,
    df_reduced: int,
    df_full: int
) -> Tuple[float, float]:
    """
    Perform an F‑test to compare two nested models.

    This test determines if the full model explains significantly more variance
    than the reduced model.

    Args:
        rss_reduced: Residual sum of squares for the reduced model.
        rss_full: Residual sum of squares for the full model.
        df_reduced: Degrees of freedom for the reduced model.
        df_full: Degrees of freedom for the full model.

    Returns:
        Tuple (f_statistic, p_value).
    """
    if rss_full >= rss_reduced:
        # Full model should have lower or equal RSS
        # If not, the full model is worse, so F < 1
        f_stat = ((rss_reduced - rss_full) / (df_full - df_reduced)) / (rss_full / df_full)
    else:
        # This shouldn't happen in nested models, but handle gracefully
        f_stat = 0.0

    if f_stat <= 0:
        return 0.0, 1.0

    # Calculate p‑value
    p_value = 1 - stats.f.cdf(f_stat, df_full - df_reduced, df_full)

    return f_stat, p_value


def bootstrap_confidence_interval(
    data: np.ndarray,
    statistic: callable = np.mean,
    n_bootstrap: int = 1000,
    confidence_level: float = 0.95,
    random_state: Optional[int] = None
) -> Tuple[float, float]:
    """
    Calculate bootstrap confidence intervals for a statistic.

    Args:
        data: Input data array.
        statistic: Function to compute the statistic.
        n_bootstrap: Number of bootstrap samples.
        confidence_level: Confidence level (e.g., 0.95 for 95% CI).
        random_state: Random seed for reproducibility.

    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    data = np.asarray(data)
    rng = np.random.RandomState(random_state)

    bootstrap_stats = np.zeros(n_bootstrap)
    n = len(data)

    for i in range(n_bootstrap):
        # Resample with replacement
        sample = rng.choice(data, size=n, replace=True)
        bootstrap_stats[i] = statistic(sample)

    # Calculate confidence interval
    alpha = 1 - confidence_level
    lower_bound = np.percentile(bootstrap_stats, (alpha / 2) * 100)
    upper_bound = np.percentile(bootstrap_stats, (1 - alpha / 2) * 100)

    return lower_bound, upper_bound


def effect_size_cohens_d(
    group1: np.ndarray,
    group2: np.ndarray
) -> float:
    """
    Calculate Cohen's d effect size for two independent groups.

    Args:
        group1: First group data.
        group2: Second group data.

    Returns:
        Cohen's d effect size.
    """
    group1 = np.asarray(group1)
    group2 = np.asarray(group2)

    mean1, mean2 = np.mean(group1), np.mean(group2)
    std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)
    n1, n2 = len(group1), len(group2)

    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))

    if pooled_std == 0:
        return 0.0

    return (mean1 - mean2) / pooled_std


def correlation_significance(
    r: float,
    n: int
) -> float:
    """
    Calculate the p‑value for a correlation coefficient.

    Args:
        r: Pearson correlation coefficient.
        n: Sample size.

    Returns:
        Two‑tailed p‑value.
    """
    if n <= 2:
        return 1.0

    # t‑statistic for correlation
    t_stat = r * np.sqrt((n - 2) / (1 - r**2))

    # Two‑tailed p‑value
    p_value = 2 * (1 - stats.t.cdf(np.abs(t_stat), n - 2))

    return p_value


# ----------------------------------------------------------------------
# New functions required by FR‑006 / FR‑007 / FR‑011
# ----------------------------------------------------------------------
def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """
    Apply Bonferroni correction to a list of p‑values.

    Args:
        p_values: List of original p‑values.
        alpha: Desired family‑wise error rate (default 0.05).

    Returns:
        List of Bonferroni‑adjusted p‑values, each capped at 1.0.
    """
    if not p_values:
        return []

    n_tests = len(p_values)
    corrected = [min(p * n_tests, 1.0) for p in p_values]
    return corrected


def permutation_r2(
    X,
    y,
    model_class,
    n_splits: int,
    n_permutations: int,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Generate a null distribution of R² values by permuting training labels.

    The procedure follows the specification:
    1. Split the data once using K‑fold (the first split is used as the train/test split).
    2. For each permutation:
       a. Shuffle the training‑set labels ``y_train``.
       b. Instantiate a fresh model (no warm start) from ``model_class``.
       c. Fit the model on ``X_train`` and the shuffled ``y_train``.
       d. Evaluate R² on the held‑out test set.
    3. Return the array of R² values (null distribution).

    Args:
        X: Feature matrix (array‑like, shape [n_samples, n_features]).
        y: Target vector (array‑like, shape [n_samples]).
        model_class: A scikit‑learn‑compatible estimator class (not an instance).
        n_splits: Number of folds for the initial K‑fold split.
        n_permutations: Number of label‑shuffling permutations.
        seed: Random seed for reproducibility.

    Returns:
        Numpy array of shape (n_permutations,) containing R² values.
    """
    from sklearn.model_selection import KFold

    X = np.asarray(X)
    y = np.asarray(y)

    if X.shape[0] != y.shape[0]:
        raise ValueError("X and y must have the same number of samples")

    # Create a single train/test split using KFold (shuffle for randomness)
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=seed)
    train_idx, test_idx = next(kf.split(X))

    X_train, X_test = X[train_idx], X[test_idx]
    y_test = y[test_idx]

    rng = np.random.RandomState(seed)
    null_r2 = np.empty(n_permutations)

    for i in range(n_permutations):
        # Shuffle only the training labels
        y_train_shuffled = rng.permutation(y[train_idx])

        # Instantiate a fresh model (no warm start)
        model = model_class()
        model.fit(X_train, y_train_shuffled)

        # Predict on the held‑out test set
        y_pred = model.predict(X_test)

        # Compute R² (coefficient of determination)
        ss_res = np.sum((y_test - y_pred) ** 2)
        ss_tot = np.sum((y_test - np.mean(y_test)) ** 2)
        r2 = 1 - ss_res / ss_tot if ss_tot != 0 else 0.0
        null_r2[i] = r2

    return null_r2


def calculate_mdes(effect_size_r2: float, alpha: float = 0.05, power: float = 0.80) -> int:
    """
    Compute the Minimum Detectable Effect Size (MDES) expressed as the required
    sample size ``N`` for a target R² effect size.

    The calculation uses ``statsmodels.stats.power.FTestPower``. The effect
    size ``f`` is derived from the desired R² via ``f = sqrt(R² / (1 - R²))``.

    Args:
        effect_size_r2: Target R² (must be between 0 and 1).
        alpha: Significance level (default 0.05).
        power: Desired statistical power (default 0.80).

    Returns:
        Required sample size (integer, rounded up).
    """
    if not (0.0 < effect_size_r2 < 1.0):
        raise ValueError("effect_size_r2 must be between 0 and 1 (exclusive)")

    # Convert R² to Cohen's f (f² = R² / (1 - R²))
    f_squared = effect_size_r2 / (1.0 - effect_size_r2)
    f_effect = np.sqrt(f_squared)

    analysis = FTestPower()
    # For a regression with multiple predictors, df_num is 1 (numerator)
    # The solver will return the total number of observations needed.
    n_required = analysis.solve_power(
        effect_size=f_effect,
        df_num=1,
        df_denom=None,
        alpha=alpha,
        power=power,
        nobs=None,
        alternative='larger'
    )
    # Ensure an integer result
    return int(np.ceil(n_required))