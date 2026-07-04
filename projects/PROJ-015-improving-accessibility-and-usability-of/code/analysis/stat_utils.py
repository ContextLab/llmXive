import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Any, List, Optional
from utils.logger import get_logger
import os
from pathlib import Path

logger = get_logger(__name__)

class StatUtils:
    """
    Utility class for statistical analysis methods used in the research pipeline.
    """

    @staticmethod
    def run_shapiro_wilk(data: pd.Series) -> Dict[str, float]:
        """
        Perform Shapiro-Wilk normality test on a sample.

        Args:
            data: A pandas Series containing the sample data.

        Returns:
            Dictionary with 'statistic' and 'pvalue'.
        """
        if len(data) < 3:
            logger.warning("Sample size too small for Shapiro-Wilk test (< 3).")
            return {"statistic": np.nan, "pvalue": np.nan}

        stat, p_value = stats.shapiro(data)
        return {"statistic": float(stat), "pvalue": float(p_value)}

    @staticmethod
    def run_repeated_measures_anova(df: pd.DataFrame, 
                                    within_subject_col: str, 
                                    dependent_col: str, 
                                    subject_col: str = 'participant_id') -> Dict[str, Any]:
        """
        Perform Repeated Measures ANOVA using scipy.stats.f_oneway on 
        differences or by reshaping if strictly necessary, but for 
        standard implementation without pingouin, we approximate or 
        calculate manually if data structure permits.
        
        Note: scipy.stats.f_oneway is for independent samples. 
        For Repeated Measures without pingouin, we often calculate 
        the F-statistic manually or use a simplified approach.
        
        However, per project constraints (scipy only), we will implement
        a manual calculation for the F-statistic if the data is in wide format,
        or perform the test on the difference scores if comparing two conditions.
        
        For this implementation, assuming a comparison between two conditions 
        (Traditional vs Explainable) for a single metric, we can use a paired t-test
        which is mathematically equivalent to RM-ANOVA for 2 levels.
        
        If >2 levels are needed, a full manual implementation is complex.
        Given the context of "Traditional vs Explainable", we assume 2 levels.
        
        Args:
            df: DataFrame with columns for subject, condition, and metric.
            within_subject_col: Column name for the condition (e.g., 'interface_type').
            dependent_col: Column name for the metric (e.g., 'completion_time').
            subject_col: Column name for the participant ID.

        Returns:
            Dictionary with F-statistic, p-value, and method description.
        """
        if within_subject_col not in df.columns or dependent_col not in df.columns or subject_col not in df.columns:
            raise ValueError(f"Required columns {within_subject_col}, {dependent_col}, {subject_col} not found in DataFrame.")

        unique_conditions = df[within_subject_col].unique()
        
        if len(unique_conditions) == 2:
            # Paired t-test is equivalent to RM-ANOVA for 2 conditions
            cond_a = df[df[within_subject_col] == unique_conditions[0]][dependent_col]
            cond_b = df[df[within_subject_col] == unique_conditions[1]][dependent_col]
            
            # Ensure they are paired (same participants)
            # Assuming the dataframe is already filtered or sorted such that 
            # rows correspond to the same participant in the same order, 
            # or we merge by subject.
            # A safer approach: pivot to wide format
            try:
                wide_df = df.pivot_table(index=subject_col, columns=within_subject_col, values=dependent_col)
                t_stat, p_val = stats.ttest_rel(wide_df[unique_conditions[0]], wide_df[unique_conditions[1]])
                return {
                    "F_statistic": float(t_stat**2), # F = t^2 for 2 groups
                    "p_value": float(p_val),
                    "method": "Paired t-test (equivalent to RM-ANOVA for 2 conditions)",
                    "degrees_of_freedom": len(wide_df) - 1
                }
            except Exception as e:
                logger.error(f"Failed to pivot data for paired t-test: {e}")
                return {"F_statistic": np.nan, "p_value": np.nan, "error": str(e)}
        else:
            # For >2 conditions, scipy doesn't have a direct RM-ANOVA.
            # We would need to calculate manually or use a different library.
            # For now, we return a placeholder or raise an error if strict compliance is needed.
            # Given the task context (Traditional vs Explainable), 2 conditions is expected.
            logger.warning(f"RM-ANOVA for >2 conditions not fully implemented in scipy-only mode. Found {len(unique_conditions)} conditions.")
            return {"F_statistic": np.nan, "p_value": np.nan, "method": "Not implemented for >2 conditions without pingouin"}

    @staticmethod
    def calculate_descriptive_stats(df: pd.DataFrame, metric_name: str, group_col: Optional[str] = None) -> pd.DataFrame:
        """
        Calculate descriptive statistics (mean, std, count, min, max) for a metric.
        Optionally grouped by a specific column (e.g., interface_type).

        Args:
            df: Input DataFrame.
            metric_name: Name of the column to calculate stats for.
            group_col: Optional column name to group by.

        Returns:
            DataFrame with descriptive statistics.
        """
        if metric_name not in df.columns:
            raise ValueError(f"Metric '{metric_name}' not found in DataFrame.")

        if group_col:
            if group_col not in df.columns:
                raise ValueError(f"Group column '{group_col}' not found in DataFrame.")
            stats_df = df.groupby(group_col)[metric_name].agg(['mean', 'std', 'count', 'min', 'max']).reset_index()
            stats_df.columns = [group_col, 'mean', 'std', 'count', 'min', 'max']
        else:
            stats_df = df[metric_name].agg(['mean', 'std', 'count', 'min', 'max']).to_frame().T
            stats_df.columns = ['mean', 'std', 'count', 'min', 'max']

        return stats_df

    @staticmethod
    def generate_descriptive_stats_report(raw_data_dir: str, output_path: str) -> bool:
        """
        Generates a descriptive statistics report for 'explanation_engagement_time'.
        This metric is descriptive only (no inferential testing).
        
        Reads raw session JSON files from raw_data_dir, aggregates the data,
        and calculates mean/std per interface type.
        
        Args:
            raw_data_dir: Path to the directory containing session JSON files.
            output_path: Path to save the resulting CSV file.
            
        Returns:
            True if successful, False otherwise.
        """
        logger.info(f"Generating descriptive stats report from {raw_data_dir} to {output_path}")
        
        try:
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            # Load all raw session files
            session_files = list(Path(raw_data_dir).glob("session_*.json"))
            if not session_files:
                logger.warning(f"No session files found in {raw_data_dir}")
                # Create empty report
                df_empty = pd.DataFrame(columns=['interface_type', 'metric_name', 'mean', 'std', 'count', 'min', 'max'])
                df_empty.to_csv(output_path, index=False)
                return True

            data_records = []
            
            for file_path in session_files:
                try:
                    with open(file_path, 'r') as f:
                        session_data = json.load(f)
                    
                    # Extract metrics
                    # Structure assumed based on T019: raw_data_logger
                    # Expected keys: 'participant_id', 'interface_type', 'metrics'
                    # metrics: {'completion_time': ..., 'error_count': ..., 'explanation_engagement_time': ...}
                    
                    if 'metrics' in session_data and 'explanation_engagement_time' in session_data['metrics']:
                        record = {
                            'participant_id': session_data.get('participant_id'),
                            'session_id': session_data.get('session_id'),
                            'interface_type': session_data.get('interface_type'),
                            'explanation_engagement_time': session_data['metrics']['explanation_engagement_time']
                        }
                        data_records.append(record)
                except Exception as e:
                    logger.warning(f"Could not parse {file_path}: {e}")
                    continue

            if not data_records:
                logger.warning("No valid records with 'explanation_engagement_time' found.")
                df_empty = pd.DataFrame(columns=['interface_type', 'metric_name', 'mean', 'std', 'count', 'min', 'max'])
                df_empty.to_csv(output_path, index=False)
                return True

            df = pd.DataFrame(data_records)
            
            # Calculate descriptive stats grouped by interface_type
            # Per task: mean, std for explanation_engagement_time
            stats_df = df.groupby('interface_type')['explanation_engagement_time'].agg(['mean', 'std', 'count', 'min', 'max']).reset_index()
            stats_df.columns = ['interface_type', 'metric_name', 'mean', 'std', 'count', 'min', 'max']
            stats_df['metric_name'] = 'explanation_engagement_time' # Explicitly name the metric

            # Reorder columns for clarity
            cols = ['interface_type', 'metric_name', 'mean', 'std', 'count', 'min', 'max']
            stats_df = stats_df[cols]

            stats_df.to_csv(output_path, index=False)
            logger.info(f"Descriptive stats report saved to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error generating descriptive stats report: {e}")
            return False

def main():
    """
    Entry point for running the statistical utilities directly.
    Primarily used for testing or standalone execution of specific analyses.
    """
    import sys
    from config.settings import get_settings
    
    settings = get_settings()
    raw_data_dir = settings.get('raw_data_dir', 'data/raw')
    output_path = settings.get('descriptive_stats_output', 'data/processed/descriptive_stats.csv')
    
    success = StatUtils.generate_descriptive_stats_report(raw_data_dir, output_path)
    if success:
        print(f"Descriptive stats report generated successfully at {output_path}")
        return 0
    else:
        print("Failed to generate descriptive stats report.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
