"""
Security hardening module for llmXive pipeline.

This module provides functions to ensure no PII (Personally Identifiable Information)
leaks in logs or output files. It implements sanitization strategies for common
PII patterns and enforces safe logging practices.
"""
import re
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np

from config import get_project_root, get_config_dict
from utils import get_logger

# PII Patterns for detection
PII_PATTERNS = {
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'phone': r'\b(?:\+?(\d{1,3}))?[-.\s]?(\(?\d{3}\)?)[-.\s]?\d{3}[-.\s]?\d{4}\b',
    'ssn': r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b',
    'credit_card': r'\b(?:\d[ -]*?){13,16}\b',
    'ip_address': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
    'user_id_numeric': r'\buser_id\s*[:=]\s*\d+\b',  # Specific to our data context
}

# Sensitive column names that might contain PII
SENSITIVE_COLUMNS = [
    'user_email', 'user_phone', 'ssn', 'credit_card', 'ip_address',
    'full_name', 'address', 'birth_date', 'personal_notes'
]

def sanitize_string(value: str, mask_char: str = '*') -> str:
    """
    Sanitize a string by masking detected PII patterns.
    
    Args:
        value: The string to sanitize
        mask_char: Character to use for masking (default: '*')
        
    Returns:
        Sanitized string with PII masked
    """
    if not isinstance(value, str) or pd.isna(value):
        return str(value) if not pd.isna(value) else value
    
    result = value
    for pattern_name, pattern in PII_PATTERNS.items():
        matches = re.findall(pattern, result, re.IGNORECASE)
        for match in matches:
            # Mask the match with asterisks, preserving length
            masked = mask_char * len(match)
            result = result.replace(match, masked)
    
    return result

def sanitize_dataframe(df: pd.DataFrame, 
                     columns_to_check: Optional[List[str]] = None,
                     mask_char: str = '*') -> pd.DataFrame:
    """
    Sanitize a DataFrame by masking PII in specified columns.
    
    Args:
        df: Input DataFrame
        columns_to_check: List of columns to check. If None, checks all string columns
        mask_char: Character to use for masking
        
    Returns:
        Sanitized DataFrame (copy)
    """
    df_sanitized = df.copy()
    
    if columns_to_check is None:
        # Check all object/string columns
        columns_to_check = df_sanitized.select_dtypes(include=['object', 'string']).columns.tolist()
    
    for col in columns_to_check:
        if col in df_sanitized.columns:
            # Check if column name suggests PII
            if col.lower() in [c.lower() for c in SENSITIVE_COLUMNS]:
                df_sanitized[col] = df_sanitized[col].apply(
                    lambda x: sanitize_string(str(x), mask_char) if pd.notna(x) else x
                )
            else:
                # Check content for PII patterns
                df_sanitized[col] = df_sanitized[col].apply(
                    lambda x: sanitize_string(str(x), mask_char) if pd.notna(x) else x
                )
    
    return df_sanitized

def sanitize_log_message(msg: str, mask_char: str = '*') -> str:
    """
    Sanitize a log message to prevent PII leakage in logs.
    
    Args:
        msg: The log message to sanitize
        mask_char: Character to use for masking
        
    Returns:
        Sanitized log message
    """
    return sanitize_string(str(msg), mask_char)

def safe_log(logger: logging.Logger, level: int, msg: str, *args, **kwargs):
    """
    Log a message safely after sanitizing for PII.
    
    Args:
        logger: The logger instance
        level: Logging level
        msg: Message to log
        *args: Additional arguments for formatting
        **kwargs: Additional keyword arguments
    """
    sanitized_msg = sanitize_log_message(msg)
    if args:
        # Sanitize arguments if they are strings
        sanitized_args = tuple(
            sanitize_log_message(str(arg)) if isinstance(arg, str) else arg 
            for arg in args
        )
        logger.log(level, sanitized_msg, *sanitized_args, **kwargs)
    else:
        logger.log(level, sanitized_msg, **kwargs)

def audit_output_file(file_path: str, 
                     sensitive_columns: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Audit an output file for potential PII leaks.
    
    Args:
        file_path: Path to the output file
        sensitive_columns: List of known sensitive column names
        
    Returns:
        Dictionary with audit results
    """
    results = {
        'file_path': file_path,
        'has_pii': False,
        'pii_locations': [],
        'warnings': []
    }
    
    path = Path(file_path)
    if not path.exists():
        results['warnings'].append(f"File not found: {file_path}")
        return results
    
    try:
        if path.suffix == '.parquet':
            df = pd.read_parquet(path)
        elif path.suffix == '.csv':
            df = pd.read_csv(path)
        elif path.suffix in ['.json', '.jsonl']:
            df = pd.read_json(path)
        else:
            # Skip non-data files
            return results
        
        # Check for sensitive column names
        for col in df.columns:
            if col.lower() in [c.lower() for c in SENSITIVE_COLUMNS]:
                results['pii_locations'].append(f"Column: {col}")
                results['has_pii'] = True
        
        # Check content in string columns
        string_cols = df.select_dtypes(include=['object', 'string']).columns
        for col in string_cols:
            for idx, val in df[col].dropna().items():
                for pattern_name, pattern in PII_PATTERNS.items():
                    if re.search(pattern, str(val), re.IGNORECASE):
                        results['pii_locations'].append(
                            f"File: {file_path}, Column: {col}, Row: {idx}, Pattern: {pattern_name}"
                        )
                        results['has_pii'] = True
                        break
        
    except Exception as e:
        results['warnings'].append(f"Error reading file: {str(e)}")
    
    return results

def ensure_no_pii_in_output(output_path: str, 
                           critical: bool = True) -> bool:
    """
    Ensure an output file does not contain PII.
    
    Args:
        output_path: Path to the output file
        critical: If True, raise error on PII detection; if False, just warn
        
    Returns:
        True if no PII detected, False otherwise
    """
    audit_results = audit_output_file(output_path)
    
    if audit_results['has_pii']:
        message = f"PII detected in output file: {output_path}\nDetails: {audit_results['pii_locations']}"
        if critical:
            raise ValueError(message)
        else:
            logger = get_logger(__name__)
            logger.warning(message)
            return False
    
    return True

def sanitize_pipeline_outputs():
    """
    Sanitize all final output files in the project.
    
    This function scans the data/final directory and sanitizes any CSV/Parquet files.
    """
    logger = get_logger(__name__)
    project_root = get_project_root()
    final_dir = project_root / "data" / "final"
    
    if not final_dir.exists():
        logger.warning(f"Final data directory not found: {final_dir}")
        return
    
    sanitized_count = 0
    for file_path in final_dir.glob("*"):
        if file_path.suffix in ['.csv', '.parquet', '.json']:
            try:
                if file_path.suffix == '.parquet':
                    df = pd.read_parquet(file_path)
                elif file_path.suffix == '.csv':
                    df = pd.read_csv(file_path)
                elif file_path.suffix == '.json':
                    df = pd.read_json(file_path)
                
                # Sanitize the dataframe
                df_clean = sanitize_dataframe(df)
                
                # Save back
                if file_path.suffix == '.parquet':
                    df_clean.to_parquet(file_path, index=False)
                elif file_path.suffix == '.csv':
                    df_clean.to_csv(file_path, index=False)
                elif file_path.suffix == '.json':
                    df_clean.to_json(file_path, orient='records', lines=True)
                
                sanitized_count += 1
                logger.info(f"Sanitized: {file_path}")
                
            except Exception as e:
                logger.error(f"Error sanitizing {file_path}: {str(e)}")
    
    logger.info(f"Sanitized {sanitized_count} output files in {final_dir}")

def main():
    """Main entry point for security hardening tasks."""
    logger = get_logger(__name__)
    logger.info("Starting security hardening checks...")
    
    # Sanitize all final outputs
    sanitize_pipeline_outputs()
    
    # Audit specific critical files
    project_root = get_project_root()
    critical_files = [
        project_root / "data" / "final" / "regression_summary.csv",
        project_root / "data" / "final" / "sensitivity_analysis.csv",
        project_root / "data" / "final" / "permutation_results.csv",
        project_root / "data" / "processed" / "user_track_pairs.parquet"
    ]
    
    for file_path in critical_files:
        if file_path.exists():
            try:
                ensure_no_pii_in_output(str(file_path), critical=True)
                logger.info(f"PII check passed: {file_path}")
            except ValueError as e:
                logger.error(f"PII check failed for {file_path}: {str(e)}")
        else:
            logger.warning(f"Critical file not found: {file_path}")
    
    logger.info("Security hardening checks completed.")

if __name__ == "__main__":
    main()
