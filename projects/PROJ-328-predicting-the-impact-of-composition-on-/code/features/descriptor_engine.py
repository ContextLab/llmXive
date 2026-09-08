"""
Descriptor Engine for Solder Alloy Hardness Prediction.

This module computes physical descriptors from raw elemental compositions
and applies CLR transforms to handle the compositional nature of the data.

Descriptors computed:
  1. Weighted Mean Atomic Mass
  2. Electronegativity Variance
  3. Atomic Radius Variance
  4. Weighted Average Melting Point
  5. Valence Electron Concentration (VEC)
"""

import numpy as np
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import json

from mendeleev import element
from mendeleev.models import Element

from features.transformer import CLRTransformer
from utils.logging_config import get_logger
from utils.error_handlers import DataValidationError, ConfigurationError

logger = get_logger(__name__)


# Standard elemental properties mapping (fallback if mendeleev fails or for speed)
# Keys: Element Symbol (str), Values: dict of properties
# These are standard values at room temperature.
_ELEMENT_PROPERTIES = {
    'Sn': {'atomic_mass': 118.71, 'electronegativity': 1.96, 'atomic_radius': 145.0, 'melting_point': 505.08, 'valence_electrons': 4},
    'Pb': {'atomic_mass': 207.2, 'electronegativity': 2.33, 'atomic_radius': 175.0, 'melting_point': 600.61, 'valence_electrons': 4},
    'Ag': {'atomic_mass': 107.87, 'electronegativity': 1.93, 'atomic_radius': 165.0, 'melting_point': 1234.93, 'valence_electrons': 1},
    'Cu': {'atomic_mass': 63.55, 'electronegativity': 1.90, 'atomic_radius': 128.0, 'melting_point': 1357.77, 'valence_electrons': 1},
    'Bi': {'atomic_mass': 208.98, 'electronegativity': 2.02, 'atomic_radius': 156.0, 'melting_point': 544.75, 'valence_electrons': 5},
    'In': {'atomic_mass': 114.82, 'electronegativity': 1.78, 'atomic_radius': 156.0, 'melting_point': 429.75, 'valence_electrons': 3},
    'Zn': {'atomic_mass': 65.38, 'electronegativity': 1.65, 'atomic_radius': 134.0, 'melting_point': 692.68, 'valence_electrons': 2},
    'Au': {'atomic_mass': 196.97, 'electronegativity': 2.54, 'atomic_radius': 144.0, 'melting_point': 1337.33, 'valence_electrons': 1},
    'Ni': {'atomic_mass': 58.69, 'electronegativity': 1.91, 'atomic_radius': 124.0, 'melting_point': 1728.0, 'valence_electrons': 2},
    'Sb': {'atomic_mass': 121.76, 'electronegativity': 2.05, 'atomic_radius': 145.0, 'melting_point': 903.78, 'valence_electrons': 5},
    'Co': {'atomic_mass': 58.93, 'electronegativity': 1.88, 'atomic_radius': 125.0, 'melting_point': 1768.0, 'valence_electrons': 2},
    'Fe': {'atomic_mass': 55.85, 'electronegativity': 1.83, 'atomic_radius': 126.0, 'melting_point': 1811.0, 'valence_electrons': 2},
    'Mn': {'atomic_mass': 54.94, 'electronegativity': 1.55, 'atomic_radius': 127.0, 'melting_point': 1519.0, 'valence_electrons': 2},
    'Cr': {'atomic_mass': 52.00, 'electronegativity': 1.66, 'atomic_radius': 128.0, 'melting_point': 2180.0, 'valence_electrons': 1},
    'Al': {'atomic_mass': 26.98, 'electronegativity': 1.61, 'atomic_radius': 143.0, 'melting_point': 933.47, 'valence_electrons': 3},
    'Mg': {'atomic_mass': 24.31, 'electronegativity': 1.31, 'atomic_radius': 160.0, 'melting_point': 923.0, 'valence_electrons': 2},
}


def _get_element_property(symbol: str, property_name: str, use_mendeleev: bool = True) -> float:
    """
    Retrieve a property for an element symbol.
    Priority:
      1. Mendeleev library (if available and requested)
      2. Local fallback dictionary
    """
    symbol = symbol.strip().upper()
    
    if use_mendeleev:
        try:
            el = element(symbol)
            if property_name == 'atomic_mass':
                return float(el.atomic_mass)
            elif property_name == 'electronegativity':
                # Mendeleev uses Pauling scale
                val = el.electronegativity
                return float(val) if val is not None else 0.0
            elif property_name == 'atomic_radius':
                # Mendeleev covalent radius in pm
                val = el.covalent_radius
                return float(val) if val is not None else 0.0
            elif property_name == 'melting_point':
                val = el.melting_point
                return float(val) if val is not None else 0.0
            elif property_name == 'valence_electrons':
                # Mendeleev valence electrons count
                val = el.valence_electrons
                return float(val) if val is not None else 0.0
        except Exception as e:
            logger.warning(f"Mendeleev lookup failed for {symbol}.{property_name}: {e}. Falling back to local table.")
    
    # Fallback to local table
    if symbol in _ELEMENT_PROPERTIES:
        if property_name in _ELEMENT_PROPERTIES[symbol]:
            return float(_ELEMENT_PROPERTIES[symbol][property_name])
    
    logger.error(f"Could not find property '{property_name}' for element '{symbol}' in any source.")
    raise DataValidationError(f"Missing property data for element: {symbol}")


class DescriptorEngine:
    """
    Computes physical descriptors and CLR features for solder alloys.
    
    Method:
      1. Load raw composition percentages (summing to ~100 or 1.0).
      2. Normalize to sum to 1.0.
      3. Compute Physical Descriptors using RAW percentages as weights.
      4. Compute CLR feature vector using normalized percentages.
      5. Combine into final feature matrix.
    """

    def __init__(self, use_mendeleev: bool = True):
        self.use_mendeleev = use_mendeleev
        self.clr_transformer = CLRTransformer()

    def _normalize_composition(self, composition: Dict[str, float]) -> Dict[str, float]:
        """Normalize composition values to sum to 1.0."""
        total = sum(composition.values())
        if total == 0:
            raise DataValidationError("Composition sum is zero.")
        if abs(total - 1.0) > 0.01 and abs(total - 100.0) > 0.01:
            # If it's close to 100, normalize by 100. If close to 1, normalize by sum.
            # If it's something else (e.g. 0.5), normalize by sum.
            pass 
        
        # Assume input is either % (sum ~100) or fraction (sum ~1)
        # We want output to be fraction (sum 1)
        if total > 10.0:
            # Likely percentages
            return {k: v / total for k, v in composition.items()}
        else:
            # Likely fractions, but ensure sum is 1.0
            return {k: v / total for k, v in composition.items()}

    def compute_descriptors(self, composition: Dict[str, float]) -> Dict[str, float]:
        """
        Compute physical descriptors from raw composition.
        
        Args:
            composition: Dict of {ElementSymbol: Percentage (e.g. 63.0, 37.0)}
        
        Returns:
            Dict of computed descriptors.
        """
        # Normalize to fractions for weighting
        normalized = self._normalize_composition(composition)
        
        descriptors = {}
        
        # 1. Weighted Mean Atomic Mass
        # Sum(w_i * M_i)
        weighted_mass = sum(
            w * _get_element_property(sym, 'atomic_mass', self.use_mendeleev)
            for sym, w in normalized.items()
        )
        descriptors['weighted_mean_atomic_mass'] = weighted_mass
        
        # 2. Electronegativity Variance
        # Var(X) = E[X^2] - (E[X])^2
        # E[X] = Sum(w_i * EN_i)
        # E[X^2] = Sum(w_i * EN_i^2)
        en_values = {sym: _get_element_property(sym, 'electronegativity', self.use_mendeleev) for sym in normalized}
        en_mean = sum(w * en for w, en in zip(normalized.values(), en_values.values()))
        en_sq_mean = sum(w * (en ** 2) for w, en in zip(normalized.values(), en_values.values()))
        descriptors['electronegativity_variance'] = en_sq_mean - (en_mean ** 2)
        
        # 3. Atomic Radius Variance
        # Same logic as electronegativity
        rad_values = {sym: _get_element_property(sym, 'atomic_radius', self.use_mendeleev) for sym in normalized}
        rad_mean = sum(w * r for w, r in zip(normalized.values(), rad_values.values()))
        rad_sq_mean = sum(w * (r ** 2) for w, r in zip(normalized.values(), rad_values.values()))
        descriptors['atomic_radius_variance'] = rad_sq_mean - (rad_mean ** 2)
        
        # 4. Weighted Average Melting Point
        mp_values = {sym: _get_element_property(sym, 'melting_point', self.use_mendeleev) for sym in normalized}
        weighted_mp = sum(w * mp for w, mp in zip(normalized.values(), mp_values.values()))
        descriptors['weighted_avg_melting_point'] = weighted_mp
        
        # 5. Valence Electron Concentration (VEC)
        # Sum(w_i * V_i)
        vec_values = {sym: _get_element_property(sym, 'valence_electrons', self.use_mendeleev) for sym in normalized}
        weighted_vec = sum(w * v for w, v in zip(normalized.values(), vec_values.values()))
        descriptors['valence_electron_concentration'] = weighted_vec
        
        return descriptors

    def compute_clr_features(self, composition: Dict[str, float]) -> np.ndarray:
        """
        Compute CLR-transformed feature vector from composition.
        
        Args:
            composition: Dict of {ElementSymbol: Percentage}
        
        Returns:
            np.ndarray of CLR-transformed values.
        """
        # Normalize to sum to 1.0
        normalized = self._normalize_composition(composition)
        
        # Sort keys to ensure consistent ordering
        sorted_symbols = sorted(normalized.keys())
        values = np.array([normalized[s] for s in sorted_symbols])
        
        # Apply CLR transform
        # CLR(x)_i = ln(x_i / g(x)) where g(x) is geometric mean
        clr_features = self.clr_transformer.transform(values)
        
        # Return as a dictionary with keys for the CLR features
        # e.g. {'clr_Sn': val, 'clr_Pb': val, ...}
        clr_dict = {f'clr_{sym}': val for sym, val in zip(sorted_symbols, clr_features)}
        
        return clr_dict, sorted_symbols

    def transform_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform a single row of data.
        
        Args:
            row: Dict containing 'elemental_breakdown' (dict) and other fields.
        
        Returns:
            Dict containing physical descriptors and CLR features.
        """
        if 'elemental_breakdown' not in row:
            raise DataValidationError("Row missing 'elemental_breakdown'")
        
        composition = row['elemental_breakdown']
        
        # Compute physical descriptors using RAW composition (normalized to sum=1)
        descriptors = self.compute_descriptors(composition)
        
        # Compute CLR features
        clr_dict, sorted_symbols = self.compute_clr_features(composition)
        
        # Merge into result
        result = {}
        result.update(descriptors)
        result.update(clr_dict)
        
        # Add metadata for debugging
        result['_sorted_elements'] = sorted_symbols
        
        return result

    def transform_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform a DataFrame of solder compositions.
        
        Args:
            df: DataFrame with 'elemental_breakdown' column (dicts) and 'hardness_hv'.
        
        Returns:
            DataFrame with added physical descriptors and CLR features.
        """
        logger.info(f"Transforming {len(df)} rows with DescriptorEngine...")
        
        results = []
        for idx, row in df.iterrows():
            try:
                transformed = self.transform_row(row)
                results.append(transformed)
            except Exception as e:
                logger.error(f"Error transforming row {idx}: {e}")
                raise
        
        result_df = pd.DataFrame(results)
        
        # Drop metadata column
        if '_sorted_elements' in result_df.columns:
            result_df = result_df.drop(columns=['_sorted_elements'])
        
        # Ensure original columns are preserved if needed (optional, usually we want features + target)
        # For model training, we usually separate X and y.
        # Here we return the full feature set.
        
        logger.info(f"Descriptor engineering complete. Output shape: {result_df.shape}")
        return result_df


def main():
    """
    Main entry point for testing the Descriptor Engine.
    Loads cleaned data, computes descriptors, and saves to processed data.
    """
    logger.info("Starting Descriptor Engine main execution...")
    
    # Load cleaned data
    input_path = Path("data/processed/solder_hardness_cleaned.csv")
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    
    # Initialize engine
    engine = DescriptorEngine(use_mendeleev=True)
    
    # Transform
    try:
        feature_df = engine.transform_dataframe(df)
    except Exception as e:
        logger.error(f"Transformation failed: {e}")
        raise
    
    # Save output
    output_path = Path("data/processed/solder_hardness_features.csv")
    feature_df.to_csv(output_path, index=False)
    logger.info(f"Saved features to {output_path}")
    
    # Verify output
    logger.info(f"Output columns: {list(feature_df.columns)}")
    logger.info(f"Output shape: {feature_df.shape}")
    
    return feature_df


if __name__ == "__main__":
    main()