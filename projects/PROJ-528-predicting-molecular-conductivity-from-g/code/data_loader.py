import os
import pandas as pd
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
    """Validates the target variable in a CSV file."""
    df = load_and_validate_target(path)
    if df.empty:
        logging.error("No valid target variable found.")
        return False
    return True

def validate_target_range(values: np.ndarray, min_log_range: float = 3.0) -> bool:
    """Validates the dynamic range of the target variable."""
    if values.max() - values.min() >= 10**min_log_range:
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
