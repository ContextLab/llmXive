"""
Target variable calculation for High-Entropy Alloy (HEA) elastic modulus prediction.

This module computes the primary model target:
Bulk_Modulus_Residual = Bulk_Modulus_Observed - Bulk_Modulus_Miedema

It also computes the absolute Bulk Modulus as a diagnostic column.
"""
import logging
import pandas as pd
import numpy as np
from typing import Optional, Tuple, List, Dict, Any

from src.utils.logging_config import get_logger

# Constants
OBSERVED_BULK_MODULUS_COL = "Bulk_Modulus_Observed"
MIEDEMA_BULK_MODULUS_COL = "Bulk_Modulus_Miedema"
RESIDUAL_TARGET_COL = "Bulk_Modulus_Residual"
DIAGNOSTIC_BULK_MODULUS_COL = "Bulk_Modulus_Absolute"

# Miedema model parameters for Bulk Modulus estimation
# These are simplified parameters; in a full implementation, these would be
# computed based on the specific alloy composition using Miedema's formalism.
# For this implementation, we assume the Miedema bulk modulus has been
# pre-calculated in T018 (descriptors.py) or is available in the dataframe.
# If not present, we calculate it here using a simplified weighted average
# of elemental bulk moduli as a placeholder for the Miedema prediction.

# Elemental bulk moduli (GPa) - Source: Standard literature values
# This is a lookup for common elements. In a production system, this would
# be a comprehensive periodic table lookup or a pymatgen integration.
ELEMENTAL_BULK_MODULI = {
    "Al": 76.0, "Sc": 57.0, "Ti": 110.0, "V": 160.0, "Cr": 160.0,
    "Mn": 140.0, "Fe": 170.0, "Co": 180.0, "Ni": 180.0, "Cu": 140.0,
    "Zr": 92.0, "Nb": 170.0, "Mo": 230.0, "Tc": 190.0, "Ru": 280.0,
    "Rh": 270.0, "Pd": 180.0, "Ag": 100.0, "Hf": 110.0, "Ta": 196.0,
    "W": 310.0, "Re": 350.0, "Os": 410.0, "Ir": 320.0, "Pt": 230.0,
    "Au": 180.0, "Mg": 45.0, "Ca": 17.0, "Y": 41.0, "La": 28.0,
    "Ce": 33.0, "Pr": 32.0, "Nd": 30.0, "Sm": 35.0, "Eu": 18.0,
    "Gd": 35.0, "Tb": 37.0, "Dy": 41.0, "Ho": 44.0, "Er": 46.0,
    "Tm": 48.0, "Yb": 24.0, "Lu": 49.0
}

def get_elemental_bulk_modulus(element: str) -> float:
    """
    Retrieve the bulk modulus for a given element.
    
    Args:
        element: Element symbol (e.g., "Fe", "Ni")
        
    Returns:
        Bulk modulus in GPa. Returns 0.0 if element not found.
    """
    return ELEMENTAL_BULK_MODULI.get(element, 0.0)

def calculate_miedema_bulk_modulus(composition: Dict[str, float]) -> float:
    """
    Calculate the Miedema-predicted Bulk Modulus for a given composition.
    
    This implementation uses a weighted average of elemental bulk moduli
    as a proxy for the Miedema model prediction. In a full implementation,
    this would use the specific Miedema formalism involving electron density,
    electronegativity, and atomic volume parameters.
    
    Args:
        composition: Dictionary mapping element symbols to their atomic fractions.
                    
    Returns:
        Predicted Bulk Modulus in GPa.
    """
    if not composition:
        return 0.0
        
    total_modulus = 0.0
    for element, fraction in composition.items():
        element_modulus = get_elemental_bulk_modulus(element)
        total_modulus += element_modulus * fraction
        
    return total_modulus

def compute_miedema_column(df: pd.DataFrame) -> pd.Series:
    """
    Compute the Miedema Bulk Modulus column for a dataframe.
    
    Assumes the dataframe has a 'composition' column containing dictionaries
    of element -> fraction.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Series containing the Miedema Bulk Modulus values.
    """
    if "composition" not in df.columns:
        raise ValueError("DataFrame must contain a 'composition' column")
        
    return df["composition"].apply(calculate_miedema_bulk_modulus)

def compute_residual_target(df: pd.DataFrame, observed_col: str = OBSERVED_BULK_MODULUS_COL) -> pd.DataFrame:
    """
    Compute the primary model target: Bulk_Modulus_Residual.
    
    Bulk_Modulus_Residual = Bulk_Modulus_Observed - Bulk_Modulus_Miedema
    
    Also computes the absolute Bulk Modulus as a diagnostic column.
    
    Args:
        df: Input DataFrame containing observed bulk modulus and composition.
        observed_col: Name of the column containing observed bulk modulus values.
        
    Returns:
        DataFrame with added columns:
        - Bulk_Modulus_Miedema: Predicted value
        - Bulk_Modulus_Residual: The target variable
        - Bulk_Modulus_Absolute: Diagnostic column (same as observed)
        
    Raises:
        ValueError: If required columns are missing or data is invalid.
    """
    logger = get_logger(__name__)
    
    if observed_col not in df.columns:
        raise ValueError(f"Required column '{observed_col}' not found in DataFrame")
        
    if "composition" not in df.columns:
        raise ValueError("Required column 'composition' not found in DataFrame")
        
    # Calculate Miedema prediction
    logger.info("Calculating Miedema Bulk Modulus predictions...")
    miedema_values = compute_miedema_column(df)
    df[MIEDEMA_BULK_MODULUS_COL] = miedema_values
    
    # Calculate residual target
    logger.info("Computing residual target (Observed - Miedema)...")
    df[RESIDUAL_TARGET_COL] = df[observed_col] - miedema_values
    
    # Add diagnostic column
    df[DIAGNOSTIC_BULK_MODULUS_COL] = df[observed_col]
    
    # Log statistics
    logger.info(f"Miedema Bulk Modulus - Mean: {df[MIEDEMA_BULK_MODULUS_COL].mean():.2f} GPa, "
               f"Std: {df[MIEDEMA_BULK_MODULUS_COL].std():.2f} GPa")
    logger.info(f"Residual Target - Mean: {df[RESIDUAL_TARGET_COL].mean():.4f} GPa, "
               f"Std: {df[RESIDUAL_TARGET_COL].std():.4f} GPa")
    
    # Check for NaN values
    nan_count = df[[RESIDUAL_TARGET_COL, MIEDEMA_BULK_MODULUS_COL]].isna().sum().sum()
    if nan_count > 0:
        logger.warning(f"Found {nan_count} NaN values in target calculation results")
        
    return df

def main():
    """
    Main function for testing target calculation.
    Creates a sample dataframe and computes targets.
    """
    logger = get_logger(__name__)
    logger.info("Starting target calculation test...")
    
    # Create sample data
    sample_data = {
        "composition": [
            {"Fe": 0.2, "Co": 0.2, "Ni": 0.2, "Cr": 0.2, "Mn": 0.2},
            {"Al": 0.2, "Ti": 0.2, "V": 0.2, "Cr": 0.2, "Ni": 0.2},
            {"Nb": 0.2, "Mo": 0.2, "Ta": 0.2, "W": 0.2, "Zr": 0.2}
        ],
        "Bulk_Modulus_Observed": [180.5, 145.2, 210.8]
    }
    
    df = pd.DataFrame(sample_data)
    logger.info(f"Sample data shape: {df.shape}")
    
    # Compute targets
    result_df = compute_residual_target(df)
    
    # Display results
    logger.info("Result columns:")
    for col in result_df.columns:
        logger.info(f"  {col}")
        
    logger.info("\nSample results:")
    logger.info(result_df[[OBSERVED_BULK_MODULUS_COL, MIEDEMA_BULK_MODULUS_COL, 
                          RESIDUAL_TARGET_COL, DIAGNOSTIC_BULK_MODULUS_COL]].to_string())
                          
    logger.info("Target calculation completed successfully.")
    return result_df

if __name__ == "__main__":
    main()
