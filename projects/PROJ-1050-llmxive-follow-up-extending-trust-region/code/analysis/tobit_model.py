import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
import numpy as np
import pandas as pd
from statsmodels.regression.tobit import Tobit

from utils.logger import get_logger

logger = get_logger(__name__)


class TobitModel:
    """
    Wrapper for statsmodels Tobit regression to analyze reasoning collapse.
    
    This model handles censored data where the observed effective depth
    may be capped by the student's cognitive horizon, while the teacher
    depth represents the true optimal path length.
    """

    def __init__(
        self,
        lower_bound: float = 0.0,
        upper_bound: Optional[float] = None,
        seed: Optional[int] = None
    ):
        """
        Initialize the Tobit model.
        
        Args:
            lower_bound: Lower censoring limit (default 0.0 for depth).
            upper_bound: Upper censoring limit (default None, infinite).
            seed: Random seed for reproducibility if needed.
        """
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.seed = seed
        self.model = None
        self.results = None
        self.logger = get_logger(__name__)

    def fit(
        self,
        y: np.ndarray,
        X: np.ndarray,
        col_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Fit the Tobit regression model.
        
        Args:
            y: 1D array of dependent variable (effective depth).
            X: 2D array of independent variables (features).
            col_names: Optional list of column names for features.
        
        Returns:
            Dictionary containing model results and statistics.
        """
        if len(y) == 0:
            raise ValueError("Cannot fit Tobit model with empty data.")
        
        if X.shape[0] != len(y):
            raise ValueError("X and y must have the same number of observations.")

        self.logger.info(f"Fitting Tobit model with lower_bound={self.lower_bound}, "
                       f"upper_bound={self.upper_bound}")

        try:
            # statsmodels Tobit expects 2D y
            y_2d = y.reshape(-1, 1)
            
            self.model = Tobit(
                y_2d,
                X,
                lower=self.lower_bound,
                upper=self.upper_bound
            )
            self.results = self.model.fit()
            
            return {
                "success": True,
                "coefficients": self.results.params,
                "standard_errors": self.results.bse,
                "p_values": self.results.pvalues,
                "log_likelihood": self.results.llf,
                "aic": self.results.aic,
                "bic": self.results.bic,
                "n_obs": self.results.nobs,
                "censored_count": self._count_censored(y),
                "uncensored_count": self.results.nobs - self._count_censored(y)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to fit Tobit model: {e}")
            raise

    def _count_censored(self, y: np.ndarray) -> int:
        """Count number of censored observations."""
        count = 0
        if self.lower_bound is not None:
            count += np.sum(y <= self.lower_bound)
        if self.upper_bound is not None:
            count += np.sum(y >= self.upper_bound)
        # Note: observations at both bounds are counted once
        return int(count)

    def detect_collapse(
        self,
        df: pd.DataFrame,
        effective_depth_col: str = "effective_depth",
        teacher_depth_col: str = "teacher_depth",
        collapse_threshold: float = 0.5
    ) -> pd.DataFrame:
        """
        Detect reasoning collapse in the dataset.
        
        Collapse is defined as effective_depth <= collapse_threshold * teacher_depth.
        
        Args:
            df: DataFrame containing training episode logs.
            effective_depth_col: Column name for effective depth.
            teacher_depth_col: Column name for teacher depth.
            collapse_threshold: Ratio threshold for collapse (default 0.5).
        
        Returns:
            DataFrame with an additional 'is_collapse' boolean column.
        """
        if effective_depth_col not in df.columns:
            raise ValueError(f"Column '{effective_depth_col}' not found in DataFrame.")
        if teacher_depth_col not in df.columns:
            raise ValueError(f"Column '{teacher_depth_col}' not found in DataFrame.")

        self.logger.info(f"Detecting collapse using threshold: {collapse_threshold}")
        
        # Calculate collapse condition: effective_depth <= threshold * teacher_depth
        # Handle potential division by zero or invalid teacher_depth
        valid_mask = df[teacher_depth_col] > 0
        collapse_mask = pd.Series(False, index=df.index)
        
        if valid_mask.any():
            threshold_values = collapse_threshold * df.loc[valid_mask, teacher_depth_col]
            collapse_mask.loc[valid_mask] = df.loc[valid_mask, effective_depth_col] <= threshold_values

        df_with_collapse = df.copy()
        df_with_collapse["is_collapse"] = collapse_mask

        collapse_count = collapse_mask.sum()
        total_count = len(df)
        collapse_ratio = collapse_count / total_count if total_count > 0 else 0.0

        self.logger.info(f"Collapse detected in {collapse_count}/{total_count} episodes "
                       f"({collapse_ratio:.2%})")

        return df_with_collapse

    def run_sensitivity_analysis(
        self,
        df: pd.DataFrame,
        feature_cols: List[str],
        effective_depth_col: str = "effective_depth",
        teacher_depth_col: str = "teacher_depth",
        alpha_col: str = "alpha",
        horizon_col: str = "horizon",
        collapse_threshold: float = 0.5
    ) -> Dict[str, Any]:
        """
        Run sensitivity analysis across different alpha and horizon values.
        
        Args:
            df: DataFrame with training logs.
            feature_cols: List of feature columns for Tobit regression.
            effective_depth_col: Column for effective depth.
            teacher_depth_col: Column for teacher depth.
            alpha_col: Column for alpha parameter.
            horizon_col: Column for student horizon.
            collapse_threshold: Threshold for collapse detection.
        
        Returns:
            Dictionary with analysis results per (alpha, horizon) group.
        """
        # First, detect collapse
        df_analyzed = self.detect_collapse(
            df,
            effective_depth_col=effective_depth_col,
            teacher_depth_col=teacher_depth_col,
            collapse_threshold=collapse_threshold
        )

        # Group by alpha and horizon
        groups = df_analyzed.groupby([alpha_col, horizon_col])
        
        results = {
            "groups": [],
            "aggregated_stats": {}
        }

        for (alpha_val, horizon_val), group_df in groups:
            group_data = {
                "alpha": alpha_val,
                "horizon": horizon_val,
                "n_obs": len(group_df),
                "collapse_count": group_df["is_collapse"].sum(),
                "collapse_ratio": group_df["is_collapse"].mean(),
                "mean_effective_depth": group_df[effective_depth_col].mean(),
                "mean_teacher_depth": group_df[teacher_depth_col].mean(),
                "std_effective_depth": group_df[effective_depth_col].std()
            }

            # Prepare data for Tobit regression if enough samples
            if len(group_df) >= 10 and len(feature_cols) > 0:
                X = group_df[feature_cols].values
                y = group_df[effective_depth_col].values
                
                try:
                    tobit_result = self.fit(y, X)
                    if tobit_result["success"]:
                        group_data["tobit_coefficients"] = tobit_result["coefficients"].tolist()
                        group_data["tobit_p_values"] = tobit_result["p_values"].tolist()
                        group_data["tobit_log_likelihood"] = tobit_result["log_likelihood"]
                        group_data["censored_ratio"] = tobit_result["censored_count"] / tobit_result["n_obs"]
                except Exception as e:
                    self.logger.warning(f"Tobit fit failed for alpha={alpha_val}, horizon={horizon_val}: {e}")
                    group_data["tobit_error"] = str(e)

            results["groups"].append(group_data)

        # Aggregate statistics
        if results["groups"]:
            all_collapses = [g["collapse_ratio"] for g in results["groups"]]
            results["aggregated_stats"] = {
                "mean_collapse_ratio": np.mean(all_collapses),
                "std_collapse_ratio": np.std(all_collapses),
                "max_collapse_ratio": np.max(all_collapses),
                "min_collapse_ratio": np.min(all_collapses),
                "total_groups": len(results["groups"])
            }

        self.logger.info(f"Sensitivity analysis completed for {len(results['groups'])} groups")
        return results

    def export_results(
        self,
        results: Dict[str, Any],
        output_path: Path
    ) -> None:
        """
        Export analysis results to a CSV file.
        
        Args:
            results: Dictionary containing analysis results.
            output_path: Path to write the output CSV.
        """
        if not results.get("groups"):
            self.logger.warning("No groups to export.")
            return

        df_results = pd.DataFrame(results["groups"])
        
        # Flatten nested dictionaries if any
        df_flat = pd.json_normalize(df_results)
        
        df_flat.to_csv(output_path, index=False)
        self.logger.info(f"Exported results to {output_path}")