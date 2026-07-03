import numpy as np
import pandas as pd
import logging
from typing import Dict, Any, Optional, Tuple, Union, Callable
from scipy import stats
from dataclasses import dataclass, field
from enum import Enum

# Import existing scaling functions from preprocessing module
from preprocessing.scaling import standardize_data, min_max_scale, robust_scale

logger = logging.getLogger(__name__)


class ScalingMethod(Enum):
    """Enumeration of available scaling methods."""
    STANDARDIZE = "standardize"
    MIN_MAX = "min_max"
    ROBUST = "robust"
    NONE = "none"


@dataclass
class TestResult:
    """
    Data class to store the results of a statistical test after scaling.
    """
    test_type: str
    scaling_method: str
    statistic: float
    p_value: float
    null_hypothesis_rejected: bool
    effect_size: Optional[float] = None
    confidence_interval: Optional[Tuple[float, float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary for serialization."""
        return {
            "test_type": self.test_type,
            "scaling_method": self.scaling_method,
            "statistic": self.statistic,
            "p_value": self.p_value,
            "null_hypothesis_rejected": self.null_hypothesis_rejected,
            "effect_size": self.effect_size,
            "confidence_interval": list(self.confidence_interval) if self.confidence_interval else None,
            **self.metadata
        }


def run_scaled_t_test(
    data_a: Union[pd.Series, np.ndarray],
    data_b: Union[pd.Series, np.ndarray],
    scaling_method: ScalingMethod = ScalingMethod.STANDARDIZE,
    equal_var: bool = True,
    alternative: str = "two-sided",
    **kwargs
) -> TestResult:
    """
    Apply a scaling method to two datasets, then perform a t-test.

    Args:
        data_a: First dataset (Group A).
        data_b: Second dataset (Group B).
        scaling_method: The scaling method to apply (Standardize, MinMax, Robust, or None).
        equal_var: Assumption for t-test (equal variance).
        alternative: Type of t-test ("two-sided", "less", "greater").
        **kwargs: Additional arguments passed to the specific scaling function.

    Returns:
        TestResult entity containing statistics and metadata.
    """
    # Convert inputs to numpy arrays for consistent processing
    arr_a = np.asarray(data_a)
    arr_b = np.asarray(data_b)

    if arr_a.ndim > 1 or arr_b.ndim > 1:
        arr_a = arr_a.flatten()
        arr_b = arr_b.flatten()

    # Apply Scaling
    if scaling_method == ScalingMethod.STANDARDIZE:
        logger.info(f"Applying standardization to t-test groups")
        scaled_a = standardize_data(arr_a, **kwargs)
        scaled_b = standardize_data(arr_b, **kwargs)
    elif scaling_method == ScalingMethod.MIN_MAX:
        logger.info(f"Applying min-max scaling to t-test groups")
        scaled_a = min_max_scale(arr_a, **kwargs)
        scaled_b = min_max_scale(arr_b, **kwargs)
    elif scaling_method == ScalingMethod.ROBUST:
        logger.info(f"Applying robust scaling to t-test groups")
        scaled_a = robust_scale(arr_a, **kwargs)
        scaled_b = robust_scale(arr_b, **kwargs)
    elif scaling_method == ScalingMethod.NONE:
        scaled_a = arr_a
        scaled_b = arr_b
    else:
        raise ValueError(f"Unknown scaling method: {scaling_method}")

    # Run T-Test
    # Reusing logic similar to run_t_test but ensuring we use scaled data
    t_stat, p_val = stats.ttest_ind(scaled_a, scaled_b, equal_var=equal_var, alternative=alternative)

    # Calculate effect size (Cohen's d) on scaled data
    n1, n2 = len(scaled_a), len(scaled_b)
    if n1 > 1 and n2 > 1:
        mean_diff = np.mean(scaled_a) - np.mean(scaled_b)
        pooled_std = np.sqrt(((n1 - 1) * np.var(scaled_a, ddof=1) + (n2 - 1) * np.var(scaled_b, ddof=1)) / (n1 + n2 - 2))
        if pooled_std > 0:
            effect_size = mean_diff / pooled_std
        else:
            effect_size = 0.0
    else:
        effect_size = 0.0

    # Determine rejection
    alpha = kwargs.get('alpha', 0.05)
    rejected = p_val < alpha

    return TestResult(
        test_type="t_test",
        scaling_method=scaling_method.value,
        statistic=float(t_stat),
        p_value=float(p_val),
        null_hypothesis_rejected=rejected,
        effect_size=float(effect_size),
        metadata={"alpha": alpha, "equal_var": equal_var}
    )


def run_scaled_anova(
    groups: Dict[str, Union[pd.Series, np.ndarray]],
    scaling_method: ScalingMethod = ScalingMethod.STANDARDIZE,
    **kwargs
) -> TestResult:
    """
    Apply a scaling method to multiple groups, then perform ANOVA.

    Args:
        groups: Dictionary mapping group names to data arrays.
        scaling_method: The scaling method to apply.
        **kwargs: Additional arguments passed to scaling functions.

    Returns:
        TestResult entity.
    """
    if len(groups) < 2:
        raise ValueError("ANOVA requires at least two groups.")

    scaled_arrays = []
    for name, data in groups.items():
        arr = np.asarray(data).flatten()
        if scaling_method == ScalingMethod.STANDARDIZE:
            scaled_arrays.append(standardize_data(arr, **kwargs))
        elif scaling_method == ScalingMethod.MIN_MAX:
            scaled_arrays.append(min_max_scale(arr, **kwargs))
        elif scaling_method == ScalingMethod.ROBUST:
            scaled_arrays.append(robust_scale(arr, **kwargs))
        elif scaling_method == ScalingMethod.NONE:
            scaled_arrays.append(arr)
        else:
            raise ValueError(f"Unknown scaling method: {scaling_method}")

    # Run ANOVA
    f_stat, p_val = stats.f_oneway(*scaled_arrays)

    # Effect size: Eta-squared (η²)
    # η² = SS_between / SS_total
    # We calculate this manually on the scaled data
    all_data = np.concatenate(scaled_arrays)
    grand_mean = np.mean(all_data)
    ss_total = np.sum((all_data - grand_mean) ** 2)

    ss_between = 0
    n_total = 0
    for s_arr in scaled_arrays:
        n = len(s_arr)
        group_mean = np.mean(s_arr)
        ss_between += n * (group_mean - grand_mean) ** 2
        n_total += n

    eta_squared = ss_between / ss_total if ss_total > 0 else 0.0

    alpha = kwargs.get('alpha', 0.05)
    rejected = p_val < alpha

    return TestResult(
        test_type="anova",
        scaling_method=scaling_method.value,
        statistic=float(f_stat),
        p_value=float(p_val),
        null_hypothesis_rejected=rejected,
        effect_size=float(eta_squared),
        metadata={"alpha": alpha, "num_groups": len(groups)}
    )


def run_scaled_chi_squared(
    contingency_table: Union[pd.DataFrame, np.ndarray],
    scaling_method: ScalingMethod = ScalingMethod.NONE,
    **kwargs
) -> TestResult:
    """
    Apply scaling to a contingency table (if applicable) and run Chi-Squared test.
    
    Note: Chi-squared tests are typically for counts. Scaling continuous data 
    into counts requires binning logic (handled in run_chi_squared in this module).
    If a raw table is provided, scaling is generally not applied or is a no-op
    unless specific normalization is requested.
    
    This wrapper specifically handles the case where we might have continuous 
    data that needs binning (as per T023) OR a pre-binned table.
    For T024, we focus on the pipeline wrapper aspect.
    If input is 2D array, we assume it's a contingency table.
    If input is 1D arrays, we bin them first.

    Args:
        contingency_table: 2D array-like (contingency table) or tuple of 1D arrays.
        scaling_method: Scaling method (mostly ignored for standard Chi-sq on counts, 
                        but if 1D continuous data is passed, we scale then bin).
        **kwargs: Arguments for binning (if applicable) or test.

    Returns:
        TestResult entity.
    """
    # Handle input types
    if isinstance(contingency_table, tuple) and len(contingency_table) == 2:
        # Continuous data provided, need to bin
        data_a, data_b = contingency_table
        arr_a = np.asarray(data_a).flatten()
        arr_b = np.asarray(data_b).flatten()

        # Apply scaling if requested for continuous data before binning
        if scaling_method != ScalingMethod.NONE:
            if scaling_method == ScalingMethod.STANDARDIZE:
                arr_a = standardize_data(arr_a)
                arr_b = standardize_data(arr_b)
            elif scaling_method == ScalingMethod.MIN_MAX:
                arr_a = min_max_scale(arr_a)
                arr_b = min_max_scale(arr_b)
            elif scaling_method == ScalingMethod.ROBUST:
                arr_a = robust_scale(arr_a)
                arr_b = robust_scale(arr_b)

        # Bin using Sturges' rule (as per T023 logic)
        k = int(np.ceil(np.log2(max(len(arr_a), len(arr_b))) + 1))
        # Create bins covering the union of ranges
        min_val = min(np.min(arr_a), np.min(arr_b))
        max_val = max(np.max(arr_a), np.max(arr_b))
        bins = np.linspace(min_val - 1e-9, max_val + 1e-9, k + 1)
        
        hist_a, _ = np.histogram(arr_a, bins=bins)
        hist_b, _ = np.histogram(arr_b, bins=bins)
        
        table = np.vstack([hist_a, hist_b])
    else:
        # Assume 2D contingency table provided directly
        if scaling_method != ScalingMethod.NONE:
            logger.warning("Scaling method specified for pre-binned contingency table. Ignoring scaling.")
        table = np.asarray(contingency_table)

    # Run Chi-Squared
    chi2_stat, p_val, dof, expected = stats.chi2_contingency(table)

    # Effect size: Cramér's V
    n = np.sum(table)
    min_dim = min(table.shape)
    cramers_v = np.sqrt(chi2_stat / (n * (min_dim - 1))) if n > 0 else 0.0

    alpha = kwargs.get('alpha', 0.05)
    rejected = p_val < alpha

    return TestResult(
        test_type="chi_squared",
        scaling_method=scaling_method.value,
        statistic=float(chi2_stat),
        p_value=float(p_val),
        null_hypothesis_rejected=rejected,
        effect_size=float(cramers_v),
        metadata={"alpha": alpha, "degrees_of_freedom": dof}
    )


def run_pipeline(
    data_a: Union[pd.Series, np.ndarray],
    data_b: Union[pd.Series, np.ndarray],
    test_type: str = "t_test",
    scaling_methods: Optional[list] = None,
    **kwargs
) -> list[TestResult]:
    """
    Pipeline wrapper to apply multiple scaling methods and run the specified test.
    
    Args:
        data_a: Group A data.
        data_b: Group B data.
        test_type: "t_test", "anova", or "chi_squared".
        scaling_methods: List of ScalingMethod enums. Defaults to [STANDARDIZE, MIN_MAX, ROBUST, NONE].
        **kwargs: Arguments passed to specific test functions.

    Returns:
        List of TestResult entities.
    """
    if scaling_methods is None:
        scaling_methods = [
            ScalingMethod.STANDARDIZE,
            ScalingMethod.MIN_MAX,
            ScalingMethod.ROBUST,
            ScalingMethod.NONE
        ]

    results = []
    
    for method in scaling_methods:
        logger.info(f"Running {test_type} with {method.value} scaling")
        try:
            if test_type == "t_test":
                res = run_scaled_t_test(data_a, data_b, scaling_method=method, **kwargs)
            elif test_type == "anova":
                # For ANOVA, we treat data_a as group 1 and data_b as group 2
                # In a real pipeline, we might expect a dict of groups, but for this wrapper
                # we adapt to the two-sample input provided by the task context.
                # If more groups are needed, the caller should pass a dict to run_scaled_anova directly.
                # Here we just run on the two provided groups.
                res = run_scaled_anova({"group_a": data_a, "group_b": data_b}, scaling_method=method, **kwargs)
            elif test_type == "chi_squared":
                res = run_scaled_chi_squared((data_a, data_b), scaling_method=method, **kwargs)
            else:
                raise ValueError(f"Unsupported test_type: {test_type}")
            
            results.append(res)
        except Exception as e:
            logger.error(f"Failed to run {test_type} with {method.value}: {e}", exc_info=True)
            # Optionally append a failure result or skip
            continue

    return results