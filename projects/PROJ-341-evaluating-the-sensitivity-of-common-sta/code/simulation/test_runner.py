"""
Test runner for statistical tests.
Implements T012: Execute t-test, ANOVA, and chi-squared on generated data.
"""
import numpy as np
from scipy import stats
from typing import Tuple, List, Dict, Any, Optional, Union
import warnings
import json
import os

from code.simulation.logging_config import get_logger, log_operation
from code.simulation.data_generator import generate_two_sample_data, generate_anova_data, generate_contingency_table_data
from code.simulation.chi_squared_utils import run_chi_squared_with_fallback

logger = get_logger("test_runner")

def run_t_test(sample1: np.ndarray, sample2: np.ndarray, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Run independent t-test.
    """
    try:
        stat, p_value = stats.ttest_ind(sample1, sample2)
        return {
            "test_type": "t-test",
            "p_value": float(p_value),
            "statistic": float(stat),
            "alpha": alpha,
            "significant": p_value < alpha
        }
    except Exception as e:
        logger.log("t_test_error", error=str(e))
        return {"test_type": "t-test", "p_value": np.nan, "error": str(e)}

def run_anova(groups: List[np.ndarray], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Run one-way ANOVA.
    """
    try:
        stat, p_value = stats.f_oneway(*groups)
        return {
            "test_type": "anova",
            "p_value": float(p_value),
            "statistic": float(stat),
            "alpha": alpha,
            "significant": p_value < alpha
        }
    except Exception as e:
        logger.log("anova_error", error=str(e))
        return {"test_type": "anova", "p_value": np.nan, "error": str(e)}

def run_chi_squared(contingency: np.ndarray, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Run chi-squared test with fallback logic.
    """
    result = run_chi_squared_with_fallback(contingency)
    return {
        "test_type": "chi-squared",
        "p_value": float(result["p_value"]),
        "statistic": float(result["statistic"]),
        "alpha": alpha,
        "significant": result["p_value"] < alpha,
        "method": result["method"]
    }

def run_simulation_condition(condition: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Run simulation for a single condition.
    """
    n = condition["sample_size"]
    effect_size = condition["effect_size"]
    hypothesis = condition["hypothesis"]
    test_type = condition["test_type"]
    iterations = condition["iterations"]
    alpha = condition["alpha"]
    
    results = []
    
    for i in range(iterations):
        try:
            if test_type == "t-test":
                # Generate two samples
                if hypothesis == "null":
                    # Null hypothesis: no effect
                    data1 = np.random.normal(0, 1, n)
                    data2 = np.random.normal(0, 1, n)
                else:
                    # Alternative hypothesis: effect exists
                    data1 = np.random.normal(0, 1, n)
                    data2 = np.random.normal(effect_size, 1, n)
                
                res = run_t_test(data1, data2, alpha)
            
            elif test_type == "anova":
                # Generate groups for ANOVA
                if hypothesis == "null":
                    groups = [np.random.normal(0, 1, n) for _ in range(3)]
                else:
                    groups = [
                        np.random.normal(0, 1, n),
                        np.random.normal(effect_size, 1, n),
                        np.random.normal(2 * effect_size, 1, n)
                    ]
                res = run_anova(groups, alpha)
            
            elif test_type == "chi-squared":
                # Generate contingency table
                if hypothesis == "null":
                    # Expected counts are roughly equal
                    contingency = np.random.multinomial(n, [0.25, 0.25, 0.25, 0.25]).reshape(2, 2)
                else:
                    # Expected counts are different
                    contingency = np.random.multinomial(n, [0.1, 0.4, 0.4, 0.1]).reshape(2, 2)
                res = run_chi_squared(contingency, alpha)
            
            res["sample_size"] = n
            res["effect_size"] = effect_size
            res["hypothesis"] = hypothesis
            res["iteration"] = i
            results.append(res)
            
        except Exception as e:
            logger.log("simulation_iteration_error", error=str(e), iteration=i)
            results.append({
                "test_type": test_type,
                "sample_size": n,
                "effect_size": effect_size,
                "hypothesis": hypothesis,
                "iteration": i,
                "p_value": np.nan,
                "error": str(e)
            })
    
    return results

def aggregate_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate simulation results.
    """
    # Placeholder for aggregation logic
    return {"total": len(results)}

def main():
    """Main entry point for testing."""
    logger.log("test_runner_main")

if __name__ == "__main__":
    main()
