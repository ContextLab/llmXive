import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logger import get_logger
from data.verify_columns import verify_platform_column

def load_baseline_results(file_path: Path, logger: logging.Logger):
    """Load baseline regression results."""
    import pandas as pd
    logger.info(f"Loading baseline results from {file_path}")
    if not file_path.exists():
        logger.warning(f"Baseline results not found at {file_path}.")
        return None
    return pd.read_csv(file_path)

def fit_ols_model_continuous(df: pd.DataFrame, outcome: str, logger: logging.Logger):
    """Fit model using continuous harassment_severity instead of binary exposure."""
    import statsmodels.formula.api as smf
    
    covariates = ['age', 'gender', 'education', 'income']
    covariates = [c for c in covariates if c in df.columns]
    cov_str = " + ".join(covariates) if covariates else ""
    
    formula = f"{outcome} ~ social_support + harassment_severity + social_support:harassment_severity"
    if cov_str:
        formula += f" + {cov_str}"
    
    logger.info(f"Fitting continuous model: {formula}")
    
    try:
        model = smf.ols(formula, data=df).fit(cov_type='HC3')
        coef = model.params.get('social_support:harassment_severity', None)
        return {"coef": coef, "formula": formula}
    except Exception as e:
        logger.error(f"Continuous model failed: {str(e)}")
        return None

def stratify_by_platform(df: pd.DataFrame, logger: logging.Logger) -> Dict[str, pd.DataFrame]:
    """Stratify dataset by platform groups (N >= 30)."""
    if 'platform' not in df.columns:
        logger.warning("W-NO-PLATFORM-001: Platform column missing. Skipping stratification.")
        return {}
    
    # Check platform status
    platform_status_path = project_root / "data" / "results" / "platform_status.json"
    if platform_status_path.exists():
        import json
        with open(platform_status_path) as f:
            status = json.load(f)
        if not status.get("platform_exists", False):
            logger.warning("W-NO-PLATFORM-001: Platform does not exist. Skipping stratification.")
            return {}
    
    # Group by platform
    groups = df.groupby('platform')
    valid_groups = {}
    
    for name, group in groups:
        if len(group) >= 30:
            valid_groups[name] = group
        else:
            logger.warning(f"E-SMALL-N-001: Platform {name} has N={len(group)} < 30. Excluding.")
    
    if not valid_groups:
        logger.warning("No valid platform groups (N >= 30) found. Skipping stratification.")
    
    return valid_groups

def run_sensitivity_analysis(df: pd.DataFrame, outcomes: List[str], logger: logging.Logger) -> List[Dict[str, Any]]:
    """Run sensitivity analysis (continuous severity)."""
    results = []
    for outcome in outcomes:
        if outcome not in df.columns:
            continue
        res = fit_ols_model_continuous(df, outcome, logger)
        if res:
            results.append({
                "outcome": outcome,
                "interaction_coef": res["coef"],
                "type": "continuous"
            })
    return results

def save_results(results: List[Dict[str, Any]], output_path: Path, logger: logging.Logger):
    """Save sensitivity results."""
    import pandas as pd
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    logger.info(f"Sensitivity results saved to {output_path}")

def main():
    """Entry point for sensitivity analysis (T027a, T027b)."""
    logger = get_logger(__name__)
    logger.info("Starting Sensitivity Analysis")
    
    # Load cohort
    cohort_path = project_root / "data" / "results" / "analysis_cohort.csv"
    import pandas as pd
    if not cohort_path.exists():
        logger.error("Analysis cohort not found. Run pipeline first.")
        return
    df = pd.read_csv(cohort_path)
    
    # Continuous model
    outcomes = ['depression', 'anxiety']
    if 'ptsd' in df.columns:
        outcomes.append('ptsd')
    
    cont_results = run_sensitivity_analysis(df, outcomes, logger)
    
    # Stratified model
    stratified_groups = stratify_by_platform(df, logger)
    strat_results = []
    
    if stratified_groups:
        for platform, group_df in stratified_groups.items():
            logger.info(f"Running stratified model for platform: {platform}")
            for outcome in outcomes:
                if outcome in group_df.columns:
                    res = fit_ols_model_continuous(group_df, outcome, logger)
                    if res:
                        strat_results.append({
                            "platform": platform,
                            "outcome": outcome,
                            "interaction_coef": res["coef"],
                            "type": "stratified"
                        })
    
    # Save continuous results
    cont_path = project_root / "data" / "results" / "sensitivity_raw_continuous.csv"
    save_results(cont_results, cont_path, logger)
    
    # Save stratified results
    strat_path = project_root / "data" / "results" / "sensitivity_raw_stratified.csv"
    save_results(strat_results, strat_path, logger)
    
    # Combine for final summary
    all_results = cont_results + strat_results
    summary_path = project_root / "data" / "results" / "sensitivity_analysis.csv"
    save_results(all_results, summary_path, logger)
    
    logger.info("Sensitivity analysis completed.")

if __name__ == "__main__":
    main()