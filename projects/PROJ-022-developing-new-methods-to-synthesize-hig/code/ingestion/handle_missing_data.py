"""
Handles missing data via imputation or halting.
"""
import os
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime
from utils.errors import DataInsufficientError
from utils.constants import get_polymer_class_from_smiles

def calculate_missing_ratio(df: pd.DataFrame, columns: Optional[List[str]] = None) -> float:
    """Calculates the overall missing ratio for specified columns."""
    if columns is None:
        columns = ['permeability', 'selectivity', 'smiles']
    
    total_cells = df[columns].size
    missing_cells = df[columns].isnull().sum().sum()
    
    if total_cells == 0:
        return 0.0
    return missing_cells / total_cells

def impute_polymer_class_averages(df: pd.DataFrame) -> pd.DataFrame:
    """
    Imputes missing 'class_name' using SMILES substructure lookup.
    Then imputes missing 'permeability' and 'selectivity' using class averages.
    """
    df = df.copy()
    
    # 1. Impute Class Name if missing
    if 'class_name' in df.columns:
        mask_missing_class = df['class_name'].isnull()
        if mask_missing_class.any():
            # Derive from SMILES
            if 'smiles' in df.columns:
                df.loc[mask_missing_class, 'class_name'] = df.loc[mask_missing_class, 'smiles'].apply(get_polymer_class_from_smiles)
            else:
                df.loc[mask_missing_class, 'class_name'] = 'Unknown'
    
    # 2. Calculate class averages for permeability and selectivity
    class_means = {}
    for col in ['permeability', 'selectivity']:
        if col in df.columns:
            class_means[col] = df.groupby('class_name')[col].mean().to_dict()
    
    # 3. Impute missing values using class averages
    for col in ['permeability', 'selectivity']:
        if col in df.columns:
            mask_missing = df[col].isnull()
            if mask_missing.any():
                for cls, mean_val in class_means.get(col, {}).items():
                    if pd.notna(mean_val):
                        df.loc[mask_missing & (df['class_name'] == cls), col] = mean_val
                
                # Fallback for 'Unknown' or missing class
                fallback_mean = df[col].mean()
                if pd.notna(fallback_mean):
                    df.loc[mask_missing & (df['class_name'].isnull()), col] = fallback_mean
                
                df.loc[mask_missing, 'imputed'] = True

    return df

def handle_missing_data(df: pd.DataFrame) -> tuple:
    """
    Main logic to handle missing data.
    - If missing > 20% -> Halt with DataInsufficientError.
    - If 0 < missing <= 20% -> Impute and generate flags.
    """
    ratio = calculate_missing_ratio(df)
    
    flags = []
    
    if ratio > 0.20:
        raise DataInsufficientError(
            f"Missing data ratio ({ratio:.2%}) exceeds 20% threshold. "
            "Dataset is insufficient for processing."
        )
    
    if ratio > 0:
        logger.info(f"Missing data ratio is {ratio:.2%}. Initiating imputation.")
        df = impute_polymer_class_averages(df)
        flags.append({
            "type": "imputation_performed",
            "missing_ratio": ratio,
            "timestamp": datetime.now().isoformat()
        })
    
    return df, flags

logger = logging.getLogger(__name__)

def main():
    # Dummy test
    data = {
        'polymer_name': ['P1', 'P2', 'P3'],
        'smiles': ['c1ccccc1', 'C=O', 'N'],
        'permeability': [10.0, None, 20.0],
        'class_name': ['Polystyrene', None, None]
    }
    df = pd.DataFrame(data)
    try:
        result, flags = handle_missing_data(df)
        print(result)
        print(flags)
    except DataInsufficientError as e:
        print(f"HALTED: {e}")

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    main()
