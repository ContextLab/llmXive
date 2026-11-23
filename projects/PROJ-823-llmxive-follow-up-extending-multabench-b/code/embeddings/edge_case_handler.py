import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from utils.logging import get_logger, log_info, log_warning, log_error, log_debug

logger = get_logger(__name__)

class EdgeCaseHandler:
    """
    Handles edge cases in datasets such as zero-variance columns and missing image/text fields.
    """

    def __init__(self, missing_strategy: str = "skip", zero_var_strategy: str = "impute_constant"):
        """
        Initialize the handler.

        Args:
            missing_strategy: How to handle missing fields ('skip', 'impute_constant', 'error')
            zero_var_strategy: How to handle zero-variance columns ('skip', 'impute_constant', 'error')
        """
        self.missing_strategy = missing_strategy
        self.zero_var_strategy = zero_var_strategy

    def detect_zero_variance_columns(self, df: pd.DataFrame, numeric_cols: Optional[List[str]] = None) -> List[str]:
        """
        Detect columns with zero variance (constant values).

        Args:
            df: Input DataFrame
            numeric_cols: Specific columns to check. If None, checks all numeric columns.

        Returns:
            List of column names with zero variance.
        """
        if numeric_cols is None:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        zero_var_cols = []
        for col in numeric_cols:
            if df[col].nunique() == 1:
                zero_var_cols.append(col)
                log_warning(f"Detected zero-variance column: {col}")

        return zero_var_cols

    def detect_missing_fields(self, df: pd.DataFrame, required_fields: List[str]) -> Dict[str, Any]:
        """
        Detect missing required fields (image/text paths or content).

        Args:
            df: Input DataFrame
            required_fields: List of field names that must be present and non-null.

        Returns:
            Dictionary with 'missing_fields' (list of fields missing entirely)
            and 'missing_values' (dict mapping field to count of missing values).
        """
        result = {
            'missing_fields': [],
            'missing_values': {}
        }

        for field in required_fields:
            if field not in df.columns:
                result['missing_fields'].append(field)
                log_error(f"Required field '{field}' is missing from dataset.")
            else:
                missing_count = df[field].isna().sum()
                if missing_count > 0:
                    result['missing_values'][field] = int(missing_count)
                    log_warning(f"Field '{field}' has {missing_count} missing values.")

        return result

    def handle_zero_variance_columns(
        self,
        df: pd.DataFrame,
        zero_var_cols: List[str],
        constant_value: float = 0.0
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Handle zero-variance columns based on configured strategy.

        Args:
            df: Input DataFrame
            zero_var_cols: List of zero-variance column names
            constant_value: Value to impute if strategy is 'impute_constant'

        Returns:
            Tuple of (processed DataFrame, metadata about handling)
        """
        metadata = {
            'action': self.zero_var_strategy,
            'columns_affected': zero_var_cols,
            'constant_value': constant_value
        }

        if self.zero_var_strategy == "skip":
            log_info(f"Dropping {len(zero_var_cols)} zero-variance columns: {zero_var_cols}")
            df_processed = df.drop(columns=zero_var_cols)
            metadata['dropped_columns'] = zero_var_cols

        elif self.zero_var_strategy == "impute_constant":
            log_info(f"Imputing {len(zero_var_cols)} zero-variance columns with constant {constant_value}")
            df_processed = df.copy()
            for col in zero_var_cols:
                df_processed[col] = constant_value
            metadata['imputed_columns'] = zero_var_cols

        elif self.zero_var_strategy == "error":
            raise ValueError(f"Zero-variance columns detected: {zero_var_cols}. "
                             f"Strategy is set to 'error'.")
        else:
            raise ValueError(f"Unknown zero_var_strategy: {self.zero_var_strategy}")

        return df_processed, metadata

    def handle_missing_fields(
        self,
        df: pd.DataFrame,
        missing_info: Dict[str, Any],
        image_fill: str = "",
        text_fill: str = ""
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Handle missing image/text fields based on configured strategy.

        Args:
            df: Input DataFrame
            missing_info: Output from detect_missing_fields()
            image_fill: Fill value for missing image paths (default empty string)
            text_fill: Fill value for missing text content (default empty string)

        Returns:
            Tuple of (processed DataFrame, metadata about handling)
        """
        metadata = {
            'action': self.missing_strategy,
            'missing_fields': missing_info['missing_fields'],
            'missing_value_counts': missing_info['missing_values']
        }

        if self.missing_strategy == "skip":
            # Identify rows with any missing required field
            rows_to_drop = set()
            for field, count in missing_info['missing_values'].items():
                if count > 0:
                    mask = df[field].isna()
                    rows_to_drop.update(df[mask].index.tolist())

            if rows_to_drop:
                log_warning(f"Dropping {len(rows_to_drop)} rows with missing required fields.")
                df_processed = df.drop(index=list(rows_to_drop))
                metadata['rows_dropped'] = len(rows_to_drop)
            else:
                df_processed = df.copy()
                metadata['rows_dropped'] = 0

        elif self.missing_strategy == "impute_constant":
            log_info("Imputing missing fields with constant values.")
            df_processed = df.copy()
            for field, count in missing_info['missing_values'].items():
                if field in df_processed.columns:
                    if 'image' in field.lower():
                        df_processed[field] = df_processed[field].fillna(image_fill)
                    else:
                        df_processed[field] = df_processed[field].fillna(text_fill)
            metadata['imputed_fields'] = list(missing_info['missing_values'].keys())

        elif self.missing_strategy == "error":
            if missing_info['missing_fields'] or missing_info['missing_values']:
                raise ValueError(
                    f"Missing required data detected. "
                    f"Missing fields: {missing_info['missing_fields']}, "
                    f"Missing value counts: {missing_info['missing_values']}. "
                    f"Strategy is set to 'error'."
                )
            df_processed = df.copy()
        else:
            raise ValueError(f"Unknown missing_strategy: {self.missing_strategy}")

        return df_processed, metadata

def detect_zero_variance_columns(df: pd.DataFrame, numeric_cols: Optional[List[str]] = None) -> List[str]:
    """Convenience function to detect zero-variance columns."""
    handler = EdgeCaseHandler()
    return handler.detect_zero_variance_columns(df, numeric_cols)

def detect_missing_fields(df: pd.DataFrame, required_fields: List[str]) -> Dict[str, Any]:
    """Convenience function to detect missing fields."""
    handler = EdgeCaseHandler()
    return handler.detect_missing_fields(df, required_fields)

def handle_zero_variance_columns(
    df: pd.DataFrame,
    zero_var_cols: List[str],
    strategy: str = "impute_constant",
    constant_value: float = 0.0
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Convenience function to handle zero-variance columns."""
    handler = EdgeCaseHandler(zero_var_strategy=strategy)
    return handler.handle_zero_variance_columns(df, zero_var_cols, constant_value)

def handle_missing_fields(
    df: pd.DataFrame,
    missing_info: Dict[str, Any],
    strategy: str = "impute_constant",
    image_fill: str = "",
    text_fill: str = ""
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Convenience function to handle missing fields."""
    handler = EdgeCaseHandler(missing_strategy=strategy)
    return handler.handle_missing_fields(df, missing_info, image_fill, text_fill)

def preprocess_dataset_for_edge_cases(
    df: pd.DataFrame,
    required_fields: List[str],
    zero_var_strategy: str = "impute_constant",
    missing_strategy: str = "impute_constant",
    numeric_cols: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Full preprocessing pipeline for edge cases.

    Args:
        df: Input DataFrame
        required_fields: List of required field names
        zero_var_strategy: Strategy for zero-variance columns
        missing_strategy: Strategy for missing fields
        numeric_cols: Specific numeric columns to check for variance

    Returns:
        Tuple of (processed DataFrame, aggregate metadata)
    """
    logger.info(f"Starting edge case preprocessing for dataset with {len(df)} rows.")

    # Step 1: Detect issues
    zero_var_cols = detect_zero_variance_columns(df, numeric_cols)
    missing_info = detect_missing_fields(df, required_fields)

    aggregate_metadata = {
        'zero_variance_columns': zero_var_cols,
        'missing_field_info': missing_info,
        'original_row_count': len(df),
        'original_column_count': len(df.columns)
    }

    # Step 2: Handle missing fields first (might drop rows)
    df_processed, missing_metadata = handle_missing_fields(
        df, missing_info, missing_strategy
    )
    aggregate_metadata['missing_handling'] = missing_metadata

    # Step 3: Handle zero-variance columns on the remaining data
    # Re-detect zero-variance on the processed data if rows were dropped
    current_zero_var_cols = detect_zero_variance_columns(df_processed, numeric_cols)
    df_processed, zero_var_metadata = handle_zero_variance_columns(
        df_processed, current_zero_var_cols, zero_var_strategy
    )
    aggregate_metadata['zero_variance_handling'] = zero_var_metadata

    aggregate_metadata['final_row_count'] = len(df_processed)
    aggregate_metadata['final_column_count'] = len(df_processed.columns)

    logger.info(f"Edge case preprocessing complete. "
                f"Rows: {aggregate_metadata['original_row_count']} -> {aggregate_metadata['final_row_count']}, "
                f"Columns: {aggregate_metadata['original_column_count']} -> {aggregate_metadata['final_column_count']}.")

    return df_processed, aggregate_metadata
