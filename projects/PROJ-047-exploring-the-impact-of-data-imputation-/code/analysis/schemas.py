"""
Pydantic schemas for strict validation of simulation outputs.
Implements T053: Schema Rigor.
"""
from typing import Optional, List, Literal, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime


class SimulationSummaryRow(BaseModel):
    """
    Pydantic model for a single row in simulation_summary.csv.
    Validates types and required fields for T029c output.
    """
    beta: float
    method: Literal["mean", "knn", "mice"]
    estimator: Literal["ipw", "psm"]
    ate: Optional[float] = None  # Can be NaN for failed runs
    bias: Optional[float] = None
    rmse: Optional[float] = None
    coverage_rate: Optional[float] = None
    seed: int
    run_id: str
    ground_truth_ate: float
    status: Literal["success", "failed", "warning"] = "success"
    vif: Optional[float] = None
    mnar_correlation: Optional[float] = None
    mnar_p_value: Optional[float] = None

    @field_validator('ate', 'bias', 'rmse', 'coverage_rate', 'vif', 'mnar_correlation', 'mnar_p_value')
    @classmethod
    def validate_float_or_nan(cls, v):
        """Allow None or float, converting NaN to None for Pydantic compatibility if needed,
        but primarily ensuring it's a valid number if present."""
        if v is None:
            return None
        if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
            return None
        return float(v)

    @field_validator('beta', 'seed', 'ground_truth_ate')
    @classmethod
    def ensure_numeric(cls, v):
        if v is None:
            raise ValueError("beta, seed, and ground_truth_ate cannot be None")
        return v

    class Config:
        # Allow population by field name (for CSV loading)
        populate_by_name = True


class StatisticalTestResults(BaseModel):
    """
    Pydantic model for statistical_test_results.json.
    Validates T028 output schema.
    """
    test_type: Literal["anova", "friedman"]
    p_value: float
    test_statistic: float
    skewness: float
    bootstrap_ci_diff: Optional[float] = None

    @model_validator(mode='after')
    def check_bootstrap_requirement(self):
        """
        If |skewness| > 1, bootstrap_ci_diff MUST be populated (not null).
        This enforces the FR-006 decision tree requirement.
        """
        if abs(self.skewness) > 1.0:
            if self.bootstrap_ci_diff is None:
                raise ValueError(
                    "bootstrap_ci_diff is required when |skewness| > 1.0. "
                    "Set it to a float value or 0.0 if calculation failed."
                )
        else:
            # If skewness is low, we can set it to 0.0 or None for determinism
            if self.bootstrap_ci_diff is None:
                object.__setattr__(self, 'bootstrap_ci_diff', 0.0)
        return self


def validate_simulation_summary_csv(df: pd.DataFrame) -> List[SimulationSummaryRow]:
    """
    Validates a DataFrame against the SimulationSummaryRow schema.
    Raises ValueError if validation fails.
    """
    required_columns = [
        'beta', 'method', 'estimator', 'ate', 'bias', 'rmse', 'coverage_rate',
        'seed', 'run_id', 'ground_truth_ate', 'status', 'vif', 'mnar_correlation', 'mnar_p_value'
    ]
    
    missing_cols = set(required_columns) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns in simulation_summary.csv: {missing_cols}")

    validated_rows = []
    errors = []
    
    for idx, row in df.iterrows():
        try:
            # Convert row to dict, handling NaN values explicitly
            row_dict = row.to_dict()
            for key, val in row_dict.items():
                if isinstance(val, float) and (np.isnan(val) or np.isinf(val)):
                    row_dict[key] = None
            
            validated_rows.append(SimulationSummaryRow(**row_dict))
        except Exception as e:
            errors.append(f"Row {idx}: {str(e)}")
    
    if errors:
        raise ValueError(f"Validation failed for {len(errors)} rows:\n" + "\n".join(errors))
    
    return validated_rows


def validate_statistical_test_results(data: Dict[str, Any]) -> StatisticalTestResults:
    """
    Validates a dictionary against the StatisticalTestResults schema.
    Raises ValueError if validation fails.
    """
    try:
        return StatisticalTestResults(**data)
    except Exception as e:
        raise ValueError(f"Statistical test results validation failed: {str(e)}")


def load_and_validate_simulation_summary(filepath: str) -> pd.DataFrame:
    """
    Loads a CSV and validates it against the SimulationSummaryRow schema.
    Returns the original DataFrame if valid.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    df = pd.read_csv(filepath)
    validate_simulation_summary_csv(df)
    return df


def load_and_validate_statistical_test(filepath: str) -> StatisticalTestResults:
    """
    Loads a JSON and validates it against the StatisticalTestResults schema.
    Returns the validated model instance.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    return validate_statistical_test_results(data)
