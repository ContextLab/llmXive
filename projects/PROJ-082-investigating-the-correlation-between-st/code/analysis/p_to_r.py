"""
p-value to r Conversion Module.

Implements Fisher's Z conversion logic for converting p-values and t-statistics
to correlation coefficients (r).

Formulas:
- For t-statistic: r = sqrt(t^2 / (t^2 + df))
- For p-value: Convert p to t using scipy.stats.t.ppf (handling one-tailed vs two-tailed)
  then apply t-to-r formula.

Raises:
    DataConversionError: For ambiguous cases where conversion is not possible.
"""

import csv
import json
import logging
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats

from utils.config import get_project_root

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataConversionError(Exception):
    """Custom exception for data conversion failures."""
    pass


def get_project_root() -> Path:
    """Returns the project root directory."""
    return Path(__file__).resolve().parent.parent.parent


def p_to_t(p_value: float, df: int, two_tailed: bool = True) -> float:
    """
    Convert a p-value to a t-statistic.

    Args:
        p_value: The p-value (must be between 0 and 1).
        df: Degrees of freedom.
        two_tailed: Whether the p-value is from a two-tailed test.

    Returns:
        The corresponding t-statistic.

    Raises:
        DataConversionError: If p-value is out of bounds or conversion fails.
    """
    if not (0 < p_value < 1):
        raise DataConversionError(f"Invalid p-value: {p_value}. Must be 0 < p < 1.")

    try:
        if two_tailed:
            # For two-tailed, the area in one tail is p/2
            # We want the t-value such that P(|T| > t) = p
            # So P(T > t) = p/2
            # t = ppf(1 - p/2)
            t_val = stats.t.ppf(1 - p_value / 2, df)
        else:
            # For one-tailed, assuming we want the positive t if p is small
            # If the original test was one-tailed in the negative direction,
            # we might need to negate. However, standard conversion assumes
            # we are recovering the magnitude or assuming a positive effect
            # unless specified otherwise. We'll assume positive t for small p.
            t_val = stats.t.ppf(1 - p_value, df)

        return float(t_val)
    except Exception as e:
        raise DataConversionError(f"Failed to convert p={p_value} to t with df={df}: {e}")


def t_to_r(t_stat: float, df: int) -> float:
    """
    Convert a t-statistic to a correlation coefficient r.

    Formula: r = sqrt(t^2 / (t^2 + df))

    Args:
        t_stat: The t-statistic.
        df: Degrees of freedom.

    Returns:
        The correlation coefficient r.
    """
    if df <= 0:
        raise DataConversionError(f"Invalid degrees of freedom: {df}. Must be > 0.")

    t_sq = t_stat ** 2
    r_sq = t_sq / (t_sq + df)

    # Clamp to [0, 1] to handle floating point errors
    r_sq = max(0.0, min(1.0, r_sq))
    r = math.sqrt(r_sq)

    # Note: This formula recovers the magnitude of r.
    # The sign of r is ambiguous from t alone if we don't know the direction.
    # However, in meta-analysis of correlations, t usually preserves the sign
    # of the correlation if calculated as t = r * sqrt((n-2)/(1-r^2)).
    # Let's check the standard transformation:
    # t = r * sqrt(df / (1 - r^2))
    # t^2 = r^2 * df / (1 - r^2)
    # t^2 (1 - r^2) = r^2 * df
    # t^2 - t^2 r^2 = r^2 df
    # t^2 = r^2 (df + t^2)
    # r^2 = t^2 / (df + t^2)
    # This matches. The sign of r is the same as the sign of t.
    # So we should return t / sqrt(t^2 + df) to preserve sign.

    # Corrected formula preserving sign:
    # r = t / sqrt(t^2 + df)
    r_signed = t_stat / math.sqrt(t_stat ** 2 + df)
    return float(r_signed)


def convert_p_to_r(p_value: float, n: int, two_tailed: bool = True) -> Tuple[float, str]:
    """
    Convert a p-value to r, given sample size n.

    Args:
        p_value: The p-value.
        n: Sample size.
        two_tailed: Whether the p-value is two-tailed.

    Returns:
        Tuple of (r, method_description).

    Raises:
        DataConversionError: If conversion fails.
    """
    if n is None or n <= 2:
        raise DataConversionError(f"Invalid sample size: {n}. Must be > 2.")

    df = n - 2
    t_val = p_to_t(p_value, df, two_tailed)
    r_val = t_to_r(t_val, df)

    return r_val, f"p_to_t_to_r (p={p_value}, n={n}, two_tailed={two_tailed})"


def convert_t_to_r(t_stat: float, n: int) -> Tuple[float, str]:
    """
    Convert a t-statistic to r, given sample size n.

    Args:
        t_stat: The t-statistic.
        n: Sample size.

    Returns:
        Tuple of (r, method_description).

    Raises:
        DataConversionError: If conversion fails.
    """
    if n is None or n <= 2:
        raise DataConversionError(f"Invalid sample size: {n}. Must be > 2.")

    df = n - 2
    r_val = t_to_r(t_stat, df)
    return r_val, f"t_to_r (t={t_stat}, n={n})"


def process_row(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Process a single row from the extracted studies CSV.

    If 'r' is missing but 'p' or 't' is present, performs conversion.
    Updates the row with the new 'r' and 'conversion_method'.

    Args:
        row: Dictionary representing a study record.

    Returns:
        Updated row, or None if no conversion was needed/possible.
    """
    r_val = row.get('r')
    p_val = row.get('p')
    t_val = row.get('t')
    n_val = row.get('n')

    # If r is already present, no conversion needed
    if r_val is not None and r_val != '':
        try:
            float(r_val)
            return None # Already has valid r
        except (ValueError, TypeError):
            # r exists but is invalid, try to convert if possible
            pass

    # Try to convert from t if available
    if t_val is not None and t_val != '':
        try:
            t_float = float(t_val)
            if n_val is not None and n_val != '':
                n_int = int(float(n_val))
                r_converted, method = convert_t_to_r(t_float, n_int)
                row['r'] = r_converted
                row['conversion_method'] = method
                return row
            else:
                logger.warning(f"t present but n missing for study {row.get('author', 'unknown')}. Cannot convert.")
                row['conversion_method'] = 'skipped_missing_n'
                return row
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid t value '{t_val}' for study {row.get('author', 'unknown')}: {e}")

    # Try to convert from p if available
    if p_val is not None and p_val != '':
        try:
            p_float = float(p_val)
            if n_val is not None and n_val != '':
                n_int = int(float(n_val))
                # Assume two-tailed by default unless specified otherwise in data
                # If the data has a 'two_tailed' column, use it.
                two_tailed = row.get('two_tailed', True)
                if isinstance(two_tailed, str):
                    two_tailed = two_tailed.lower() in ('true', '1', 'yes')

                r_converted, method = convert_p_to_r(p_float, n_int, two_tailed)
                row['r'] = r_converted
                row['conversion_method'] = method
                return row
            else:
                logger.warning(f"p present but n missing for study {row.get('author', 'unknown')}. Cannot convert.")
                row['conversion_method'] = 'skipped_missing_n'
                return row
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid p value '{p_val}' for study {row.get('author', 'unknown')}: {e}")
        except DataConversionError as e:
            logger.warning(f"Conversion error for study {row.get('author', 'unknown')}: {e}")

    # If we reached here, we couldn't convert
    if r_val is None or r_val == '':
        row['conversion_method'] = 'no_source_data'
        return row

    return None


def run_p_to_r_conversion(input_path: Optional[Path] = None, output_path: Optional[Path] = None) -> None:
    """
    Main function to run p-value to r conversion on the extracted studies file.

    Reads from data/processed/extracted_studies.csv (or input_path),
    performs conversions, and writes to data/processed/extracted_studies.csv (or output_path).
    """
    if input_path is None:
        project_root = get_project_root()
        input_path = project_root / "data" / "processed" / "extracted_studies.csv"
    
    if output_path is None:
        project_root = get_project_root()
        output_path = project_root / "data" / "processed" / "extracted_studies.csv"

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Reading input from {input_path}")
    
    rows = []
    fieldnames = []
    conversions_count = 0
    skipped_count = 0

    try:
        with open(input_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            
            # Ensure output has the necessary columns
            if 'conversion_method' not in fieldnames:
                fieldnames.append('conversion_method')

            for row in reader:
                # Clean up empty strings to None for easier processing
                cleaned_row = {k: (v if v != '' else None) for k, v in row.items()}
                
                result = process_row(cleaned_row)
                if result:
                    # Convert back to string representation for CSV
                    output_row = {k: (str(v) if v is not None else '') for k, v in result.items()}
                    rows.append(output_row)
                    if 'conversion_method' in result and result['conversion_method'] and result['conversion_method'] != 'no_source_data':
                        conversions_count += 1
                    else:
                        skipped_count += 1
                else:
                    # No conversion needed, just copy original (ensure consistent formatting)
                    original_row = {k: (v if v is not None else '') for k, v in row.items()}
                    if 'conversion_method' not in original_row:
                        original_row['conversion_method'] = ''
                    rows.append(original_row)

        logger.info(f"Processed {len(rows)} rows. {conversions_count} conversions performed.")
        
        # Write output
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        logger.info(f"Output written to {output_path}")

    except Exception as e:
        logger.error(f"Error during conversion: {e}")
        raise


def main():
    """Entry point for script execution."""
    try:
        run_p_to_r_conversion()
        logger.info("p-to-r conversion completed successfully.")
    except Exception as e:
        logger.error(f"p-to-r conversion failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()