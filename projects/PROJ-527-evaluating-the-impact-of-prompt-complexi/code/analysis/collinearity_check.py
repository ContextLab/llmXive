"""
Collinearity diagnostic for FR-013.

Computes the Pearson correlation coefficient between prompt token count
and structural element count to diagnose collinearity.

Writes the result to data/results/analysis_summary.csv.
"""
import sys
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

# Project root relative to code/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RESULTS_DIR = PROJECT_ROOT / "data" / "results"
PARQUET_PATH = PROJECT_ROOT / "data" / "processed" / "prompt_variants.parquet"
SUMMARY_PATH = RESULTS_DIR / "analysis_summary.csv"

def load_variants_from_parquet(path: Path) -> pd.DataFrame:
    """Load prompt variants from parquet file."""
    if not path.exists():
        raise FileNotFoundError(f"Parquet file not found: {path}")
    return pd.read_parquet(path)

def compute_correlation(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute Pearson correlation between token_count and structural_element_count.
    
    Returns a dictionary with correlation coefficient, p-value (if available),
    and sample size.
    """
    if "token_count" not in df.columns or "structural_element_count" not in df.columns:
        raise ValueError(
            "DataFrame must contain 'token_count' and 'structural_element_count' columns"
        )
    
    # Drop rows with missing values in either column
    clean_df = df.dropna(subset=["token_count", "structural_element_count"])
    n = len(clean_df)
    
    if n < 2:
        return {
            "correlation": None,
            "p_value": None,
            "n_samples": n,
            "status": "insufficient_data"
        }
    
    x = clean_df["token_count"].values.astype(float)
    y = clean_df["structural_element_count"].values.astype(float)
    
    # Compute Pearson correlation
    correlation_matrix = np.corrcoef(x, y)
    correlation = correlation_matrix[0, 1]
    
    # Compute p-value using t-distribution
    # t = r * sqrt((n-2) / (1-r^2))
    if abs(correlation) >= 1.0:
        p_value = 0.0
    else:
        t_stat = correlation * np.sqrt((n - 2) / (1 - correlation**2))
        # Two-tailed p-value
        from scipy import stats
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df=n-2))
    
    return {
        "correlation": float(correlation),
        "p_value": float(p_value),
        "n_samples": n,
        "status": "computed"
    }

def write_summary(results: Dict[str, Any], output_path: Path) -> None:
    """Write correlation results to CSV, creating file if needed."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    row = {
        "metric": "token_structural_collinearity",
        "correlation_coefficient": results.get("correlation"),
        "p_value": results.get("p_value"),
        "sample_size": results.get("n_samples"),
        "status": results.get("status"),
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    # Check if file exists to determine if we need headers
    file_exists = output_path.exists()
    
    with open(output_path, mode='a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

def main() -> int:
    """Main entry point for collinearity check."""
    logger = __import__('utils.logger', fromlist=['get_logger']).get_logger(__name__)
    
    logger.info("Starting collinearity analysis (FR-013)")
    
    try:
        # Load data
        logger.info(f"Loading variants from {PARQUET_PATH}")
        df = load_variants_from_parquet(PARQUET_PATH)
        logger.info(f"Loaded {len(df)} records")
        
        # Compute correlation
        logger.info("Computing Pearson correlation")
        results = compute_correlation(df)
        
        # Log results
        logger.info(f"Correlation coefficient: {results.get('correlation')}")
        logger.info(f"P-value: {results.get('p_value')}")
        logger.info(f"Sample size: {results.get('n_samples')}")
        
        # Write to CSV
        logger.info(f"Writing results to {SUMMARY_PATH}")
        write_summary(results, SUMMARY_PATH)
        
        logger.info("Collinearity analysis complete")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during collinearity analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
