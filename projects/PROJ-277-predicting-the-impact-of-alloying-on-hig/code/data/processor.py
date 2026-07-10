import os
import sys
import pandas as pd
import numpy as np
from typing import Optional, Tuple, Dict, Any
from config import get_config_from_args
from utils.logger import get_logger, log_data_validation_failure
import logging

# Periodic Table Lookup Data (Simplified for common alloying elements)
# Format: element -> {atomic_radius (pm), electronegativity (Pauling), valence_electrons, oxide_formation_enthalpy (kJ/mol)}
# Oxide formation enthalpy is for the most stable simple oxide (e.g., Al2O3, Cr2O3, NiO)
PERIODIC_DATA = {
    'H': {'radius': 37, 'en': 2.20, 'valence': 1, 'oxide_dh': -241.8}, # H2O
    'He': {'radius': 32, 'en': None, 'valence': 0, 'oxide_dh': None},
    'Li': {'radius': 152, 'en': 0.98, 'valence': 1, 'oxide_dh': -598.0}, # Li2O
    'Be': {'radius': 112, 'en': 1.57, 'valence': 2, 'oxide_dh': -609.6}, # BeO
    'B': {'radius': 85, 'en': 2.04, 'valence': 3, 'oxide_dh': -1273.0}, # B2O3
    'C': {'radius': 77, 'en': 2.55, 'valence': 4, 'oxide_dh': -393.5}, # CO2
    'N': {'radius': 75, 'en': 3.04, 'valence': 5, 'oxide_dh': None},
    'O': {'radius': 73, 'en': 3.44, 'valence': 2, 'oxide_dh': 0.0}, # Reference
    'F': {'radius': 72, 'en': 3.98, 'valence': 1, 'oxide_dh': None},
    'Ne': {'radius': 71, 'en': None, 'valence': 0, 'oxide_dh': None},
    'Na': {'radius': 186, 'en': 0.93, 'valence': 1, 'oxide_dh': -414.2}, # Na2O
    'Mg': {'radius': 160, 'en': 1.31, 'valence': 2, 'oxide_dh': -601.7}, # MgO
    'Al': {'radius': 143, 'en': 1.61, 'valence': 3, 'oxide_dh': -1675.7}, # Al2O3
    'Si': {'radius': 117, 'en': 1.90, 'valence': 4, 'oxide_dh': -910.9}, # SiO2
    'P': {'radius': 110, 'en': 2.19, 'valence': 5, 'oxide_dh': -1492.0}, # P2O5
    'S': {'radius': 104, 'en': 2.58, 'valence': 6, 'oxide_dh': -296.8}, # SO2
    'Cl': {'radius': 99, 'en': 3.16, 'valence': 7, 'oxide_dh': None},
    'Ar': {'radius': 98, 'en': None, 'valence': 0, 'oxide_dh': None},
    'K': {'radius': 227, 'en': 0.82, 'valence': 1, 'oxide_dh': -361.5}, # K2O
    'Ca': {'radius': 197, 'en': 1.00, 'valence': 2, 'oxide_dh': -635.1}, # CaO
    'Sc': {'radius': 162, 'en': 1.36, 'valence': 3, 'oxide_dh': -1908.8}, # Sc2O3
    'Ti': {'radius': 147, 'en': 1.54, 'valence': 4, 'oxide_dh': -944.7}, # TiO2
    'V': {'radius': 134, 'en': 1.63, 'valence': 5, 'oxide_dh': -1130.0}, # V2O5
    'Cr': {'radius': 128, 'en': 1.66, 'valence': 6, 'oxide_dh': -1139.7}, # Cr2O3
    'Mn': {'radius': 127, 'en': 1.55, 'valence': 7, 'oxide_dh': -385.2}, # MnO (simplified)
    'Fe': {'radius': 126, 'en': 1.83, 'valence': 8, 'oxide_dh': -824.2}, # Fe2O3
    'Co': {'radius': 125, 'en': 1.88, 'valence': 9, 'oxide_dh': -237.9}, # CoO
    'Ni': {'radius': 124, 'en': 1.91, 'valence': 10, 'oxide_dh': -239.7}, # NiO
    'Cu': {'radius': 128, 'en': 1.90, 'valence': 11, 'oxide_dh': -157.3}, # CuO
    'Zn': {'radius': 134, 'en': 1.65, 'valence': 12, 'oxide_dh': -350.5}, # ZnO
    'Ga': {'radius': 135, 'en': 1.81, 'valence': 13, 'oxide_dh': -1071.0}, # Ga2O3
    'Ge': {'radius': 122, 'en': 2.01, 'valence': 14, 'oxide_dh': -533.0}, # GeO2
    'As': {'radius': 121, 'en': 2.18, 'valence': 15, 'oxide_dh': -924.5}, # As2O5
    'Se': {'radius': 117, 'en': 2.55, 'valence': 16, 'oxide_dh': -237.9}, # SeO2
    'Br': {'radius': 114, 'en': 2.96, 'valence': 17, 'oxide_dh': None},
    'Kr': {'radius': 110, 'en': None, 'valence': 18, 'oxide_dh': None},
    'Rb': {'radius': 248, 'en': 0.82, 'valence': 19, 'oxide_dh': -301.0}, # Rb2O
    'Sr': {'radius': 215, 'en': 0.95, 'valence': 20, 'oxide_dh': -592.0}, # SrO
    'Y': {'radius': 180, 'en': 1.22, 'valence': 21, 'oxide_dh': -1904.0}, # Y2O3
    'Zr': {'radius': 160, 'en': 1.33, 'valence': 22, 'oxide_dh': -1100.6}, # ZrO2
    'Nb': {'radius': 146, 'en': 1.60, 'valence': 23, 'oxide_dh': -1433.0}, # Nb2O5
    'Mo': {'radius': 139, 'en': 2.16, 'valence': 24, 'oxide_dh': -745.0}, # MoO3
    'Tc': {'radius': 136, 'en': 1.90, 'valence': 25, 'oxide_dh': None},
    'Ru': {'radius': 134, 'en': 2.20, 'valence': 26, 'oxide_dh': None},
    'Rh': {'radius': 134, 'en': 2.28, 'valence': 27, 'oxide_dh': None},
    'Pd': {'radius': 137, 'en': 2.20, 'valence': 28, 'oxide_dh': None},
    'Ag': {'radius': 144, 'en': 1.93, 'valence': 29, 'oxide_dh': -31.7}, # Ag2O
    'Cd': {'radius': 151, 'en': 1.69, 'valence': 30, 'oxide_dh': -328.2}, # CdO
    'In': {'radius': 166, 'en': 1.78, 'valence': 31, 'oxide_dh': -925.8}, # In2O3
    'Sn': {'radius': 140, 'en': 1.96, 'valence': 32, 'oxide_dh': -577.6}, # SnO2
    'Sb': {'radius': 140, 'en': 2.05, 'valence': 33, 'oxide_dh': -715.0}, # Sb2O5
    'Te': {'radius': 136, 'en': 2.10, 'valence': 34, 'oxide_dh': -320.0}, # TeO2
    'I': {'radius': 133, 'en': 2.66, 'valence': 35, 'oxide_dh': None},
    'Xe': {'radius': 130, 'en': None, 'valence': 36, 'oxide_dh': None},
    'Cs': {'radius': 265, 'en': 0.79, 'valence': 37, 'oxide_dh': -231.0}, # Cs2O
    'Ba': {'radius': 222, 'en': 0.89, 'valence': 38, 'oxide_dh': -548.0}, # BaO
    'La': {'radius': 187, 'en': 1.10, 'valence': 39, 'oxide_dh': -1794.0}, # La2O3
    'Ce': {'radius': 181, 'en': 1.12, 'valence': 40, 'oxide_dh': -1733.0}, # CeO2
    'Pr': {'radius': 182, 'en': 1.13, 'valence': 41, 'oxide_dh': -1807.0}, # Pr6O11
    'Nd': {'radius': 181, 'en': 1.14, 'valence': 42, 'oxide_dh': -1710.0}, # Nd2O3
    'Pm': {'radius': 183, 'en': None, 'valence': 43, 'oxide_dh': None},
    'Sm': {'radius': 180, 'en': 1.17, 'valence': 44, 'oxide_dh': -1815.0}, # Sm2O3
    'Eu': {'radius': 199, 'en': None, 'valence': 45, 'oxide_dh': None},
    'Gd': {'radius': 179, 'en': 1.20, 'valence': 46, 'oxide_dh': -1823.0}, # Gd2O3
    'Tb': {'radius': 177, 'en': None, 'valence': 47, 'oxide_dh': None},
    'Dy': {'radius': 178, 'en': 1.22, 'valence': 48, 'oxide_dh': -1884.0}, # Dy2O3
    'Ho': {'radius': 176, 'en': 1.23, 'valence': 49, 'oxide_dh': -1895.0}, # Ho2O3
    'Er': {'radius': 176, 'en': 1.24, 'valence': 50, 'oxide_dh': -1903.0}, # Er2O3
    'Tm': {'radius': 175, 'en': 1.25, 'valence': 51, 'oxide_dh': -1910.0}, # Tm2O3
    'Yb': {'radius': 194, 'en': None, 'valence': 52, 'oxide_dh': None},
    'Lu': {'radius': 174, 'en': 1.27, 'valence': 53, 'oxide_dh': -1920.0}, # Lu2O3
    'Hf': {'radius': 159, 'en': 1.30, 'valence': 54, 'oxide_dh': -1130.0}, # HfO2
    'Ta': {'radius': 146, 'en': 1.50, 'valence': 55, 'oxide_dh': -1430.0}, # Ta2O5
    'W': {'radius': 139, 'en': 2.36, 'valence': 56, 'oxide_dh': -842.0}, # WO3
    'Re': {'radius': 137, 'en': 1.90, 'valence': 57, 'oxide_dh': None},
    'Os': {'radius': 135, 'en': 2.20, 'valence': 58, 'oxide_dh': None},
    'Ir': {'radius': 136, 'en': 2.20, 'valence': 59, 'oxide_dh': None},
    'Pt': {'radius': 139, 'en': 2.28, 'valence': 60, 'oxide_dh': None},
    'Au': {'radius': 144, 'en': 2.54, 'valence': 61, 'oxide_dh': None},
    'Hg': {'radius': 151, 'en': 2.00, 'valence': 62, 'oxide_dh': -90.8}, # HgO
    'Tl': {'radius': 170, 'en': 1.62, 'valence': 63, 'oxide_dh': -576.0}, # Tl2O3
    'Pb': {'radius': 175, 'en': 2.33, 'valence': 64, 'oxide_dh': -217.3}, # PbO
    'Bi': {'radius': 167, 'en': 2.02, 'valence': 65, 'oxide_dh': -570.0}, # Bi2O3
    'Po': {'radius': 167, 'en': None, 'valence': 66, 'oxide_dh': None},
    'At': {'radius': 140, 'en': None, 'valence': 67, 'oxide_dh': None},
    'Rn': {'radius': 140, 'en': None, 'valence': 68, 'oxide_dh': None},
}

# Common alloying elements that might be missing or have incomplete data in the above
# We will use averages for these if not found
AVERAGE_PERIODIC = {
    'radius': 135.0, # Approximate average metallic radius
    'en': 1.8,       # Approximate average electronegativity
    'valence': 3,    # Approximate average valence
    'oxide_dh': -500.0 # Approximate average oxide enthalpy
}

def calculate_thermodynamic_descriptors(df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """
    Calculate thermodynamic descriptors and periodic table features for each alloy sample.
    
    Args:
        df: DataFrame with 'elemental_composition' column (dicts of element: wt%)
        logger: Logger instance
        
    Returns:
        DataFrame with new columns for descriptors
    """
    logger.info("Calculating thermodynamic descriptors and periodic features...")
    
    # Initialize new columns
    desc_cols = [
        'weighted_avg_radius', 'weighted_avg_en', 'weighted_avg_valence', 
        'weighted_avg_oxide_dh', 'num_elements', 'dominant_element'
    ]
    
    for col in desc_cols:
        df[col] = np.nan
        
    def process_composition(composition: dict) -> Tuple[float, float, float, float, int, str]:
        if not isinstance(composition, dict) or not composition:
            return np.nan, np.nan, np.nan, np.nan, 0, "Unknown"
        
        total_weight = sum(composition.values())
        if total_weight == 0:
            return np.nan, np.nan, np.nan, np.nan, 0, "Unknown"
        
        weighted_radius = 0.0
        weighted_en = 0.0
        weighted_valence = 0.0
        weighted_oxide_dh = 0.0
        num_elements = len(composition)
        dominant_element = max(composition, key=composition.get)
        
        # Calculate weighted averages
        for elem, weight_pct in composition.items():
            elem_lower = elem.strip().lower()
            # Find in periodic data (case insensitive)
            found_key = None
            for key in PERIODIC_DATA:
                if key.lower() == elem_lower:
                    found_key = key
                    break
            
            if found_key:
                data = PERIODIC_DATA[found_key]
                weight_frac = weight_pct / total_weight
                
                if data['radius'] is not None:
                    weighted_radius += data['radius'] * weight_frac
                if data['en'] is not None:
                    weighted_en += data['en'] * weight_frac
                if data['valence'] is not None:
                    weighted_valence += data['valence'] * weight_frac
                if data['oxide_dh'] is not None:
                    weighted_oxide_dh += data['oxide_dh'] * weight_frac
            else:
                # Unknown element - use average
                weight_frac = weight_pct / total_weight
                weighted_radius += AVERAGE_PERIODIC['radius'] * weight_frac
                weighted_en += AVERAGE_PERIODIC['en'] * weight_frac
                weighted_valence += AVERAGE_PERIODIC['valence'] * weight_frac
                weighted_oxide_dh += AVERAGE_PERIODIC['oxide_dh'] * weight_frac
                logger.warning(f"Unknown element '{elem}' encountered. Using periodic averages.")
        
        return weighted_radius, weighted_en, weighted_valence, weighted_oxide_dh, num_elements, dominant_element
        
    # Apply function
    results = df['elemental_composition'].apply(process_composition)
    df['weighted_avg_radius'] = [r[0] for r in results]
    df['weighted_avg_en'] = [r[1] for r in results]
    df['weighted_avg_valence'] = [r[2] for r in results]
    df['weighted_avg_oxide_dh'] = [r[3] for r in results]
    df['num_elements'] = [r[4] for r in results]
    df['dominant_element'] = [r[5] for r in results]
    
    logger.info(f"Descriptors calculated for {len(df)} samples.")
    return df

def validate_data(df: pd.DataFrame, logger: logging.Logger) -> bool:
    """
    Validate data for required fields and handle missing/unknown elements.
    
    Logic:
    - Halt if Ni, Cr, Al, or weight_gain is missing.
    - If unknown element > 0.5 wt%, flag and exclude.
    - If unknown element <= 0.5 wt%, impute and flag.
    
    Returns:
        bool: True if validation passes, False otherwise.
    """
    logger.info("Validating dataset...")
    
    required_cols = ['elemental_composition', 'observed_weight_gain']
    for col in required_cols:
        if col not in df.columns:
            logger.error(f"Missing required column: {col}")
            return False
            
    # Check for Ni, Cr, Al in composition
    for idx, row in df.iterrows():
        comp = row['elemental_composition']
        if not isinstance(comp, dict):
            logger.error(f"Invalid composition format at row {idx}")
            return False
            
        comp_lower = {k.lower(): v for k, v in comp.items()}
        
        # Check required elements (Ni, Cr, Al)
        if 'ni' not in comp_lower or 'cr' not in comp_lower or 'al' not in comp_lower:
            # Task T040 requirement: Halt if any required predictor is missing
            # Note: The task description says "if *any* required predictor (Ni, Cr, Al, weight gain) is missing"
            # We assume this means the alloy must contain these elements to be valid for this specific model
            # However, in real alloys, sometimes one might be 0. But for the model to work as described:
            # "Halt execution immediately... if any required predictor... is missing"
            # We will treat missing as not present in the dict or 0.
            # Let's assume the model requires these to be present in the composition.
            # If the task implies the column 'Ni' etc exists separately, we'd check that.
            # But here we have a dict. So if 'Ni' key is missing, it's 0.
            # The instruction says "Halt... if missing".
            # We will check if the key exists and value > 0.
            has_ni = comp_lower.get('ni', 0) > 0
            has_cr = comp_lower.get('cr', 0) > 0
            has_al = comp_lower.get('al', 0) > 0
            
            if not (has_ni and has_cr and has_al):
                logger.error(f"Row {idx} missing required elements (Ni, Cr, Al). Halting.")
                return False
                
        # Check for unknown elements
        unknown_elements = []
        for elem in comp.keys():
            elem_lower = elem.strip().lower()
            found = False
            for key in PERIODIC_DATA:
                if key.lower() == elem_lower:
                    found = True
                    break
            if not found:
                unknown_elements.append((elem, comp[elem]))
                
        if unknown_elements:
            for elem, weight in unknown_elements:
                if weight > 0.5:
                    logger.error(f"Row {idx}: Unknown element '{elem}' with {weight}% > 0.5%. Excluding sample.")
                    # Mark for exclusion (we will filter later)
                    # For now, we just log. The filtering logic might be in the caller or we drop here.
                    # The task says "flag and exclude". We'll return False to halt or drop?
                    # "Halt execution immediately... if *any* required predictor... is missing"
                    # "If an unknown element is present: if > 0.5 wt%, flag and exclude"
                    # This implies we don't halt the whole run, but exclude the row.
                    # But the "Halt" applies to the required predictors.
                    # So we continue but mark this row.
                    # To implement "exclude", we can set a flag or drop later.
                    # Let's drop the row immediately to simplify.
                    # But we need to return True to continue processing other rows?
                    # The task says "Halt execution immediately" ONLY for required predictors.
                    # For unknown > 0.5, "flag and exclude".
                    # We will drop the row.
                    pass # Logic handled in process_data by filtering
                else:
                    logger.warning(f"Row {idx}: Unknown element '{elem}' with {weight}% <= 0.5%. Imputing.")
                    
    return True

def downsample_dataset(df: pd.DataFrame, logger: logging.Logger, mode: str) -> pd.DataFrame:
    """
    Downsample dataset based on mode and size.
    
    Logic:
    - If mode=ci and rows > 500, downsample to 500.
    - If mode=local and rows > 1000, downsample to 1000.
    """
    n = len(df)
    target = None
    
    if mode == 'ci' and n > 500:
        target = 500
    elif mode == 'local' and n > 1000:
        target = 1000
        
    if target and n > target:
        logger.info(f"Downsampling dataset from {n} to {target} rows (mode={mode}).")
        # Use random sampling with fixed seed for reproducibility
        return df.sample(n=target, random_state=42).reset_index(drop=True)
        
    return df

def process_data(input_path: str, output_path: str) -> None:
    """
    Main processing pipeline:
    1. Load data
    2. Validate
    3. Downsample
    4. Calculate descriptors
    5. Save output
    """
    config = get_config_from_args()
    logger = get_logger(__name__)
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
        
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Convert string representation of dict to actual dict if necessary
    # Assuming the fetcher loads it correctly, but just in case
    if 'elemental_composition' in df.columns:
        # If it's a string, we might need to eval or parse. 
        # Assuming it's already a dict or JSON string.
        # If it's a string like "{'Ni': 70, ...}", we need to parse.
        # For safety, let's check type.
        if isinstance(df['elemental_composition'].iloc[0], str):
            import ast
            def safe_eval(s):
                try:
                    return ast.literal_eval(s)
                except:
                    return {}
            df['elemental_composition'] = df['elemental_composition'].apply(safe_eval)
    
    # Validate
    if not validate_data(df, logger):
        log_data_validation_failure(logger, "Data validation failed")
        sys.exit(1) # Exit with error code
        
    # Downsample
    df = downsample_dataset(df, logger, config.mode)
    
    # Calculate descriptors
    df = calculate_thermodynamic_descriptors(df, logger)
    
    # Filter out rows with unknown elements > 0.5% (if any were not caught in validation)
    # Re-scan for unknowns > 0.5% and drop
    def has_large_unknown(composition):
        for elem, weight in composition.items():
            elem_lower = elem.strip().lower()
            found = False
            for key in PERIODIC_DATA:
                if key.lower() == elem_lower:
                    found = True
                    break
            if not found and weight > 0.5:
                return True
        return False
        
    mask = df['elemental_composition'].apply(lambda x: not has_large_unknown(x))
    dropped_count = len(df) - mask.sum()
    if dropped_count > 0:
        logger.warning(f"Dropped {dropped_count} rows with unknown elements > 0.5%.")
        df = df[mask].reset_index(drop=True)
    
    logger.info(f"Saving processed data to {output_path}")
    df.to_csv(output_path, index=False)
    logger.info("Processing complete.")

def main():
    """Entry point for processor script."""
    import argparse
    parser = argparse.ArgumentParser(description="Process alloy data.")
    parser.add_argument("--input", type=str, required=True, help="Input CSV path")
    parser.add_argument("--output", type=str, required=True, help="Output CSV path")
    args = parser.parse_args()
    
    process_data(args.input, args.output)

if __name__ == "__main__":
    main()