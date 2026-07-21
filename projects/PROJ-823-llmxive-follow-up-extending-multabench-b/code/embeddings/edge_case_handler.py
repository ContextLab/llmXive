"""
Edge Case Handler for MulTaBench Embedding Pipeline.

This module provides utilities to detect and handle edge cases in tabular data
before embedding generation, specifically:
- Zero variance features (constant columns)
- Missing fields (null/NaN in required image/text columns)
- Single-row datasets
- Empty datasets

Strategies:
- Zero variance: Skip column or impute with constant mean
- Missing fields: Skip sample or impute with placeholder
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from utils.logging import get_logger, log_info, log_warning, log_error, log_debug

logger = get_logger(__name__)

class EdgeCaseHandler:
    """
    Handles edge cases in tabular data for embedding generation.
    
    Attributes:
        skip_zero_variance (bool): If True, drop zero-variance columns.
                                   If False, impute with mean.
        missing_strategy (str): 'skip' or 'impute' for missing fields.
        impute_value (float): Value to use for imputation.
    """
    
    def __init__(
        self,
        skip_zero_variance: bool = True,
        missing_strategy: str = 'skip',
        impute_value: float = 0.0
    ):
        self.skip_zero_variance = skip_zero_variance
        self.missing_strategy = missing_strategy
        self.impute_value = impute_value
    
    def detect_zero_variance(self, df: pd.DataFrame, numeric_cols: Optional[List[str]] = None) -> List[str]:
        """
        Detect columns with zero variance (constant values).
        
        Args:
            df: Input DataFrame
            numeric_cols: Optional list of numeric column names to check.
                         If None, checks all numeric columns.
        
        Returns:
            List of column names with zero variance.
        """
        if df.empty:
            log_warning("Empty DataFrame passed to detect_zero_variance")
            return []
        
        if numeric_cols is None:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        zero_var_cols = []
        for col in numeric_cols:
            if col not in df.columns:
                continue
            
            # Check variance (handles NaN by dropping them for variance calc)
            col_data = df[col].dropna()
            if len(col_data) == 0:
                # All NaN - treat as zero variance
                zero_var_cols.append(col)
            else:
                variance = col_data.var(ddof=0)  # Population variance
                if variance == 0.0:
                    zero_var_cols.append(col)
        
        if zero_var_cols:
            log_info(f"Detected {len(zero_var_cols)} zero-variance columns: {zero_var_cols}")
        
        return zero_var_cols
    
    def detect_missing_fields(
        self,
        df: pd.DataFrame,
        required_fields: List[str]
    ) -> Dict[str, int]:
        """
        Detect missing fields in required columns.
        
        Args:
            df: Input DataFrame
            required_fields: List of column names that must not be missing
        
        Returns:
            Dictionary mapping column name to count of missing values.
        """
        missing_counts = {}
        for field in required_fields:
            if field not in df.columns:
                log_error(f"Required field '{field}' not found in DataFrame")
                missing_counts[field] = len(df)
                continue
            
            count = df[field].isna().sum()
            if count > 0:
                missing_counts[field] = count
                log_warning(f"Found {count} missing values in required field '{field}'")
        
        return missing_counts
    
    def handle_zero_variance(
        self,
        df: pd.DataFrame,
        zero_var_cols: List[str]
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Handle zero-variance columns based on strategy.
        
        Args:
            df: Input DataFrame
            zero_var_cols: List of columns with zero variance
        
        Returns:
            Tuple of (processed DataFrame, metadata about handling)
        """
        metadata = {
            'zero_variance_columns': zero_var_cols,
            'action': None,
            'imputed_values': {}
        }
        
        if not zero_var_cols:
            return df, metadata
        
        if self.skip_zero_variance:
            log_info(f"Dropping {len(zero_var_cols)} zero-variance columns")
            df_processed = df.drop(columns=zero_var_cols)
            metadata['action'] = 'drop'
        else:
            log_info(f"Imputing {len(zero_var_cols)} zero-variance columns with mean")
            df_processed = df.copy()
            for col in zero_var_cols:
                if col not in df_processed.columns:
                    continue
                mean_val = df_processed[col].mean()
                if pd.isna(mean_val):
                    mean_val = self.impute_value
                df_processed[col] = mean_val
                metadata['imputed_values'][col] = mean_val
            metadata['action'] = 'impute'
        
        return df_processed, metadata
    
    def handle_missing_fields(
        self,
        df: pd.DataFrame,
        missing_counts: Dict[str, int],
        required_fields: List[str]
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Handle missing fields based on strategy.
        
        Args:
            df: Input DataFrame
            missing_counts: Dictionary of missing counts per field
            required_fields: List of required field names
        
        Returns:
            Tuple of (processed DataFrame, metadata about handling)
        """
        metadata = {
            'missing_fields': missing_counts,
            'action': None,
            'rows_dropped': 0
        }
        
        if not missing_counts:
            return df, metadata
        
        if self.missing_strategy == 'skip':
            # Drop rows with any missing required fields
            mask = pd.Series([True] * len(df), index=df.index)
            for field in required_fields:
                if field in df.columns:
                    mask = mask & df[field].notna()
            
            dropped_count = (~mask).sum()
            if dropped_count > 0:
                log_info(f"Dropping {dropped_count} rows with missing required fields")
                df_processed = df[mask].reset_index(drop=True)
            else:
                df_processed = df
            
            metadata['action'] = 'skip_rows'
            metadata['rows_dropped'] = dropped_count
        
        elif self.missing_strategy == 'impute':
            log_info(f"Imputing missing values in required fields with {self.impute_value}")
            df_processed = df.copy()
            for field in required_fields:
                if field in df_processed.columns:
                    df_processed[field] = df_processed[field].fillna(self.impute_value)
            metadata['action'] = 'impute'
        
        else:
            raise ValueError(f"Unknown missing_strategy: {self.missing_strategy}")
        
        return df_processed, metadata
    
    def process(
        self,
        df: pd.DataFrame,
        required_fields: List[str],
        numeric_cols: Optional[List[str]] = None
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Full pipeline to detect and handle all edge cases.
        
        Args:
            df: Input DataFrame
            required_fields: List of required column names
            numeric_cols: Optional list of numeric columns to check for zero variance
        
        Returns:
            Tuple of (processed DataFrame, comprehensive metadata)
        """
        metadata = {
            'original_shape': df.shape,
            'zero_variance': {},
            'missing_fields': {},
            'final_shape': None
        }
        
        if df.empty:
            log_warning("Empty DataFrame passed to EdgeCaseHandler")
            metadata['final_shape'] = (0, 0)
            return df, metadata
        
        # Step 1: Detect zero variance
        zero_var_cols = self.detect_zero_variance(df, numeric_cols)
        metadata['zero_variance']['detected'] = zero_var_cols
        
        # Step 2: Handle zero variance
        df, zvar_metadata = self.handle_zero_variance(df, zero_var_cols)
        metadata['zero_variance'].update(zvar_metadata)
        
        # Step 3: Detect missing fields
        missing_counts = self.detect_missing_fields(df, required_fields)
        metadata['missing_fields']['detected'] = missing_counts
        
        # Step 4: Handle missing fields
        df, miss_metadata = self.handle_missing_fields(df, missing_counts, required_fields)
        metadata['missing_fields'].update(miss_metadata)
        
        metadata['final_shape'] = df.shape
        
        log_info(f"Edge case processing complete: {metadata['original_shape']} -> {metadata['final_shape']}")
        
        return df, metadata
    
    def validate_dataset(self, df: pd.DataFrame, required_fields: List[str]) -> Tuple[bool, List[str]]:
        """
        Validate dataset has no critical edge cases that would cause failure.
        
        Args:
            df: Input DataFrame
            required_fields: List of required column names
        
        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []
        
        if df.empty:
            issues.append("Dataset is empty")
            return False, issues
        
        # Check for required fields
        for field in required_fields:
            if field not in df.columns:
                issues.append(f"Missing required column: {field}")
        
        # Check for all-NaN columns
        for col in df.columns:
            if df[col].isna().all():
                issues.append(f"All-NaN column: {col}")
        
        return len(issues) == 0, issues

def detect_zero_variance_columns(
    df: pd.DataFrame,
    numeric_cols: Optional[List[str]] = None
) -> List[str]:
    """Convenience function to detect zero variance columns."""
    handler = EdgeCaseHandler()
    return handler.detect_zero_variance(df, numeric_cols)

def detect_missing_fields(
    df: pd.DataFrame,
    required_fields: List[str]
) -> Dict[str, int]:
    """Convenience function to detect missing fields."""
    handler = EdgeCaseHandler()
    return handler.detect_missing_fields(df, required_fields)

def handle_zero_variance_columns(
    df: pd.DataFrame,
    zero_var_cols: List[str],
    skip: bool = True
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Convenience function to handle zero variance columns."""
    handler = EdgeCaseHandler(skip_zero_variance=skip)
    return handler.handle_zero_variance(df, zero_var_cols)

def handle_missing_fields(
    df: pd.DataFrame,
    missing_counts: Dict[str, int],
    required_fields: List[str],
    strategy: str = 'skip'
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Convenience function to handle missing fields."""
    handler = EdgeCaseHandler(missing_strategy=strategy)
    return handler.handle_missing_fields(df, missing_counts, required_fields)

def preprocess_dataset_for_edge_cases(
    df: pd.DataFrame,
    required_fields: List[str],
    numeric_cols: Optional[List[str]] = None,
    skip_zero_variance: bool = True,
    missing_strategy: str = 'skip'
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Full preprocessing pipeline for edge cases.
    
    Args:
        df: Input DataFrame
        required_fields: List of required column names
        numeric_cols: Optional list of numeric columns to check
        skip_zero_variance: If True, drop zero-variance columns
        missing_strategy: 'skip' or 'impute' for missing values
    
    Returns:
        Tuple of (processed DataFrame, metadata)
    """
    handler = EdgeCaseHandler(
        skip_zero_variance=skip_zero_variance,
        missing_strategy=missing_strategy
    )
    return handler.process(df, required_fields, numeric_cols)
