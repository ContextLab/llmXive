import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Any, List, Optional
from utils.logger import get_logger
import os

logger = get_logger(__name__)

class StatUtils:
    """
    Utility class for statistical analysis operations.
    """

    @staticmethod
    def shapiro_wilk_test(data: np.ndarray) -> Dict[str, Any]:
        """
        Perform Shapiro-Wilk normality test on the provided data.

        Args:
            data: numpy array of values to test.

        Returns:
            Dictionary containing 'statistic' and 'pvalue'.
        """
        if len(data) < 3:
            logger.warning("Insufficient data points for Shapiro-Wilk test (n < 3).")
            return {"statistic": None, "pvalue": None}

        try:
            stat, p_value = stats.shapiro(data)
            return {"statistic": float(stat), "pvalue": float(p_value)}
        except Exception as e:
            logger.error(f"Shapiro-Wilk test failed: {e}")
            return {"statistic": None, "pvalue": None, "error": str(e)}

    @staticmethod
    def repeated_measures_anova(data: pd.DataFrame, 
                                subject_col: str, 
                                within_col: str, 
                                value_col: str) -> Dict[str, Any]:
        """
        Perform Repeated Measures ANOVA on the provided data.
        
        Note: This implementation uses scipy.stats.f_oneway as a proxy for 
        independent groups if a full rm-anova library is not available, 
        or performs a simplified calculation. For strict RM-ANOVA, 
        statsmodels or pingouin is typically required, but we stick to 
        scipy/numpy as per constraints unless specified otherwise.
        
        However, to provide a valid RM-ANOVA with only scipy/numpy/pandas:
        We will calculate the F-statistic manually or use a simplified approach
        if the data structure allows.
        
        For this implementation, we assume the data is in long format.
        We will perform a standard ANOVA on the groups defined by `within_col`
        after accounting for subject variability if possible, or fall back 
        to a standard one-way ANOVA on the differences if applicable.
        
        Given the constraints and typical usage in this project:
        We will compute the F-statistic for the within-subject factor.
        
        Args:
            data: DataFrame with columns for subject, within-factor, and value.
            subject_col: Name of the column identifying subjects.
            within_col: Name of the column identifying the within-subject condition.
            value_col: Name of the column containing the measured values.

        Returns:
            Dictionary with F-statistic, p-value, and degrees of freedom.
        """
        try:
            # Pivot to wide format for standard ANOVA calculation
            # This assumes each subject has exactly one value per condition
            wide_data = data.pivot_table(index=subject_col, columns=within_col, values=value_col)
            
            # Extract arrays for each group
            groups = [wide_data[col].dropna().values for col in wide_data.columns]
            
            if any(len(g) < 2 for g in groups):
                logger.warning("Not enough data points per group for ANOVA.")
                return {"f_statistic": None, "p_value": None, "df": None, "error": "Insufficient data"}

            # Perform one-way ANOVA (approximation for RM-ANOVA if subject effect is removed via pivot)
            # Note: True RM-ANOVA removes subject variance. 
            # A simple f_oneway on the wide data columns treats them as independent, which is incorrect for RM.
            # To do it properly with scipy only, we calculate the ANOVA on the differences or use a manual formula.
            # Given the task constraints, we will implement a manual RM-ANOVA calculation.
            
            n_subjects = len(wide_data)
            k_conditions = len(wide_data.columns)
            
            if n_subjects < 2 or k_conditions < 2:
                return {"f_statistic": None, "p_value": None, "df": None, "error": "Insufficient subjects or conditions"}

            # Calculate Means
            grand_mean = wide_data.values.mean()
            subject_means = wide_data.mean(axis=1).values
            condition_means = wide_data.mean(axis=0).values

            # Sum of Squares Total
            ss_total = np.sum((wide_data.values - grand_mean) ** 2)
            
            # Sum of Squares Between Subjects
            ss_subjects = k_conditions * np.sum((subject_means - grand_mean) ** 2)
            
            # Sum of Squares Between Conditions (Treatment)
            ss_conditions = n_subjects * np.sum((condition_means - grand_mean) ** 2)
            
            # Sum of Squares Error (Residual)
            ss_error = ss_total - ss_subjects - ss_conditions
            
            if ss_error <= 0:
                logger.warning("SS Error is zero or negative, cannot compute F-statistic.")
                return {"f_statistic": None, "p_value": None, "df": None, "error": "SS Error <= 0"}

            # Degrees of Freedom
            df_conditions = k_conditions - 1
            df_error = (n_subjects - 1) * (k_conditions - 1)
            
            # Mean Squares
            ms_conditions = ss_conditions / df_conditions
            ms_error = ss_error / df_error
            
            # F-statistic
            f_stat = ms_conditions / ms_error
            
            # P-value
            p_val = 1 - stats.f.cdf(f_stat, df_conditions, df_error)
            
            return {
                "f_statistic": float(f_stat),
                "p_value": float(p_val),
                "df": (int(df_conditions), int(df_error)),
                "ss_conditions": float(ss_conditions),
                "ss_error": float(ss_error),
                "ms_conditions": float(ms_conditions),
                "ms_error": float(ms_error)
            }

        except Exception as e:
            logger.error(f"Repeated Measures ANOVA failed: {e}")
            return {"f_statistic": None, "p_value": None, "df": None, "error": str(e)}

    @staticmethod
    def holm_bonferroni_correction(p_values: List[float]) -> List[float]:
        """
        Apply Holm-Bonferroni correction to a list of p-values.

        Args:
            p_values: List of raw p-values.

        Returns:
            List of adjusted p-values.
        """
        if not p_values:
            return []

        n = len(p_values)
        sorted_indices = np.argsort(p_values)
        sorted_p_values = [p_values[i] for i in sorted_indices]
        
        adjusted_p_values = [0.0] * n
        min_alpha = 1.0
        
        for i, p in enumerate(sorted_p_values):
            # Holm-Bonferroni step: p * (n - i)
            # Ensure it doesn't exceed 1.0 and doesn't decrease from previous step
            adjusted = p * (n - i)
            adjusted = min(1.0, max(adjusted, min_alpha)) # Monotonicity constraint
            min_alpha = adjusted
            adjusted_p_values[sorted_indices[i]] = adjusted
            
        return adjusted_p_values

    @staticmethod
    def calculate_effect_size(mean1: float, std1: float, n1: int, 
                              mean2: float, std2: float, n2: int) -> Dict[str, float]:
        """
        Calculate Cohen's d effect size for two independent groups.
        For paired data (like RM-ANOVA), a different calculation is needed, 
        but this is a general utility.
        
        For paired data, we would need the correlation or the std of differences.
        Given the context, we will implement a simplified version for independent groups
        or return None if it's clearly paired and we lack correlation data.
        
        However, for the specific task of RM-ANOVA effect size (Partial Eta Squared):
        eta_squared = SS_conditions / (SS_conditions + SS_error)
        
        Let's add a specific method for Partial Eta Squared if we have the SS values.
        """
        # Standard independent t-test Cohen's d
        pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
        if pooled_std == 0:
            return {"cohens_d": 0.0, "interpretation": "zero"}
        
        d = (mean1 - mean2) / pooled_std
        return {"cohens_d": float(d)}

    @staticmethod
    def calculate_partial_eta_squared(ss_conditions: float, ss_error: float) -> float:
        """
        Calculate Partial Eta Squared for ANOVA.
        eta^2 = SS_effect / (SS_effect + SS_error)
        """
        if ss_conditions + ss_error == 0:
            return 0.0
        return ss_conditions / (ss_conditions + ss_error)

    @staticmethod
    def compute_descriptive_stats(data: pd.DataFrame, 
                                  metric: str, 
                                  group_col: Optional[str] = None) -> pd.DataFrame:
        """
        Compute descriptive statistics (mean, std) for a specific metric.
        
        Args:
            data: Input DataFrame.
            metric: Column name to compute stats for.
            group_col: Optional column to group by (e.g., interface_type).
        
        Returns:
            DataFrame with descriptive statistics.
        """
        if metric not in data.columns:
            logger.warning(f"Metric '{metric}' not found in data columns.")
            return pd.DataFrame()

        if group_col:
            if group_col not in data.columns:
                logger.warning(f"Group column '{group_col}' not found.")
                return pd.DataFrame()
            
            stats_df = data.groupby(group_col)[metric].agg(['mean', 'std', 'count']).reset_index()
            stats_df.columns = [group_col, 'mean', 'std', 'count']
        else:
            mean_val = data[metric].mean()
            std_val = data[metric].std()
            count_val = data[metric].count()
            stats_df = pd.DataFrame({
                'metric': [metric],
                'mean': [mean_val],
                'std': [std_val],
                'count': [count_val]
            })

        return stats_df

    @staticmethod
    def generate_descriptive_stats_csv(output_path: str, 
                                       raw_data_path: str,
                                       metric: str = "explanation_engagement_time") -> bool:
        """
        Main entry point to generate the descriptive statistics CSV file.
        Loads raw session data, computes stats for the specified metric, 
        and saves to the output path.
        
        Args:
            output_path: Path to save the CSV.
            raw_data_path: Path or glob pattern to raw session JSON files.
            metric: The metric to analyze (default: explanation_engagement_time).
        
        Returns:
            True if successful, False otherwise.
        """
        logger.info(f"Generating descriptive stats for '{metric}' from {raw_data_path}")
        
        try:
            # Load data
            raw_files = []
            if os.path.isdir(raw_data_path):
                raw_files = [f for f in os.listdir(raw_data_path) if f.endswith('.json')]
                raw_files = [os.path.join(raw_data_path, f) for f in raw_files]
            elif os.path.isfile(raw_data_path):
                raw_files = [raw_data_path]
            else:
                # Assume glob pattern
                import glob as glob_module
                raw_files = glob_module.glob(raw_data_path)

            if not raw_files:
                logger.error(f"No raw data files found matching {raw_data_path}")
                return False

            all_data = []
            for f_path in raw_files:
                try:
                    with open(f_path, 'r') as f:
                        data = json.load(f)
                        # Flatten if necessary or extract specific field
                        # Assuming data structure has 'metrics' or direct fields
                        # Based on T019, session logs contain metrics.
                        # We need to handle the structure defined in T007/T019.
                        # Assuming a structure like: { "metrics": { "explanation_engagement_time": 12.5 }, ... }
                        # or direct fields.
                        
                        # Let's assume the session log structure from T007/T019
                        # Session model: session_id, participant_id, interface_type, ... error_count, explanation_engagement_time_seconds, sus_score
                        # If the JSON matches the Session model:
                        
                        val = data.get(metric) or data.get(metric + "_seconds")
                        if val is not None:
                            all_data.append({
                                "session_id": data.get("session_id"),
                                "interface_type": data.get("interface_type"),
                                "metric_value": float(val)
                            })
                except Exception as e:
                    logger.warning(f"Failed to parse {f_path}: {e}")
                    continue

            if not all_data:
                logger.error("No valid data points found for the metric.")
                # Create an empty file with headers to indicate failure/no data
                df_empty = pd.DataFrame(columns=["interface_type", "mean", "std", "count"])
                df_empty.to_csv(output_path, index=False)
                return False

            df = pd.DataFrame(all_data)
            
            # Calculate stats per interface type
            if "interface_type" in df.columns:
                result_df = df.groupby("interface_type")["metric_value"].agg(['mean', 'std', 'count']).reset_index()
                result_df.columns = ["interface_type", "mean", "std", "count"]
            else:
                # Global stats
                mean_val = df["metric_value"].mean()
                std_val = df["metric_value"].std()
                count_val = df["metric_value"].count()
                result_df = pd.DataFrame({
                    "interface_type": ["All"],
                    "mean": [mean_val],
                    "std": [std_val],
                    "count": [count_val]
                })

            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            result_df.to_csv(output_path, index=False)
            logger.info(f"Descriptive stats saved to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to generate descriptive stats: {e}")
            return False

def main():
    """
    Main function to run the descriptive stats generation.
    """
    import sys
    from pathlib import Path
    from config.settings import get_settings

    settings = get_settings()
    raw_data_dir = settings.data_raw_dir
    output_file = settings.data_processed_dir / "descriptive_stats.csv"
    
    # Ensure paths are strings for the function
    raw_path_str = str(raw_data_dir)
    output_path_str = str(output_file)
    
    success = StatUtils.generate_descriptive_stats_csv(
        output_path=output_path_str,
        raw_data_path=raw_path_str,
        metric="explanation_engagement_time"
    )
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
