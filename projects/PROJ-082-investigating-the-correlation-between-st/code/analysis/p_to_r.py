"""
p-value to r conversion module for meta-analysis.
Implements Fisher's Z conversion logic for converting p-values and t-statistics to correlation coefficients.
"""
import csv
import json
import logging
import math
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from scipy import stats

# Import shared utilities from existing API surface
from utils.config import get_project_root, ensure_directory
from utils.logger import get_logger

class DataConversionError(Exception):
    """Raised when data conversion is ambiguous or impossible."""
    pass

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def p_to_t(p_value: float, df: int, two_tailed: bool = True) -> float:
    """
    Convert a p-value to a t-statistic.
    
    Args:
        p_value: The p-value (0 < p < 1)
        df: Degrees of freedom
        two_tailed: If True, treat as two-tailed test; if False, one-tailed
        
    Returns:
        The corresponding t-statistic
        
    Raises:
        DataConversionError: If p-value is out of valid range or ambiguous
    """
    if not (0 < p_value < 1):
        raise DataConversionError(f"Invalid p-value: {p_value}. Must be 0 < p < 1")
        
    if two_tailed:
        # For two-tailed, the p-value is split between both tails
        # We need the t-value such that P(|T| > |t|) = p_value
        # So P(T > |t|) = p_value / 2
        tail_prob = p_value / 2.0
    else:
        # For one-tailed, P(T > t) = p_value
        tail_prob = p_value
        
    # Use ppf (percent point function) to get t from probability
    # ppf(1 - tail_prob) gives the t-value for the upper tail
    t_stat = stats.t.ppf(1 - tail_prob, df)
    
    return t_stat

def t_to_r(t_stat: float, df: int) -> float:
    """
    Convert a t-statistic to a correlation coefficient r.
    
    Formula: r = sqrt(t^2 / (t^2 + df))
    Sign is preserved based on t_stat.
    
    Args:
        t_stat: The t-statistic
        df: Degrees of freedom
        
    Returns:
        The correlation coefficient r (-1 <= r <= 1)
    """
    if df <= 0:
        raise DataConversionError(f"Invalid degrees of freedom: {df}. Must be > 0")
        
    t_squared = t_stat ** 2
    r_squared = t_squared / (t_squared + df)
    
    # Ensure we don't get r > 1 due to floating point errors
    r_squared = min(1.0, max(0.0, r_squared))
    r = math.sqrt(r_squared)
    
    # Preserve sign
    if t_stat < 0:
        r = -r
        
    return r

def convert_p_to_r(p_value: float, df: int, two_tailed: bool = True) -> float:
    """
    Convert a p-value to a correlation coefficient r.
    
    Args:
        p_value: The p-value
        df: Degrees of freedom
        two_tailed: Whether the p-value is from a two-tailed test
        
    Returns:
        The correlation coefficient r
    """
    t_stat = p_to_t(p_value, df, two_tailed)
    r = t_to_r(t_stat, df)
    return r

def convert_t_to_r(t_stat: float, df: int) -> float:
    """
    Convert a t-statistic to a correlation coefficient r.
    
    Args:
        t_stat: The t-statistic
        df: Degrees of freedom
        
    Returns:
        The correlation coefficient r
    """
    return t_to_r(t_stat, df)

def process_row(row: Dict[str, Any], logger: logging.Logger) -> Tuple[Optional[float], str]:
    """
    Process a single row to extract r value from p-value or t-statistic if r is missing.
    
    Args:
        row: A dictionary representing a study record
        logger: Logger instance
        
    Returns:
        Tuple of (r_value, conversion_method)
        If r is already present, returns (r, "original")
        If conversion successful, returns (r, "p_to_r" or "t_to_r")
        If conversion fails, returns (None, "failed")
    """
    # Check if r is already present and valid
    r_val = row.get('r')
    if r_val is not None and r_val != '' and r_val != 'NA' and r_val != 'NaN':
        try:
            r_float = float(r_val)
            if -1.0 <= r_float <= 1.0:
                return r_float, "original"
        except (ValueError, TypeError):
            pass
    
    # Try to convert from t-statistic
    t_val = row.get('t')
    if t_val is not None and t_val != '' and t_val != 'NA' and t_val != 'NaN':
        df_val = row.get('df')
        if df_val is not None and df_val != '' and df_val != 'NA' and df_val != 'NaN':
            try:
                t_float = float(t_val)
                df_float = int(float(df_val))
                if df_float > 0:
                    r = convert_t_to_r(t_float, df_float)
                    logger.info(f"Converted t={t_float}, df={df_float} to r={r:.4f}")
                    return r, "t_to_r"
            except (ValueError, TypeError, DataConversionError) as e:
                logger.warning(f"Failed t-to-r conversion: {e}")
    
    # Try to convert from p-value
    p_val = row.get('p')
    if p_val is not None and p_val != '' and p_val != 'NA' and p_val != 'NaN':
        df_val = row.get('df')
        two_tailed_str = row.get('two_tailed', 'True')
        
        if df_val is not None and df_val != '' and df_val != 'NA' and df_val != 'NaN':
            try:
                p_float = float(p_val)
                df_float = int(float(df_val))
                two_tailed = two_tailed_str.lower() in ['true', '1', 'yes', 't']
                
                if 0 < p_float < 1 and df_float > 0:
                    r = convert_p_to_r(p_float, df_float, two_tailed)
                    logger.info(f"Converted p={p_float}, df={df_float}, two_tailed={two_tailed} to r={r:.4f}")
                    return r, "p_to_r"
            except (ValueError, TypeError, DataConversionError) as e:
                logger.warning(f"Failed p-to-r conversion: {e}")
    
    # No valid conversion possible
    return None, "failed"

def run_p_to_r_conversion(input_path: str, output_path: str) -> Dict[str, int]:
    """
    Read studies CSV, convert p-values/t-stats to r where missing, and write updated CSV.
    
    Args:
        input_path: Path to input CSV
        output_path: Path to output CSV
        
    Returns:
        Dictionary with conversion statistics
    """
    project_root = get_project_root()
    logger = get_logger("p_to_r")
    
    input_file = project_root / input_path
    output_file = project_root / output_path
    
    ensure_directory(output_file.parent)
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    stats_dict = {
        'total_rows': 0,
        'original_r': 0,
        'converted_t': 0,
        'converted_p': 0,
        'failed': 0
    }
    
    rows = []
    
    with open(input_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        
        # Add new columns if not present
        if 'r' not in fieldnames:
            fieldnames = list(fieldnames) + ['r']
        if 'conversion_method' not in fieldnames:
            fieldnames = list(fieldnames) + ['conversion_method']
        
        for row in reader:
            stats_dict['total_rows'] += 1
            
            r_val, method = process_row(row, logger)
            
            row['conversion_method'] = method
            if r_val is not None:
                row['r'] = f"{r_val:.6f}"
            else:
                row['r'] = ''
            
            if method == 'original':
                stats_dict['original_r'] += 1
            elif method == 't_to_r':
                stats_dict['converted_t'] += 1
            elif method == 'p_to_r':
                stats_dict['converted_p'] += 1
            else:
                stats_dict['failed'] += 1
            
            rows.append(row)
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    logger.info(f"Conversion complete. Written to {output_file}")
    logger.info(f"Stats: {stats_dict}")
    
    return stats_dict

def main():
    """Main entry point for the p-to-r conversion script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert p-values and t-statistics to correlation coefficients')
    parser.add_argument('--input', type=str, default='data/processed/extracted_studies.csv',
                      help='Input CSV file path')
    parser.add_argument('--output', type=str, default='data/processed/extracted_studies.csv',
                      help='Output CSV file path')
    args = parser.parse_args()
    
    try:
        stats = run_p_to_r_conversion(args.input, args.output)
        print(f"Conversion completed successfully.")
        print(f"Total rows: {stats['total_rows']}")
        print(f"Original r: {stats['original_r']}")
        print(f"Converted from t: {stats['converted_t']}")
        print(f"Converted from p: {stats['converted_p']}")
        print(f"Failed conversions: {stats['failed']}")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Conversion failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()