"""
Runner for statistical tests on real datasets.
Implements T031: Run t-test, ANOVA, and chi-squared on real datasets and save observed p-value distributions.
"""
import os
import csv
import json
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats

from code.simulation.logging_config import get_logger, log_operation
from code.analysis.validator import download_breast_cancer_dataset, download_wine_dataset, download_adult_dataset
from code.simulation.chi_squared_utils import run_chi_squared_with_fallback

logger = get_logger("real_data_runner")

def run_ttest_on_dataset(df: pd.DataFrame, target_col: str, group_col: str, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Run independent t-test on a dataset.
    """
    try:
        groups = df.groupby(group_col)[target_col]
        if len(groups) != 2:
            return {"test_type": "t-test", "status": "failed", "reason": "Not exactly 2 groups"}
        
        group1, group2 = groups
        stat, p_value = stats.ttest_ind(group1.dropna(), group2.dropna())
        
        return {
            "test_type": "t-test",
            "p_value": float(p_value),
            "statistic": float(stat),
            "alpha": alpha,
            "significant": p_value < alpha,
            "n1": len(group1),
            "n2": len(group2)
        }
    except Exception as e:
        return {"test_type": "t-test", "status": "failed", "reason": str(e)}

def run_anova_on_dataset(df: pd.DataFrame, target_col: str, group_col: str, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Run one-way ANOVA on a dataset.
    """
    try:
        groups = [group.dropna() for _, group in df.groupby(group_col)[target_col]]
        if len(groups) < 2:
            return {"test_type": "anova", "status": "failed", "reason": "Not enough groups"}
        
        stat, p_value = stats.f_oneway(*groups)
        
        return {
            "test_type": "anova",
            "p_value": float(p_value),
            "statistic": float(stat),
            "alpha": alpha,
            "significant": p_value < alpha,
            "k": len(groups)
        }
    except Exception as e:
        return {"test_type": "anova", "status": "failed", "reason": str(e)}

def run_chi_squared_on_dataset(df: pd.DataFrame, col1: str, col2: str, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Run chi-squared test on a dataset.
    """
    try:
        contingency = pd.crosstab(df[col1], df[col2])
        if contingency.shape[0] < 2 or contingency.shape[1] < 2:
            return {"test_type": "chi-squared", "status": "failed", "reason": "Contingency table too small"}
        
        # Use fallback logic if needed
        result = run_chi_squared_with_fallback(contingency.values)
        
        return {
            "test_type": "chi-squared",
            "p_value": float(result["p_value"]),
            "statistic": float(result["statistic"]),
            "alpha": alpha,
            "significant": result["p_value"] < alpha,
            "method": result["method"]
        }
    except Exception as e:
        return {"test_type": "chi-squared", "status": "failed", "reason": str(e)}

def save_p_values_to_csv(results: List[Dict[str, Any]], filepath: str = "data/simulation/real_data_pvalues.csv"):
    """
    Save p-values to CSV.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["dataset", "test_type", "p_value", "significant", "sample_size", "method", "status"])
        writer.writeheader()
        for r in results:
            writer.writerow({
                "dataset": r.get("dataset", "unknown"),
                "test_type": r.get("test_type", "unknown"),
                "p_value": r.get("p_value", np.nan),
                "significant": r.get("significant", False),
                "sample_size": r.get("sample_size", 0),
                "method": r.get("method", "standard"),
                "status": r.get("status", "success")
            })
    logger.log("p_values_saved", path=filepath, count=len(results))

def load_p_values_to_csv_safe(filepath: str = "data/simulation/real_data_pvalues.csv") -> Optional[pd.DataFrame]:
    """
    Load p-values from CSV safely.
    """
    if not os.path.exists(filepath):
        return None
    try:
        return pd.read_csv(filepath)
    except Exception:
        return None

def run_validation_on_datasets(alpha: float = 0.05) -> List[Dict[str, Any]]:
    """
    Run validation on all downloaded datasets.
    """
    results = []
    
    # Breast Cancer (T-test)
    try:
        df_bc = download_breast_cancer_dataset()
        if df_bc is not None and not df_bc.empty:
            # Prepare for t-test
            # Assuming diagnosis is the group and some feature is the target
            # For simplicity, use first numeric column as target, diagnosis as group
            numeric_cols = df_bc.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 1:
                target = numeric_cols[0]
                group = "diagnosis" if "diagnosis" in df_bc.columns else df_bc.columns[1]
                res = run_ttest_on_dataset(df_bc, target, group, alpha)
                res["dataset"] = "breast_cancer"
                res["sample_size"] = len(df_bc)
                results.append(res)
    except Exception as e:
        logger.log("validation_failed_breast_cancer", error=str(e))
    
    # Wine (ANOVA)
    try:
        df_wine = download_wine_dataset()
        if df_wine is not None and not df_wine.empty:
            # Prepare for ANOVA
            # Assuming 'class' is the group
            numeric_cols = df_wine.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 1:
                target = numeric_cols[0]
                group = "class" if "class" in df_wine.columns else df_wine.columns[0]
                res = run_anova_on_dataset(df_wine, target, group, alpha)
                res["dataset"] = "wine"
                res["sample_size"] = len(df_wine)
                results.append(res)
    except Exception as e:
        logger.log("validation_failed_wine", error=str(e))
    
    # Adult (Chi-squared)
    try:
        df_adult = download_adult_dataset()
        if df_adult is not None and not df_adult.empty:
            # Prepare for Chi-squared
            # Use two categorical columns
            cat_cols = df_adult.select_dtypes(include=['object']).columns
            if len(cat_cols) >= 2:
                col1 = cat_cols[0]
                col2 = cat_cols[1]
                res = run_chi_squared_on_dataset(df_adult, col1, col2, alpha)
                res["dataset"] = "adult"
                res["sample_size"] = len(df_adult)
                results.append(res)
    except Exception as e:
        logger.log("validation_failed_adult", error=str(e))
    
    # Save results
    save_p_values_to_csv(results)
    return results

def main():
    """Main entry point."""
    logger.log("start_real_data_validation")
    results = run_validation_on_datasets()
    logger.log("real_data_validation_complete", count=len(results))

if __name__ == "__main__":
    main()
