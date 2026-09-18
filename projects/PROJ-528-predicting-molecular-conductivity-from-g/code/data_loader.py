import os
import sys
import pandas as pd
import numpy as np
from typing import List, Tuple, Optional
import logging
from rdkit import Chem

def load_smiles(path: str) -> pd.DataFrame:
    """Loads SMILES strings from a CSV file, validates them, and returns a DataFrame."""
    try:
        df = pd.read_csv(path)
        df['valid'] = df['smiles'].apply(lambda x: True if Chem.MolFromSmiles(x) is not None else False)
        df['error_msg'] = df['smiles'].apply(lambda x: "" if df['valid'].iloc[-1] else "Invalid SMILES")
        return df
    except FileNotFoundError:
        logging.error(f"File not found: {path}")
        return pd.DataFrame({'smiles': [], 'valid': [], 'error_msg': []})
    except Exception as e:
        logging.error(f"Error loading SMILES from {path}: {e}")
        return pd.DataFrame({'smiles': [], 'valid': [], 'error_msg': []})

def load_and_validate_target(path: str) -> pd.DataFrame:
  """Loads target variable from a CSV file and validates its range."""
  try:
      df = pd.read_csv(path)
      if 'conductivity' in df.columns:
          # Check dynamic range
          conductivity = df['conductivity']
          if conductivity.max() - conductivity.min() >= 3:
              return df
          else:
              logging.warning("Conductivity dynamic range is less than 3 orders of magnitude.")
              return pd.DataFrame()
      elif 'HOMO_LUMO_gap' in df.columns:
          logging.warning("Conductivity missing. Using HOMO-LUMO gap as proxy.")
          return df
      else:
          logging.error("No valid target variable found (Conductivity or HOMO-LUMO gap missing).")
          return pd.DataFrame()
  except FileNotFoundError:
      logging.error(f"File not found: {path}")
      return pd.DataFrame()
  except Exception as e:
      logging.error(f"Error loading target variable from {path}: {e}")
      return pd.DataFrame()

def validate_target_variable(path: str):
    """
    Validates the target variable in a CSV file loaded directly from config.RAW_DATA_PATH.
    
    Logic:
    1. Load raw data directly from `path` (config.RAW_DATA_PATH).
    2. Check for 'conductivity' or 'charge_carrier_mobility' column.
    3. If found: Verify dynamic range (>= 3 orders of magnitude). If valid, proceed.
    4. If NOT found: Check for 'HOMO_LUMO_gap'. If found: Log warning and proceed.
    5. If NEITHER found: sys.exit(1).
    """
    import config
    
    # Load raw data directly from the provided path
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        logging.critical(f"CRITICAL: Raw data file not found at {path}")
        sys.exit(1)
    except Exception as e:
        logging.critical(f"CRITICAL: Failed to load raw data from {path}: {e}")
        sys.exit(1)

    # Check for primary target variables
    primary_targets = ['conductivity', 'charge_carrier_mobility']
    found_primary = None
    
    for target in primary_targets:
        if target in df.columns:
            found_primary = target
            break
    
    if found_primary:
        # Verify dynamic range (>= 3 orders of magnitude)
        # Assuming the values are in a linear scale where difference >= 3 implies 3 orders of magnitude
        # or if they are log-scaled, range >= 3.0. 
        # Based on T005 and T028 context, we check range >= 3.0.
        values = df[found_primary].dropna()
        if len(values) == 0:
            logging.critical(f"CRITICAL: No valid values found for {found_primary}")
            sys.exit(1)
        
        dynamic_range = values.max() - values.min()
        if dynamic_range >= 3.0:
            logging.info(f"Target variable '{found_primary}' validated with dynamic range {dynamic_range:.2f} >= 3.0")
            return True
        else:
            logging.warning(f"Target variable '{found_primary}' has dynamic range {dynamic_range:.2f} < 3.0. Proceeding but caution advised.")
            return True

    # If primary not found, check for HOMO-LUMO gap proxy
    if 'HOMO_LUMO_gap' in df.columns:
        logging.warning("CRITICAL WARNING: Conductivity missing. Using HOMO-LUMO gap as proxy for Electronic Delocalization Potential.")
        return True
    
    # If neither found
    logging.critical("CRITICAL: No valid target variable found (Conductivity or HOMO-LUMO gap missing).")
    sys.exit(1)

def validate_target_range(values: np.ndarray, min_log_range: float = 3.0) -> bool:
    """Validates the dynamic range of the target variable."""
    if len(values) == 0:
        return False
    if values.max() - values.min() >= min_log_range:
        return True
    else:
        return False

def apply_log_transformation(df: pd.DataFrame, target_col: str) -> pd.DataFrame:
    """Applies a log transformation to the target column."""
    df[f'log_{target_col}'] = np.log(df[target_col])
    return df

def process_molecule_with_error_handling(smiles: str) -> Tuple[bool, str]:
    """Processes a single molecule, handling potential errors."""
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return False, "Invalid SMILES"
        return True, ""
    except Exception as e:
        return False, str(e)

def load_processed_data(path: str) -> pd.DataFrame:
    """Loads processed data from a CSV file."""
    try:
        df = pd.read_csv(path)
        return df
    except FileNotFoundError:
        logging.error(f"File not found: {path}")
        return pd.DataFrame()
    except Exception as e:
        logging.error(f"Error loading processed data from {path}: {e}")
        return pd.DataFrame()