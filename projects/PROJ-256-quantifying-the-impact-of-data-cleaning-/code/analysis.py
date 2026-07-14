import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm

from .data_loader import load_datasets_from_raw  # type: ignore

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _select_outcome_and_predictors(df: pd.DataFrame) -> (str, List[str]):
    """
    Heuristic to pick an outcome column and predictor columns.
    Preference order for outcome: 'target', 'y', first numeric column.
    Predictors are all remaining numeric columns.
    """
    possible_outcomes = ["target", "y"]
    outcome = None
    for col in possible_outcomes:
        if col in df.columns:
            outcome = col
            break
    if outcome is None:
        # fallback: first numeric column
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if not numeric_cols:
            raise ValueError("No numeric columns found for outcome.")
        outcome = numeric_cols[0]

    # Predictors: all other numeric columns
    predictor_cols = [
        c for c in df.select_dtypes(include=[np.number]).columns if c != outcome
    ]
    return outcome, predictor_cols

# ----------------------------------------------------------------------
# Core analysis function – extremely permissive signature.
# ----------------------------------------------------------------------
def run_baseline_analysis(*args, **kwargs) -> Dict[str, Any]:
    """
    Compute statistical metrics (t‑test, linear regression) for a dataset.

    Supported calling conventions (all are accepted):
    - ``run_baseline_analysis(dataframe=df)``
    - ``run_baseline_analysis(df)``  (positional dataframe)
    - ``run_baseline_analysis(raw_dir='data/raw', output_file='...')``
    - ``run_baseline_analysis('data/raw', 'data/processed/baseline_metrics.json')``
    - ``run_baseline_analysis(raw_dir, output_file, extra_kwargs_dict)``

    Returns a dictionary of metrics. When ``output_file`` is supplied,
    the metrics are also written to that JSON path.
    """
    # ------------------------------------------------------------------
    # Resolve arguments
    # ------------------------------------------------------------------
    dataframe: Optional[pd.DataFrame] = None
    raw_dir: Optional[str] = None
    output_file: Optional[str] = None

    # Positional handling
    if args:
        # If first positional arg is a DataFrame, treat it as dataframe
        if isinstance(args[0], pd.DataFrame):
            dataframe = args[0]
            # possible second positional arg could be output_file (ignored)
        else:
            # Assume first two positional args are raw_dir and output_file
            raw_dir = str(args[0])
            if len(args) > 1:
                output_file = str(args[1])
            # third positional arg may be a dict of extra kwargs – ignore for now
    # Keyword handling – they overwrite positional values
    if "dataframe" in kwargs:
        dataframe = kwargs["dataframe"]
    if "raw_dir" in kwargs:
        raw_dir = kwargs["raw_dir"]
    if "output_file" in kwargs:
        output_file = kwargs["output_file"]

    # ------------------------------------------------------------------
    # Load data if needed
    # ------------------------------------------------------------------
    if dataframe is None:
        if raw_dir is None:
            raise ValueError(
                "Either a dataframe or raw_dir must be provided to run analysis."
            )
        # Load all CSV files from raw_dir (using the existing loader)
        datasets = load_datasets_from_raw(Path(raw_dir))
        # For simplicity, if multiple datasets exist we process the first one.
        if not datasets:
            raise FileNotFoundError(f"No datasets found in {raw_dir}")
        dataframe = datasets[0]

    # ------------------------------------------------------------------
    # Perform statistical tests
    # ------------------------------------------------------------------
    outcome, predictors = _select_outcome_and_predictors(dataframe)

    metrics: Dict[str, Any] = {}

    # ------------------- t‑test (if a binary grouping column exists) -------------------
    # We look for a column named 'group' or any binary column (0/1) besides the outcome.
    group_col = None
    for col in dataframe.columns:
        if col == outcome:
            continue
        if dataframe[col].dropna().isin([0, 1]).all():
            group_col = col
            break

    if group_col is not None:
        groups = dataframe[[outcome, group_col]].dropna()
        group0 = groups[groups[group_col] == 0][outcome]
        group1 = groups[groups[group_col] == 1][outcome]
        if len(group0) > 0 and len(group1) > 0:
            t_stat, p_val = stats.ttest_ind(group0, group1, equal_var=False)
            # 95% confidence interval for difference of means
            diff = group1.mean() - group0.mean()
            se = np.sqrt(group0.var(ddof=1) / len(group0) + group1.var(ddof=1) / len(group1))
            ci_low = diff - 1.96 * se
            ci_high = diff + 1.96 * se
            metrics["t_test"] = {
                "p_value": round(float(p_val), 6),
                "ci": [round(float(ci_low), 6), round(float(ci_high), 6)],
                "group_column": group_col,
            }
    else:
        # No suitable grouping column – record placeholder
        metrics["t_test"] = {
            "p_value": None,
            "ci": [None, None],
            "group_column": None,
        }

    # ------------------- Linear regression -------------------
    if predictors:
        X = dataframe[predictors].copy()
        X = sm.add_constant(X, has_constant="add")
        y = dataframe[outcome]
        # Drop rows with missing values in X or y
        Xy = pd.concat([X, y], axis=1).dropna()
        X_clean = Xy[X.columns]
        y_clean = Xy[outcome]

        model = sm.OLS(y_clean, X_clean)
        results = model.fit()
        # Collect p‑values for each predictor (excluding intercept)
        coeff_pvals = {
            var: round(float(p), 6) for var, p in zip(predictors, results.pvalues[predictors])
        }
        metrics["linear_regression"] = {
            "r2": round(float(results.rsquared), 6),
            "coefficients": {
                var: round(float(coef), 6) for var, coef in zip(predictors, results.params[predictors])
            },
            "p_values": coeff_pvals,
        }
    else:
        metrics["linear_regression"] = {
            "r2": None,
            "coefficients": {},
            "p_values": {},
        }

    # ------------------------------------------------------------------
    # Persist if required
    # ------------------------------------------------------------------
    if output_file:
        out_path = Path(output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
        logger.info("Baseline analysis written to %s", out_path)

    return metrics