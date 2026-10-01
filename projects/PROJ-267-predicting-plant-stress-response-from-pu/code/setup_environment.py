"""
Environment setup and verification script for T002.

This script:
1. Verifies installation of critical dependencies (pandas, rpy2, imp3).
2. Verifies R installation and biomaRt availability.
3. Implements a custom MinProb LCM fallback in code/utils/lcm.py if imp3 is missing.
4. Logs deviations to docs/deviation_log.md.
5. Halts with a clear error if critical tooling is unavailable.
"""
import subprocess
import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "setup_environment.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent
UTILS_DIR = PROJECT_ROOT / "utils"
DOCS_DIR = PROJECT_ROOT.parent / "docs"
DEVIATION_LOG = DOCS_DIR / "deviation_log.md"

def run_command(cmd, check=True):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=check,
            capture_output=True,
            text=True
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, "", e.stderr

def check_python_package(package_name):
    """Check if a Python package is installed."""
    try:
        __import__(package_name)
        logger.info(f"✓ Python package '{package_name}' is installed.")
        return True
    except ImportError:
        logger.error(f"✗ Python package '{package_name}' is NOT installed.")
        return False

def check_r_installation():
    """Check if R is installed and accessible."""
    success, stdout, stderr = run_command("R --version")
    if success:
        logger.info("✓ R is installed.")
        return True
    else:
        logger.error("✗ R is NOT installed or not in PATH.")
        logger.error(f"stderr: {stderr}")
        return False

def check_biomart_r_package():
    """Check if biomaRt is installed in R."""
    # Try to load biomaRt in R
    r_code = 'if (requireNamespace("biomaRt", quietly = TRUE)) { cat("OK") } else { cat("FAIL") }'
    success, stdout, stderr = run_command(f'R --slave -e "{r_code}"')
    if success and "OK" in stdout:
        logger.info("✓ R package 'biomaRt' is installed.")
        return True
    else:
        logger.error("✗ R package 'biomaRt' is NOT installed.")
        if stderr:
            logger.error(f"stderr: {stderr}")
        return False

def check_imp3_package():
    """Check if imp3 package is available."""
    # imp3 might be available as 'imp3' or 'imp' in some contexts, but task specifies imp3
    try:
        import imp3
        logger.info("✓ Python package 'imp3' is installed.")
        return True
    except ImportError:
        logger.warning("⚠ Python package 'imp3' is NOT installed.")
        return False

def create_lcm_fallback():
    """
    Create the custom MinProb LCM implementation in code/utils/lcm.py
    if imp3 is not available.
    """
    logger.info("Creating custom MinProb LCM implementation...")
    
    UTILS_DIR.mkdir(exist_ok=True)
    lcm_file = UTILS_DIR / "lcm.py"
    
    lcm_code = '''"""
Custom Left-Censored Missing (LCM) Imputation using MinProb algorithm.
Implemented as a fallback when imp3 is unavailable (FR-002).
"""
import numpy as np
import pandas as pd
from typing import Optional, Tuple

def minprob_impute(df: pd.DataFrame, quantile: float = 0.05) -> pd.DataFrame:
    """
    Apply MinProb imputation to a DataFrame.
    
    This algorithm replaces missing values with a value drawn from a normal distribution
    centered at the minimum observed value minus a shift, simulating left-censored data.
    Specifically, it uses: x_impute = x_min - shift * sigma
    where x_min is the minimum non-missing value in the column,
    sigma is the standard deviation of non-missing values,
    and shift is a factor (often 1.8 or similar) or derived from a quantile.
    
    Here we implement a simplified version:
    1. For each column, calculate min and std of non-NaN values.
    2. Impute NaNs with min - 1.8 * std (standard MinProb heuristic) 
 OR min - (min - min_quantile) if we want to be more conservative.
 
    Following the "MinProb" description often used in proteomics:
    Impute with a value slightly below the minimum observed value.
    
    Parameters
    ----------
    df : pd.DataFrame
  Input data with NaNs representing left-censored missing values.
    quantile : float
  The quantile to use for determining the "shift" if using a quantile-based approach.
  Default 0.05 (5th percentile) is often used to estimate the noise floor.
  
    Returns
    -------
    pd.DataFrame
  DataFrame with imputed values.
    """
    df_imputed = df.copy()
    
    for col in df_imputed.columns:
  col_data = df_imputed[col]
  non_null = col_data.dropna()
  
  if len(non_null) == 0:
      # If all are missing, fill with 0 or mean of other columns? 
      # For now, fill with 0 as a placeholder, but this should ideally be handled upstream.
      df_imputed[col] = 0.0
      continue
      
  if col_data.isna().sum() == 0:
      continue
      
  min_val = non_null.min()
  std_val = non_null.std()
  
  # Standard MinProb heuristic: shift = 1.8 * std
  # Or: impute with min_val - 1.8 * std_val
  # However, to ensure we are below the minimum, we can also use:
  # min_val - (min_val - min(quantile)) 
  # Let's stick to the classic MinProb: min - 1.8 * sigma
  
  if std_val == 0:
      # If std is 0, all non-null values are the same.
      # Impute with a value slightly lower, e.g., 0.9 * min_val
      impute_val = min_val * 0.9
  else:
      impute_val = min_val - 1.8 * std_val
      
  df_imputed[col] = col_data.fillna(impute_val)
  
    return df_imputed

def filter_low_abundance(df: pd.DataFrame, detection_threshold: float = 0.5) -> pd.DataFrame:
    """
    Filter out proteins (rows) or features (columns) with low detection rates.
    
    Parameters
    ----------
    df : pd.DataFrame
  Input data.
    detection_threshold : float
  Minimum fraction of non-missing values required (0.0 to 1.0).
  
    Returns
    -------
    pd.DataFrame
  Filtered DataFrame.
    """
    # Calculate detection rate per column (feature)
    detection_rates = df.notna().mean()
    
    # Keep columns where detection rate >= threshold
    valid_columns = detection_rates[detection_rates >= detection_threshold].index
    return df[valid_columns]
'''
    
    with open(lcm_file, 'w') as f:
        f.write(lcm_code)
        
    logger.info(f"✓ Custom LCM implementation created at {lcm_file}")
    log_deviation("imp3 missing", "Using custom MinProb implementation in code/utils/lcm.py")
    return True

def log_deviation(reason, action):
    """Log a deviation to docs/deviation_log.md."""
    DOCS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    deviation_entry = f"""
## Deviation Log Entry - {timestamp}
- **Reason**: {reason}
- **Action Taken**: {action}
- **Status**: Logged
"""
    
    with open(DEVIATION_LOG, 'a') as f:
        f.write(deviation_entry)
        
    logger.info(f"✓ Deviation logged to {DEVIATION_LOG}")

def main():
    logger.info("Starting Environment Setup Verification (T002)...")
    
    # 1. Check critical Python packages
    critical_packages = ['pandas', 'scikit-learn', 'requests', 'psutil']
    missing_packages = []
    
    for pkg in critical_packages:
        if not check_python_package(pkg):
            missing_packages.append(pkg)
    
    if missing_packages:
        logger.error(f"CRITICAL: Missing Python packages: {missing_packages}")
        logger.error("Please run: pip install -r code/requirements.txt")
        sys.exit(1)
        
    # 2. Check rpy2
    if not check_python_package('rpy2'):
        logger.error("CRITICAL: rpy2 is missing. Halting.")
        sys.exit(1)
        
    # 3. Check R installation
    if not check_r_installation():
        logger.error("CRITICAL: R is not installed. Halting.")
        sys.exit(1)
        
    # 4. Check biomaRt
    if not check_biomart_r_package():
        logger.error("CRITICAL: biomaRt R package is missing. Halting.")
        sys.exit(1)
        
    # 5. Check imp3 and create fallback if needed
    imp3_available = check_imp3_package()
    if not imp3_available:
        logger.warning("imp3 is not available. Creating fallback...")
        create_lcm_fallback()
    else:
        logger.info("imp3 is available. Fallback not needed.")
        
    logger.info("Environment Setup Verification completed successfully.")
    logger.info("All critical dependencies are present.")

if __name__ == "__main__":
    main()