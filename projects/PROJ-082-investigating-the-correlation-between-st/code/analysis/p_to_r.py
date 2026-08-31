"""
Task T040: p-value to r Conversion using Fisher's Z transformation.

Implements conversion of t-statistics and p-values to correlation coefficients (r).
For p-values, converts to t-statistic first (handling one/two-tailed), then to r.
Raises DataConversionError for ambiguous or invalid inputs.
"""
import csv
import json
import logging
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from scipy.stats import t

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataConversionError(Exception):
    """Custom exception for data conversion errors."""
    pass

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def p_to_t(p_value: float, df: int, two_tailed: bool = True) -> float:
    """
    Convert a p-value to a t-statistic.

    Args:
        p_value: The p-value (0 < p < 1)
        df: Degrees of freedom
        two_tailed: If True, p is for a two-tailed test; if False, one-tailed.

    Returns:
        The corresponding t-statistic.

    Raises:
        DataConversionError: If p_value is out of valid range or df is invalid.
    """
    if not (0 < p_value < 1):
        raise DataConversionError(f"Invalid p-value: {p_value}. Must be in (0, 1).")
    if df <= 0:
        raise DataConversionError(f"Invalid degrees of freedom: {df}. Must be > 0.")

    if two_tailed:
        # For two-tailed, the cumulative probability for the upper tail is 1 - p/2
        # t.ppf expects cumulative probability from the left
        prob = 1 - (p_value / 2)
    else:
        # For one-tailed, we assume the p-value corresponds to the upper tail
        # If the effect is negative, the caller should handle the sign
        prob = 1 - p_value

    try:
        t_stat = t.ppf(prob, df)
    except Exception as e:
        raise DataConversionError(f"Failed to compute t-statistic from p={p_value}, df={df}: {e}")

    return t_stat

def t_to_r(t_stat: float, df: int) -> float:
    """
    Convert a t-statistic to a correlation coefficient (r).

    Formula: r = sqrt(t^2 / (t^2 + df))
    The sign of r is the same as the sign of t.

    Args:
        t_stat: The t-statistic.
        df: Degrees of freedom.

    Returns:
        The correlation coefficient r.

    Raises:
        DataConversionError: If df is invalid.
    """
    if df <= 0:
        raise DataConversionError(f"Invalid degrees of freedom: {df}. Must be > 0.")

    t_squared = t_stat ** 2
    denominator = t_squared + df

    if denominator == 0:
        raise DataConversionError("Division by zero in t-to-r conversion.")

    r = math.sqrt(t_squared / denominator)

    # Preserve the sign of the t-statistic
    if t_stat < 0:
        r = -r

    return r

def convert_p_to_r(p_value: float, df: int, two_tailed: bool = True) -> float:
    """
    Convert a p-value to a correlation coefficient (r).

    Steps:
    1. Convert p-value to t-statistic.
    2. Convert t-statistic to r.

    Args:
        p_value: The p-value.
        df: Degrees of freedom.
        two_tailed: Whether the p-value is from a two-tailed test.

    Returns:
        The correlation coefficient r.
    """
    t_stat = p_to_t(p_value, df, two_tailed)
    return t_to_r(t_stat, df)

def convert_t_to_r(t_stat: float, df: int) -> float:
    """
    Convert a t-statistic to a correlation coefficient (r).

    Args:
        t_stat: The t-statistic.
        df: Degrees of freedom.

    Returns:
        The correlation coefficient r.
    """
    return t_to_r(t_stat, df)

def process_row(row: Dict[str, str]) -> Tuple[Optional[float], str]:
    """
    Process a single study row to extract r if possible.

    Priority:
    1. If 'r' is already present and valid, return it with method 'existing'.
    2. If 't' and 'df' are present, convert t to r.
    3. If 'p' and 'df' are present, convert p to t then to r.
    4. If 'n' is present, calculate df = n - 2 (for correlation).

    Returns:
        Tuple of (r_value, conversion_method).
        If conversion fails or impossible, returns (None, 'error' or 'missing').
    """
    # Check if r is already present
    if 'r' in row and row['r'] and row['r'].strip():
        try:
            r_val = float(row['r'])
            if -1 <= r_val <= 1:
                return r_val, 'existing'
            else:
                logger.warning(f"Invalid r value {r_val} in row: {row.get('author', 'unknown')}")
                return None, 'invalid_existing'
        except ValueError:
            logger.warning(f"Could not parse r value: {row['r']}")
            return None, 'parse_error'

    # Determine df
    df = None
    if 'df' in row and row['df'] and row['df'].strip():
        try:
            df = int(float(row['df']))
        except ValueError:
            logger.warning(f"Could not parse df value: {row['df']}")
            return None, 'parse_error'
    elif 'n' in row and row['n'] and row['n'].strip():
        try:
            n = int(float(row['n']))
            # For Pearson correlation, df = n - 2
            df = n - 2
        except ValueError:
            logger.warning(f"Could not parse n value: {row['n']}")
            return None, 'parse_error'

    if df is None or df <= 0:
        # Cannot proceed without df
        return None, 'missing_df'

    # Try t-statistic first
    if 't' in row and row['t'] and row['t'].strip():
        try:
            t_val = float(row['t'])
            r_val = convert_t_to_r(t_val, df)
            return r_val, 'from_t'
        except ValueError:
            logger.warning(f"Could not parse t value: {row['t']}")
            return None, 'parse_error'
        except DataConversionError as e:
            logger.warning(f"t-to-r conversion failed: {e}")
            return None, 'conversion_error'

    # Try p-value
    if 'p' in row and row['p'] and row['p'].strip():
        try:
            p_val = float(row['p'])
            # Assume two-tailed by default unless specified
            two_tailed = True
            if 'two_tailed' in row:
                two_tailed = row['two_tailed'].lower() in ['true', '1', 'yes', 't']

            r_val = convert_p_to_r(p_val, df, two_tailed)
            return r_val, 'from_p'
        except ValueError:
            logger.warning(f"Could not parse p value: {row['p']}")
            return None, 'parse_error'
        except DataConversionError as e:
            logger.warning(f"p-to-r conversion failed: {e}")
            return None, 'conversion_error'

    return None, 'missing_stats'

def run_p_to_r_conversion(
    input_path: Path,
    output_path: Path,
    log_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Main function to run p-value to r conversion on a CSV file.

    Args:
        input_path: Path to input CSV file.
        output_path: Path to output CSV file.
        log_path: Optional path to log file.

    Returns:
        Dictionary with conversion statistics.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    stats = {
        'total_rows': 0,
        'converted_from_t': 0,
        'converted_from_p': 0,
        'existing_r': 0,
        'errors': 0,
        'missing_stats': 0,
        'missing_df': 0,
        'parse_errors': 0
    }

    rows_out = []
    headers = []
    log_entries = []

    try:
        with open(input_path, 'r', newline='', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            headers = reader.fieldnames or []

            # Ensure output headers include r and conversion_method
            if 'r' not in headers:
                headers.append('r')
            if 'conversion_method' not in headers:
                headers.append('conversion_method')

            for row in reader:
                stats['total_rows'] += 1
                r_val, method = process_row(row)

                # Update row
                if r_val is not None:
                    row['r'] = f"{r_val:.6f}"
                    row['conversion_method'] = method
                    if method == 'from_t':
                        stats['converted_from_t'] += 1
                    elif method == 'from_p':
                        stats['converted_from_p'] += 1
                    elif method == 'existing':
                        stats['existing_r'] += 1
                else:
                    row['r'] = ''
                    row['conversion_method'] = method
                    if method == 'missing_stats':
                        stats['missing_stats'] += 1
                    elif method == 'missing_df':
                        stats['missing_df'] += 1
                    elif method == 'parse_error':
                        stats['parse_errors'] += 1
                    else:
                        stats['errors'] += 1

                    log_entries.append({
                        'row_idx': stats['total_rows'],
                        'author': row.get('author', 'unknown'),
                        'year': row.get('year', 'unknown'),
                        'method': method,
                        'reason': f"Could not convert: {row}"
                    })

                rows_out.append(row)

    except Exception as e:
        logger.error(f"Error reading input file: {e}")
        raise

    # Write output
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows_out)
        logger.info(f"Successfully wrote {len(rows_out)} rows to {output_path}")
    except Exception as e:
        logger.error(f"Error writing output file: {e}")
        raise

    # Write log if requested
    if log_path and log_entries:
        try:
            with open(log_path, 'w', newline='', encoding='utf-8') as log_file:
                if log_entries:
                    writer = csv.DictWriter(log_file, fieldnames=log_entries[0].keys())
                    writer.writeheader()
                    writer.writerows(log_entries)
            logger.info(f"Logged {len(log_entries)} conversion failures to {log_path}")
        except Exception as e:
            logger.error(f"Error writing log file: {e}")

    return stats

def main():
    """CLI entry point for p-to-r conversion."""
    import argparse

    parser = argparse.ArgumentParser(description='Convert p-values and t-statistics to correlation coefficients (r).')
    parser.add_argument('--input', type=str, required=True, help='Path to input CSV file.')
    parser.add_argument('--output', type=str, required=True, help='Path to output CSV file.')
    parser.add_argument('--log', type=str, default=None, help='Path to log file for conversion errors.')

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    log_path = Path(args.log) if args.log else None

    logger.info(f"Starting p-to-r conversion: {input_path} -> {output_path}")

    try:
        stats = run_p_to_r_conversion(input_path, output_path, log_path)
        logger.info(f"Conversion complete. Stats: {json.dumps(stats, indent=2)}")
        return 0
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
