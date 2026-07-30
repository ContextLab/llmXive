import os
import sys
import pandas as pd
import numpy as np
from typing import Optional, Tuple, Dict, Any
from config import get_config_from_args
import logging

# Periodic table data for lookups (atomic radius in pm, electronegativity, valence)
# Simplified dictionary for common alloying elements
PERIODIC_DATA = {
    'H': {'radius': 53, 'electronegativity': 2.20, 'valence': 1},
    'He': {'radius': 31, 'electronegativity': None, 'valence': 0},
    'Li': {'radius': 167, 'electronegativity': 0.98, 'valence': 1},
    'Be': {'radius': 112, 'electronegativity': 1.57, 'valence': 2},
    'B': {'radius': 87, 'electronegativity': 2.04, 'valence': 3},
    'C': {'radius': 67, 'electronegativity': 2.55, 'valence': 4},
    'N': {'radius': 56, 'electronegativity': 3.04, 'valence': 5},
    'O': {'radius': 48, 'electronegativity': 3.44, 'valence': 6},
    'F': {'radius': 42, 'electronegativity': 3.98, 'valence': 7},
    'Ne': {'radius': 38, 'electronegativity': None, 'valence': 0},
    'Na': {'radius': 190, 'electronegativity': 0.93, 'valence': 1},
    'Mg': {'radius': 145, 'electronegativity': 1.31, 'valence': 2},
    'Al': {'radius': 118, 'electronegativity': 1.61, 'valence': 3},
    'Si': {'radius': 111, 'electronegativity': 1.90, 'valence': 4},
    'P': {'radius': 98, 'electronegativity': 2.19, 'valence': 5},
    'S': {'radius': 88, 'electronegativity': 2.58, 'valence': 6},
    'Cl': {'radius': 79, 'electronegativity': 3.16, 'valence': 7},
    'Ar': {'radius': 71, 'electronegativity': None, 'valence': 0},
    'K': {'radius': 243, 'electronegativity': 0.82, 'valence': 1},
    'Ca': {'radius': 194, 'electronegativity': 1.00, 'valence': 2},
    'Sc': {'radius': 184, 'electronegativity': 1.36, 'valence': 3},
    'Ti': {'radius': 176, 'electronegativity': 1.54, 'valence': 4},
    'V': {'radius': 171, 'electronegativity': 1.63, 'valence': 5},
    'Cr': {'radius': 166, 'electronegativity': 1.66, 'valence': 6},
    'Mn': {'radius': 161, 'electronegativity': 1.55, 'valence': 7},
    'Fe': {'radius': 156, 'electronegativity': 1.83, 'valence': 8},
    'Co': {'radius': 152, 'electronegativity': 1.88, 'valence': 9},
    'Ni': {'radius': 149, 'electronegativity': 1.91, 'valence': 10},
    'Cu': {'radius': 145, 'electronegativity': 1.90, 'valence': 11},
    'Zn': {'radius': 142, 'electronegativity': 1.65, 'valence': 12},
    'Ga': {'radius': 136, 'electronegativity': 1.81, 'valence': 13},
    'Ge': {'radius': 125, 'electronegativity': 2.01, 'valence': 14},
    'As': {'radius': 114, 'electronegativity': 2.18, 'valence': 15},
    'Se': {'radius': 103, 'electronegativity': 2.55, 'valence': 16},
    'Br': {'radius': 94, 'electronegativity': 2.96, 'valence': 17},
    'Kr': {'radius': 88, 'electronegativity': None, 'valence': 18},
    'Rb': {'radius': 265, 'electronegativity': 0.82, 'valence': 19},
    'Sr': {'radius': 219, 'electronegativity': 0.95, 'valence': 20},
    'Y': {'radius': 212, 'electronegativity': 1.22, 'valence': 21},
    'Zr': {'radius': 206, 'electronegativity': 1.33, 'valence': 22},
    'Nb': {'radius': 198, 'electronegativity': 1.6, 'valence': 23},
    'Mo': {'radius': 190, 'electronegativity': 2.16, 'valence': 24},
    'Tc': {'radius': 183, 'electronegativity': 1.9, 'valence': 25},
    'Ru': {'radius': 178, 'electronegativity': 2.2, 'valence': 26},
    'Rh': {'radius': 173, 'electronegativity': 2.28, 'valence': 27},
    'Pd': {'radius': 169, 'electronegativity': 2.20, 'valence': 28},
    'Ag': {'radius': 165, 'electronegativity': 1.93, 'valence': 29},
    'Cd': {'radius': 161, 'electronegativity': 1.69, 'valence': 30},
    'In': {'radius': 156, 'electronegativity': 1.78, 'valence': 31},
    'Sn': {'radius': 145, 'electronegativity': 1.96, 'valence': 32},
    'Sb': {'radius': 133, 'electronegativity': 2.05, 'valence': 33},
    'Te': {'radius': 123, 'electronegativity': 2.1, 'valence': 34},
    'I': {'radius': 115, 'electronegativity': 2.66, 'valence': 35},
    'Xe': {'radius': 108, 'electronegativity': None, 'valence': 36},
    'Cs': {'radius': 298, 'electronegativity': 0.79, 'valence': 37},
    'Ba': {'radius': 253, 'electronegativity': 0.89, 'valence': 38},
    'La': {'radius': 226, 'electronegativity': 1.1, 'valence': 39},
    'Ce': {'radius': 210, 'electronegativity': 1.12, 'valence': 40},
    'Pr': {'radius': 207, 'electronegativity': 1.13, 'valence': 41},
    'Nd': {'radius': 204, 'electronegativity': 1.14, 'valence': 42},
    'Pm': {'radius': 205, 'electronegativity': 1.13, 'valence': 43},
    'Sm': {'radius': 201, 'electronegativity': 1.17, 'valence': 44},
    'Eu': {'radius': 209, 'electronegativity': 1.2, 'valence': 45},
    'Gd': {'radius': 200, 'electronegativity': 1.2, 'valence': 46},
    'Tb': {'radius': 196, 'electronegativity': 1.2, 'valence': 47},
    'Dy': {'radius': 195, 'electronegativity': 1.22, 'valence': 48},
    'Ho': {'radius': 192, 'electronegativity': 1.23, 'valence': 49},
    'Er': {'radius': 189, 'electronegativity': 1.24, 'valence': 50},
    'Tm': {'radius': 187, 'electronegativity': 1.25, 'valence': 51},
    'Yb': {'radius': 187, 'electronegativity': 1.1, 'valence': 52},
    'Lu': {'radius': 186, 'electronegativity': 1.27, 'valence': 53},
    'Hf': {'radius': 208, 'electronegativity': 1.3, 'valence': 54},
    'Ta': {'radius': 205, 'electronegativity': 1.5, 'valence': 55},
    'W': {'radius': 199, 'electronegativity': 2.36, 'valence': 56},
    'Re': {'radius': 196, 'electronegativity': 1.9, 'valence': 57},
    'Os': {'radius': 192, 'electronegativity': 2.2, 'valence': 58},
    'Ir': {'radius': 190, 'electronegativity': 2.20, 'valence': 59},
    'Pt': {'radius': 186, 'electronegativity': 2.28, 'valence': 60},
    'Au': {'radius': 185, 'electronegativity': 2.54, 'valence': 61},
    'Hg': {'radius': 182, 'electronegativity': 2.00, 'valence': 62},
    'Tl': {'radius': 175, 'electronegativity': 1.62, 'valence': 63},
    'Pb': {'radius': 154, 'electronegativity': 2.33, 'valence': 64},
    'Bi': {'radius': 143, 'electronegativity': 2.02, 'valence': 65},
    'Po': {'radius': 135, 'electronegativity': 2.0, 'valence': 66},
    'At': {'radius': 127, 'electronegativity': 2.2, 'valence': 67},
    'Rn': {'radius': 120, 'electronegativity': None, 'valence': 68},
    'Fr': {'radius': 348, 'electronegativity': 0.7, 'valence': 69},
    'Ra': {'radius': 283, 'electronegativity': 0.9, 'valence': 70},
    'Ac': {'radius': 260, 'electronegativity': 1.1, 'valence': 71},
    'Th': {'radius': 237, 'electronegativity': 1.3, 'valence': 72},
    'Pa': {'radius': 243, 'electronegativity': 1.5, 'valence': 73},
    'U': {'radius': 240, 'electronegativity': 1.38, 'valence': 74},
    'Np': {'radius': 221, 'electronegativity': 1.36, 'valence': 75},
    'Pu': {'radius': 243, 'electronegativity': 1.28, 'valence': 76},
    'Am': {'radius': 244, 'electronegativity': 1.3, 'valence': 77},
    'Cm': {'radius': 245, 'electronegativity': 1.3, 'valence': 78},
    'Bk': {'radius': 244, 'electronegativity': 1.3, 'valence': 79},
    'Cf': {'radius': 245, 'electronegativity': 1.3, 'valence': 80},
    'Es': {'radius': 245, 'electronegativity': 1.3, 'valence': 81},
    'Fm': {'radius': 245, 'electronegativity': 1.3, 'valence': 82},
    'Md': {'radius': 245, 'electronegativity': 1.3, 'valence': 83},
    'No': {'radius': 245, 'electronegativity': 1.3, 'valence': 84},
    'Lr': {'radius': 245, 'electronegativity': 1.3, 'valence': 85},
    'Rf': {'radius': 245, 'electronegativity': 1.3, 'valence': 86},
    'Db': {'radius': 245, 'electronegativity': 1.3, 'valence': 87},
    'Sg': {'radius': 245, 'electronegativity': 1.3, 'valence': 88},
    'Bh': {'radius': 245, 'electronegativity': 1.3, 'valence': 89},
    'Hs': {'radius': 245, 'electronegativity': 1.3, 'valence': 90},
    'Mt': {'radius': 245, 'electronegativity': 1.3, 'valence': 91},
    'Ds': {'radius': 245, 'electronegativity': 1.3, 'valence': 92},
    'Rg': {'radius': 245, 'electronegativity': 1.3, 'valence': 93},
    'Cn': {'radius': 245, 'electronegativity': 1.3, 'valence': 94},
    'Nh': {'radius': 245, 'electronegativity': 1.3, 'valence': 95},
    'Fl': {'radius': 245, 'electronegativity': 1.3, 'valence': 96},
    'Mc': {'radius': 245, 'electronegativity': 1.3, 'valence': 97},
    'Lv': {'radius': 245, 'electronegativity': 1.3, 'valence': 98},
    'Ts': {'radius': 245, 'electronegativity': 1.3, 'valence': 99},
    'Og': {'radius': 245, 'electronegativity': 1.3, 'valence': 100},
}

# Oxide formation enthalpies (kJ/mol) for common oxides
OXIDE_ENTHALPIES = {
    'Al': -1675.7,  # Al2O3
    'Cr': -1139.7,  # Cr2O3
    'Fe': -824.2,   # Fe2O3
    'Ni': -239.7,   # NiO
    'Ti': -944.0,   # TiO2
    'Si': -910.9,   # SiO2
    'Mn': -385.2,   # MnO
    'Mo': -581.0,   # MoO3 (approx)
    'Co': -237.9,   # CoO
    'Cu': -155.2,   # CuO
    'W': -842.9,    # WO3
    'V': -1130.0,   # V2O5
    'Nb': -1427.0,  # Nb2O5
    'Ta': -1640.0,  # Ta2O5
    'Zr': -1100.0,  # ZrO2
    'Hf': -1090.0,  # HfO2
    'Y': -1900.0,   # Y2O3
    'La': -1790.0,  # La2O3
    'Mg': -601.7,   # MgO
    'Ca': -635.1,   # CaO
}

logger = logging.getLogger(__name__)

def calculate_thermodynamic_descriptors(row: pd.Series) -> Dict[str, float]:
    """
    Calculate thermodynamic descriptors based on elemental composition.
    Returns a dictionary with calculated features.
    """
    descriptors = {}
    
    # Calculate weighted average properties
    weighted_atomic_radius = 0.0
    weighted_electronegativity = 0.0
    weighted_valence = 0.0
    total_weight = 0.0
    
    # Extract elemental composition from the row
    # Expected format: keys like 'Ni', 'Cr', 'Al', etc.
    for element, weight_pct in row.items():
        if element in ['observed_weight_gain', 'grain_size', 'precipitate_fraction']:
            continue
        
        try:
            weight_pct = float(weight_pct)
            if weight_pct <= 0:
                continue
            
            total_weight += weight_pct
            
            if element in PERIODIC_DATA:
                data = PERIODIC_DATA[element]
                weighted_atomic_radius += weight_pct * data['radius']
                if data['electronegativity'] is not None:
                    weighted_electronegativity += weight_pct * data['electronegativity']
                weighted_valence += weight_pct * data['valence']
            
            # Calculate oxide formation enthalpy contribution
            if element in OXIDE_ENTHALPIES:
                descriptors[f'{element}_oxide_enthalpy'] = OXIDE_ENTHALPIES[element]
            else:
                descriptors[f'{element}_oxide_enthalpy'] = 0.0
                
        except (ValueError, TypeError):
            continue
    
    # Normalize by total weight
    if total_weight > 0:
        descriptors['avg_atomic_radius'] = weighted_atomic_radius / total_weight
        descriptors['avg_electronegativity'] = weighted_electronegativity / total_weight
        descriptors['avg_valence'] = weighted_valence / total_weight
    else:
        descriptors['avg_atomic_radius'] = 0.0
        descriptors['avg_electronegativity'] = 0.0
        descriptors['avg_valence'] = 0.0
    
    # Calculate oxide formation enthalpy weighted average
    oxide_enthalpy_sum = 0.0
    oxide_weight_sum = 0.0
    for element, weight_pct in row.items():
        if element in ['observed_weight_gain', 'grain_size', 'precipitate_fraction']:
            continue
        try:
            weight_pct = float(weight_pct)
            if weight_pct <= 0:
                continue
            if element in OXIDE_ENTHALPIES:
                oxide_enthalpy_sum += weight_pct * OXIDE_ENTHALPIES[element]
                oxide_weight_sum += weight_pct
        except (ValueError, TypeError):
            continue
    
    if oxide_weight_sum > 0:
        descriptors['weighted_oxide_enthalpy'] = oxide_enthalpy_sum / oxide_weight_sum
    else:
        descriptors['weighted_oxide_enthalpy'] = 0.0
    
    return descriptors

def validate_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Validate the input dataframe and return cleaned data with warnings.
    
    Args:
        df: Input dataframe with elemental composition and target
        
    Returns:
        Tuple of (cleaned dataframe, list of warnings)
    """
    warnings = []
    required_cols = ['observed_weight_gain']
    
    # Check for required columns
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in input data")
    
    # Identify elemental columns (exclude known non-elemental columns)
    non_elemental_cols = ['observed_weight_gain', 'grain_size', 'precipitate_fraction']
    elemental_cols = [col for col in df.columns if col not in non_elemental_cols]
    
    # Validate elemental columns
    for col in elemental_cols:
        if df[col].isnull().any():
            warnings.append(f"Column '{col}' contains null values. Filling with 0.")
            df[col] = df[col].fillna(0)
        
        if df[col].dtype not in [np.float64, np.float32, np.int64, np.int32]:
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                warnings.append(f"Column '{col}' converted to numeric.")
            except Exception as e:
                warnings.append(f"Warning: Could not convert column '{col}' to numeric: {str(e)}")
    
    # Check for negative values in elemental composition
    for col in elemental_cols:
        if (df[col] < 0).any():
            warnings.append(f"Column '{col}' contains negative values. Setting to 0.")
            df.loc[df[col] < 0, col] = 0
    
    # Check for negative weight gain
    if (df['observed_weight_gain'] < 0).any():
        warnings.append("observed_weight_gain contains negative values. Setting to 0.")
        df.loc[df['observed_weight_gain'] < 0, 'observed_weight_gain'] = 0
    
    # Check for microstructural features
    has_grain_size = 'grain_size' in df.columns
    has_precipitate = 'precipitate_fraction' in df.columns
    
    if has_grain_size:
        if df['grain_size'].isnull().any():
            warnings.append("grain_size contains null values. Will be handled in processing.")
        else:
            # Validate grain_size is positive
            if (df['grain_size'] < 0).any():
                warnings.append("grain_size contains negative values. Setting to 0.")
                df.loc[df['grain_size'] < 0, 'grain_size'] = 0
    
    if has_precipitate:
        if df['precipitate_fraction'].isnull().any():
            warnings.append("precipitate_fraction contains null values. Will be handled in processing.")
        else:
            # Validate precipitate_fraction is between 0 and 1
            if (df['precipitate_fraction'] < 0).any() or (df['precipitate_fraction'] > 1).any():
                warnings.append("precipitate_fraction contains values outside [0, 1]. Clamping to [0, 1].")
                df['precipitate_fraction'] = df['precipitate_fraction'].clip(0, 1)
    
    return df, warnings

def downsample_dataset(df: pd.DataFrame, target_size: int = 500) -> pd.DataFrame:
    """
    Downsample the dataset if it exceeds the target size.
    
    Args:
        df: Input dataframe
        target_size: Maximum number of rows to keep
        
    Returns:
        Downsampled dataframe
    """
    if len(df) <= target_size:
        return df
    
    # Random sample without replacement
    logger.info(f"Downsampling dataset from {len(df)} to {target_size} rows")
    return df.sample(n=target_size, random_state=42).reset_index(drop=True)

def process_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process the input dataframe by calculating thermodynamic descriptors
    and handling microstructural features if present.
    
    Args:
        df: Input dataframe with elemental composition and optional microstructural features
        
    Returns:
        Processed dataframe with additional feature columns
    """
    # Validate data first
    df, warnings = validate_data(df)
    for warning in warnings:
        logger.warning(warning)
    
    # Calculate thermodynamic descriptors for each row
    descriptors_list = []
    for idx, row in df.iterrows():
        descriptors = calculate_thermodynamic_descriptors(row)
        descriptors_list.append(descriptors)
    
    # Convert descriptors to DataFrame and concatenate
    descriptors_df = pd.DataFrame(descriptors_list)
    
    # Identify which descriptor columns are new
    existing_cols = set(df.columns)
    new_cols = [col for col in descriptors_df.columns if col not in existing_cols]
    
    # Add new descriptor columns to the main dataframe
    for col in new_cols:
        df[col] = descriptors_df[col].values
    
    # Handle microstructural features
    has_grain_size = 'grain_size' in df.columns
    has_precipitate = 'precipitate_fraction' in df.columns
    
    if has_grain_size:
        # Log if grain_size has null values
        if df['grain_size'].isnull().any():
            logger.info("grain_size contains null values. These will be handled during model training.")
            # Fill null values with a sentinel value (e.g., -1) to indicate missing data
            df['grain_size'] = df['grain_size'].fillna(-1)
        else:
            # Normalize grain_size if needed (log transform for better distribution)
            if (df['grain_size'] > 0).all():
                df['log_grain_size'] = np.log(df['grain_size'])
            else:
                df['log_grain_size'] = df['grain_size']  # Keep as is if non-positive values exist
    
    if has_precipitate:
        # Log if precipitate_fraction has null values
        if df['precipitate_fraction'].isnull().any():
            logger.info("precipitate_fraction contains null values. These will be handled during model training.")
            # Fill null values with a sentinel value (e.g., -1) to indicate missing data
            df['precipitate_fraction'] = df['precipitate_fraction'].fillna(-1)
        else:
            # No transformation needed, values are already in [0, 1]
            pass
    
    # Log the final feature set
    feature_cols = [col for col in df.columns if col not in ['observed_weight_gain']]
    logger.info(f"Processed data with {len(feature_cols)} features: {feature_cols}")
    
    return df

def main():
    """
    Main function to process data from a CSV file.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Process alloy data for oxidation resistance prediction')
    parser.add_argument('--input', type=str, required=True, help='Input CSV file path')
    parser.add_argument('--output', type=str, required=True, help='Output CSV file path')
    parser.add_argument('--mode', type=str, default='local', choices=['ci', 'local'], 
                      help='Execution mode: ci or local')
    args = parser.parse_args()
    
    # Configure logging
    from utils.logger import configure_logging
    configure_logging()
    
    # Load data
    logger.info(f"Loading data from {args.input}")
    df = pd.read_csv(args.input)
    logger.info(f"Loaded {len(df)} rows")
    
    # Downsample if necessary based on mode
    config = get_config_from_args(args)
    if args.mode == 'ci' and len(df) > 500:
        df = downsample_dataset(df, 500)
    elif args.mode == 'local' and len(df) > 1000:
        df = downsample_dataset(df, 1000)
    
    # Process data
    logger.info("Processing data...")
    processed_df = process_data(df)
    
    # Save processed data
    logger.info(f"Saving processed data to {args.output}")
    processed_df.to_csv(args.output, index=False)
    logger.info("Done!")

if __name__ == '__main__':
    main()