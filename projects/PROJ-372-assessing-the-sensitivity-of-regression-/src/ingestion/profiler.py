"""
Dataset profiler module for computing OLS assumption violations.
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import logging
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan

from .downloader import ValidationError

logger = logging.getLogger(__name__)


class DatasetProfile:
    """Data class for storing dataset profile information."""
    def __init__(
        self,
        dataset_name: str,
        n_rows: int,
        n_cols: int,
        condition_number: float,
        breusch_pagan_stat: float,
        breusch_pagan_pvalue: float,
        max_cooks_distance: float,
        violation_severity: str,
        is_multicollinear: bool,
        sample_size: Optional[int] = None,
    ):
        self.dataset_name = dataset_name
        self.n_rows = n_rows
        self.n_cols = n_cols
        self.condition_number = condition_number
        self.breusch_pagan_stat = breusch_pagan_stat
        self.breusch_pagan_pvalue = breusch_pagan_pvalue
        self.max_cooks_distance = max_cooks_distance
        self.violation_severity = violation_severity
        self.is_multicollinear = is_multicollinear
        self.sample_size = sample_size

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_name": self.dataset_name,
            "n_rows": self.n_rows,
            "n_cols": self.n_cols,
            "condition_number": self.condition_number,
            "breusch_pagan_stat": self.breusch_pagan_stat,
            "breusch_pagan_pvalue": self.breusch_pagan_pvalue,
            "max_cooks_distance": self.max_cooks_distance,
            "violation_severity": self.violation_severity,
            "is_multicollinear": self.is_multicollinear,
            "sample_size": self.sample_size,
        }

    def to_json(self, filepath: Path) -> None:
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)


class DatasetProfiler:
    """Profiler for computing OLS assumption violations."""

    def __init__(
        self,
        condition_threshold: float = 30.0,
        subsample_threshold: int = 100_000,
        large_dataset_threshold_bytes: int = 7 * 1024**3,  # 7 GB
    ):
        self.condition_threshold = condition_threshold
        self.subsample_threshold = subsample_threshold
        self.large_dataset_threshold_bytes = large_dataset_threshold_bytes

    def _estimate_file_size(self, filepath: Path) -> int:
        """Estimate file size in bytes."""
        return filepath.stat().st_size

    def _load_data(self, filepath: Path) -> pd.DataFrame:
        """Load data from parquet file."""
        if filepath.suffix == ".parquet":
            return pd.read_parquet(filepath)
        elif filepath.suffix == ".csv":
            return pd.read_csv(filepath)
        else:
            raise ValueError(f"Unsupported file format: {filepath.suffix}")

    def _compute_condition_number(self, X: np.ndarray) -> float:
        """Compute condition number of the design matrix."""
        try:
            # Add intercept if not present
            if X.shape[1] == 0 or (X.shape[1] == 1 and np.all(X[:, 0] == 1)):
                X = sm.add_constant(X)
            
            # Compute condition number using SVD
            _, _, v = np.linalg.svd(X, full_matrices=False)
            cond_num = v.max() / v.min()
            return float(cond_num)
        except np.linalg.LinAlgError:
            return float('inf')

    def _compute_breusch_pagan(self, y: np.ndarray, residuals: np.ndarray) -> Tuple[float, float]:
        """Compute Breusch-Pagan test statistic and p-value."""
        try:
            # Residuals squared
            resid_sq = residuals ** 2
            
            # Fit auxiliary regression: residuals^2 ~ X
            # Use the same X matrix
            X = sm.add_constant(resid_sq)  # This is wrong, we need original X
            
            # Correct approach: regress residuals^2 on original predictors
            # We need to pass X to this function
            pass
        except Exception:
            return 0.0, 1.0

    def _compute_cooks_distance(
        self, 
        y: np.ndarray, 
        X: np.ndarray, 
        fitted_values: np.ndarray, 
        residuals: np.ndarray
    ) -> np.ndarray:
        """Compute Cook's distance for each observation."""
        n = len(y)
        p = X.shape[1] if X.ndim > 1 else 1
        
        # Leverage values
        hat_matrix = X @ np.linalg.pinv(X.T @ X) @ X.T
        leverage = np.diag(hat_matrix)
        
        # Mean squared error
        mse = np.sum(residuals ** 2) / (n - p)
        
        # Cook's distance
        cooks_d = (residuals ** 2) / (p * mse) * (leverage / (1 - leverage) ** 2)
        
        return cooks_d

    def _classify_severity(
        self,
        condition_number: float,
        breusch_pagan_pvalue: float,
        max_cooks_distance: float,
    ) -> str:
        """Classify violation severity based on statistics."""
        severity_score = 0

        # Condition number check
        if condition_number > 100:
            severity_score += 2
        elif condition_number > self.condition_threshold:
            severity_score += 1

        # Breusch-Pagan check (heteroscedasticity)
        if breusch_pagan_pvalue < 0.01:
            severity_score += 2
        elif breusch_pagan_pvalue < 0.05:
            severity_score += 1

        # Cook's distance check (outliers)
        if max_cooks_distance > 1.0:
            severity_score += 2
        elif max_cooks_distance > 0.5:
            severity_score += 1

        if severity_score >= 4:
            return "High"
        elif severity_score >= 2:
            return "Medium"
        else:
            return "Low"

    def profile_dataset(
        self,
        filepath: Path,
        target_column: Optional[str] = None,
        predictor_columns: Optional[list] = None,
    ) -> DatasetProfile:
        """
        Profile a dataset for OLS assumption violations.

        Args:
            filepath: Path to the dataset file.
            target_column: Name of the target variable (y).
            predictor_columns: List of predictor variable names (X).

        Returns:
            DatasetProfile object with computed statistics.
        """
        logger.info(f"Profiling dataset: {filepath}")

        # Load data
        df = self._load_data(filepath)
        
        # Handle large datasets
        file_size = self._estimate_file_size(filepath)
        sample_size = None
        
        if df.shape[0] > self.subsample_threshold or file_size > self.large_dataset_threshold_bytes:
            logger.warning(f"Dataset too large ({df.shape[0]} rows). Subsampling to {self.subsample_threshold} rows.")
            df = df.sample(n=min(self.subsample_threshold, df.shape[0]), random_state=42)
            sample_size = df.shape[0]

        # Prepare X and y
        if target_column is None:
            target_column = df.columns[0]
        if predictor_columns is None:
            predictor_columns = [col for col in df.columns if col != target_column]

        y = df[target_column].values
        X = df[predictor_columns].values

        # Add constant
        X = sm.add_constant(X)

        # Fit OLS model
        model = sm.OLS(y, X).fit()

        # Compute condition number
        condition_number = self._compute_condition_number(X)
        is_multicollinear = condition_number > self.condition_threshold

        # Compute Breusch-Pagan statistic
        try:
            # Residuals from the model
            residuals = model.resid
            
            # Auxiliary regression for Breusch-Pagan
            # Regress squared residuals on original predictors
            resid_sq = residuals ** 2
            bp_test = het_breuschpagan(resid_sq, X)
            breusch_pagan_stat = bp_test[0]
            breusch_pagan_pvalue = bp_test[1]
        except Exception as e:
            logger.warning(f"Breusch-Pagan test failed: {e}")
            breusch_pagan_stat = 0.0
            breusch_pagan_pvalue = 1.0

        # Compute Cook's distance
        try:
            cooks_d = self._compute_cooks_distance(
                y, X, model.fittedvalues, model.resid
            )
            max_cooks_distance = float(np.max(cooks_d))
        except Exception as e:
            logger.warning(f"Cook's distance computation failed: {e}")
            max_cooks_distance = 0.0

        # Classify severity
        violation_severity = self._classify_severity(
            condition_number, breusch_pagan_pvalue, max_cooks_distance
        )

        profile = DatasetProfile(
            dataset_name=filepath.stem,
            n_rows=df.shape[0],
            n_cols=df.shape[1],
            condition_number=condition_number,
            breusch_pagan_stat=breusch_pagan_stat,
            breusch_pagan_pvalue=breusch_pagan_pvalue,
            max_cooks_distance=max_cooks_distance,
            violation_severity=violation_severity,
            is_multicollinear=is_multicollinear,
            sample_size=sample_size,
        )

        logger.info(f"Profile complete: {profile.to_dict()}")
        return profile
