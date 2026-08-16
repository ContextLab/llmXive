import os
import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set

import pandas as pd
import numpy as np
from scipy import stats

from config import get_config
from data.loader import LowPowerError, RAMExceededError
from narrative.baseline import compute_pairwise_correlations, identify_strongest_relationship

logger = logging.getLogger(__name__)

# Domain heuristics for candidate generation
TIME_KEYWORDS = [
    'year', 'month', 'day', 'date', 'time', 'quarter', 'decade', 
    'period', 'cycle', 'season', 'temporal', 'timestamp'
]

LOCATION_KEYWORDS = [
    'county', 'city', 'state', 'region', 'district', 'zip', 'postal',
    'area', 'zone', 'borough', 'neighborhood', 'location', 'lat', 'lon',
    'latitude', 'longitude', 'municipality', 'province'
]

DEMOGRAPHIC_KEYWORDS = [
    'population', 'income', 'poverty', 'unemployment', 'education',
    'race', 'ethnicity', 'gender', 'age', 'household', 'family',
    'demographic', 'census', 'median', 'per capita'
]

def _is_time_related(column_name: str) -> bool:
    """Check if column name suggests a time-related variable."""
    name_lower = column_name.lower()
    return any(keyword in name_lower for keyword in TIME_KEYWORDS)

def _is_location_related(column_name: str) -> bool:
    """Check if column name suggests a location-related variable."""
    name_lower = column_name.lower()
    return any(keyword in name_lower for keyword in LOCATION_KEYWORDS)

def _is_demographic_related(column_name: str) -> bool:
    """Check if column name suggests a demographic variable."""
    name_lower = column_name.lower()
    return any(keyword in name_lower for keyword in DEMOGRAPHIC_KEYWORDS)

def _is_numeric_column(df: pd.DataFrame, col_name: str) -> bool:
    """Check if a column is numeric and suitable for correlation."""
    if col_name not in df.columns:
        return False
    return pd.api.types.is_numeric_dtype(df[col_name])

def generate_candidate_confounders(
    df: pd.DataFrame,
    baseline_x: str,
    baseline_y: str,
    top_drivers: Optional[List[str]] = None
) -> List[str]:
    """
    Generate candidate confounders based on domain heuristics.
    
    Strategy:
    1. Identify columns that are NOT baseline_x or baseline_y.
    2. Filter for numeric columns.
    3. Prioritize columns matching time, location, or demographic heuristics.
    4. Also include columns that are strongly correlated with either X or Y
       (potential confounders in the statistical sense).
    
    Args:
        df: The processed dataset.
        baseline_x: The independent variable from baseline analysis.
        baseline_y: The dependent variable from baseline analysis.
        top_drivers: Optional list of top baseline drivers to exclude or prioritize.
    
    Returns:
        A list of candidate confounder column names, sorted by heuristic priority.
    """
    candidates = []
    excluded = {baseline_x, baseline_y}
    if top_drivers:
        excluded.update(top_drivers)
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Heuristic scoring
    scored_candidates = []
    
    for col in numeric_cols:
        if col in excluded:
            continue
        
        score = 0
        reasons = []
        
        # Heuristic 1: Time-related
        if _is_time_related(col):
            score += 3
            reasons.append("time-related")
        
        # Heuristic 2: Location-related
        if _is_location_related(col):
            score += 3
            reasons.append("location-related")
        
        # Heuristic 3: Demographic-related
        if _is_demographic_related(col):
            score += 2
            reasons.append("demographic-related")
        
        # Heuristic 4: Statistical relevance (correlation with X or Y)
        try:
            corr_x = df[col].corr(df[baseline_x])
            corr_y = df[col].corr(df[baseline_y])
            
            if abs(corr_x) > 0.3 or abs(corr_y) > 0.3:
                score += 1
                reasons.append(f"corr(X)={corr_x:.2f}, corr(Y)={corr_y:.2f}")
        except (ValueError, TypeError):
            pass  # Skip if correlation fails
        
        if score > 0:
            scored_candidates.append((col, score, reasons))
    
    # Sort by score descending, then by name
    scored_candidates.sort(key=lambda x: (-x[1], x[0]))
    
    # Extract just the column names
    candidates = [item[0] for item in scored_candidates]
    
    logger.info(f"Generated {len(candidates)} candidate confounders: {candidates[:5]}...")
    return candidates

def get_baseline_drivers(baseline_results: Dict[str, Any]) -> List[str]:
    """
    Extract the top drivers (variables involved in strongest relationships)
    from baseline analysis results.
    
    Args:
        baseline_results: Output from run_baseline_analysis or similar.
    
    Returns:
        List of variable names that are strong drivers in the baseline.
    """
    drivers = []
    
    # Extract from primary narrative if available
    if 'primary_narrative' in baseline_results:
        # We can try to parse, but simpler to use the correlation data directly
        pass
    
    # Extract from pairwise correlations
    if 'pairwise_correlations' in baseline_results:
        correlations = baseline_results['pairwise_correlations']
        # Sort by absolute correlation value
        sorted_corrs = sorted(
            correlations, 
            key=lambda x: abs(x.get('r_value', 0)), 
            reverse=True
        )
        
        # Take top 5 unique variables
        seen = set()
        for corr in sorted_corrs[:10]:
            if len(seen) >= 5:
                break
            if corr['var_x'] not in seen:
                drivers.append(corr['var_x'])
                seen.add(corr['var_x'])
            if corr['var_y'] not in seen:
                drivers.append(corr['var_y'])
                seen.add(corr['var_y'])
    
    return drivers

def compute_partial_correlation(
    df: pd.DataFrame,
    x: str,
    y: str,
    control_vars: List[str]
) -> Tuple[float, float]:
    """
    Compute partial correlation between x and y controlling for control_vars.
    
    Args:
        df: The dataset.
        x: Independent variable.
        y: Dependent variable.
        control_vars: List of variables to control for.
    
    Returns:
        Tuple of (partial_r, p_value).
    """
    # Ensure all variables exist and are numeric
    all_vars = [x, y] + control_vars
    valid_vars = [v for v in all_vars if v in df.columns and pd.api.types.is_numeric_dtype(df[v])]
    
    if len(valid_vars) < 3:  # Need at least x, y, and one control
        logger.warning(f"Not enough valid variables for partial correlation: {valid_vars}")
        return 0.0, 1.0
    
    # Drop rows with missing values in any of the variables
    subset = df[valid_vars].dropna()
    
    if len(subset) < 10:
        logger.warning(f"Insufficient samples for partial correlation: {len(subset)}")
        return 0.0, 1.0
    
    try:
        # Use scipy's partial correlation approach via residuals
        # Regress x on controls
        from sklearn.linear_model import LinearRegression
        
        X_controls = subset[control_vars].values
        y_x = subset[x].values
        y_y = subset[y].values
        
        # Residuals for x
        if len(control_vars) > 0:
            reg_x = LinearRegression().fit(X_controls, y_x)
            res_x = y_x - reg_x.predict(X_controls)
        else:
            res_x = y_x
        
        # Residuals for y
        if len(control_vars) > 0:
            reg_y = LinearRegression().fit(X_controls, y_y)
            res_y = y_y - reg_y.predict(X_controls)
        else:
            res_y = y_y
        
        # Correlation of residuals
        r, p_value = stats.pearsonr(res_x, res_y)
        return float(r), float(p_value)
        
    except Exception as e:
        logger.error(f"Error computing partial correlation: {e}")
        return 0.0, 1.0

def inspect_dataset_for_counterfactuals(
    df: pd.DataFrame,
    baseline_results: Dict[str, Any],
    max_candidates: int = 10
) -> Dict[str, Any]:
    """
    Main inspector logic to find counterfactuals.
    
    1. Get baseline drivers.
    2. Generate candidate confounders.
    3. For each candidate, compute partial correlation controlling for baseline drivers.
    4. Return results.
    
    Args:
        df: Processed dataset.
        baseline_results: Results from baseline analysis.
        max_candidates: Maximum number of candidates to test.
    
    Returns:
        Dictionary containing counterfactual analysis results.
    """
    # Get baseline drivers
    drivers = get_baseline_drivers(baseline_results)
    
    # Identify primary relationship
    primary = baseline_results.get('primary_narrative', {})
    x_var = primary.get('var_x')
    y_var = primary.get('var_y')
    
    if not x_var or not y_var:
        logger.warning("Could not identify primary variables from baseline")
        return {"counterfactuals": [], "error": "No primary relationship found"}
    
    # Generate candidates
    candidates = generate_candidate_confounders(df, x_var, y_var, drivers)
    candidates = candidates[:max_candidates]
    
    if not candidates:
        logger.info("No candidate confounders found")
        return {"counterfactuals": [], "candidates_checked": 0}
    
    results = []
    
    for candidate in candidates:
        # Control for top 2 baseline drivers
        control_vars = drivers[:2] if len(drivers) >= 2 else drivers
        
        partial_r, p_value = compute_partial_correlation(
            df, x_var, y_var, control_vars + [candidate]
        )
        
        # Check if this is a significant counterfactual
        # If partial correlation drops significantly, the candidate might be a confounder
        baseline_r = primary.get('r_value', 0)
        
        results.append({
            "candidate_confounder": candidate,
            "control_variables": control_vars + [candidate],
            "partial_r": partial_r,
            "p_value": p_value,
            "baseline_r": baseline_r,
            "r_change": abs(baseline_r) - abs(partial_r),
            "interpretation": "confounder" if abs(partial_r) < abs(baseline_r) * 0.5 else "independent"
        })
    
    return {
        "baseline_primary": {"x": x_var, "y": y_var, "r": baseline_r},
        "drivers_checked": drivers,
        "candidates_checked": len(candidates),
        "counterfactuals": results
    }

def run_inspector_analysis(
    df: pd.DataFrame,
    baseline_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Run the full inspector analysis pipeline.
    
    Args:
        df: Processed dataset.
        baseline_results: Results from baseline analysis.
    
    Returns:
        Complete inspector analysis results.
    """
    logger.info("Starting inspector analysis...")
    
    try:
        # Check sample size
        n = len(df)
        if n < 30:
            raise LowPowerError(f"Sample size {n} is below threshold of 30")
        
        # Run counterfactual inspection
        results = inspect_dataset_for_counterfactuals(df, baseline_results)
        
        # Add metadata
        results['analysis_status'] = 'completed'
        results['sample_size'] = n
        
        return results
        
    except LowPowerError as e:
        logger.error(f"Low power error in inspector: {e}")
        return {
            "analysis_status": "failed",
            "error": str(e),
            "counterfactuals": []
        }
    except Exception as e:
        logger.error(f"Inspector analysis failed: {e}")
        return {
            "analysis_status": "failed",
            "error": str(e),
            "counterfactuals": []
        }

def main():
    """
    CLI entry point for inspector analysis.
    Expects:
      --dataset: Path to processed dataset (CSV)
      --baseline: Path to baseline results (JSON)
      --output: Path for output JSON
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Counterfactual Inspector Analysis")
    parser.add_argument("--dataset", required=True, help="Path to processed dataset CSV")
    parser.add_argument("--baseline", required=True, help="Path to baseline results JSON")
    parser.add_argument("--output", required=True, help="Path for output JSON")
    parser.add_argument("--max-candidates", type=int, default=10, help="Max candidates to test")
    
    args = parser.parse_args()
    
    # Load data
    logger.info(f"Loading dataset from {args.dataset}")
    df = pd.read_csv(args.dataset)
    
    logger.info(f"Loading baseline results from {args.baseline}")
    with open(args.baseline, 'r') as f:
        baseline_results = json.load(f)
    
    # Run analysis
    results = run_inspector_analysis(df, baseline_results)
    results['max_candidates'] = args.max_candidates
    
    # Save output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Inspector results written to {args.output}")
    return results

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()