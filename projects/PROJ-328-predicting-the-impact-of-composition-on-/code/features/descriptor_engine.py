"""
DescriptorEngine: Computes physical and chemical descriptors for solder alloys.
Uses raw elemental percentages as weights for weighted means of physical properties.
"""
import numpy as np
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from features.transformer import CLRTransformer
from mendeleev import element
from utils.logging_config import get_logger
from seed import set_seed

logger = get_logger(__name__)

class DescriptorEngine:
    """
    Engine for computing compositional descriptors from solder alloy data.
    """

    # Standard elemental properties available via mendeleev
    # We cache these to avoid repeated lookups
    _ELEMENT_PROPERTIES = {
        'atomic_mass': 'atomic_mass',
        'electronegativity': 'en',
        'atomic_radius': 'covalent_radius',
        'melting_point': 'melting_point',
        'valence_electrons': 'valence_electrons'
    }

    def __init__(self):
        """
        Initialize the Descriptor Engine.
        """
        logger.info("DescriptorEngine initialized")
        self._property_cache: Dict[str, Dict[str, float]] = {}
        self._load_element_properties()

    def _load_element_properties(self):
        """
        Pre-load elemental properties for known elements to speed up computation.
        """
        # Common solder elements
        common_elements = ['Sn', 'Pb', 'Ag', 'Cu', 'Bi', 'Sb', 'In', 'Zn', 'Ni', 'Au']
        
        for symbol in common_elements:
            try:
                el = element(symbol)
                self._property_cache[symbol] = {
                    'atomic_mass': el.atomic_mass,
                    'electronegativity': el.en,
                    'atomic_radius': el.covalent_radius,
                    'melting_point': el.melting_point,
                    'valence_electrons': el.valence_electrons
                }
            except Exception as e:
                logger.warning(f"Could not load properties for element {symbol}: {e}")

    def _get_element_property(self, symbol: str, property_name: str) -> Optional[float]:
        """
        Get a specific property for an element, with fallback to mendeleev.
        """
        # Check cache first
        if symbol in self._property_cache:
            if property_name in self._property_cache[symbol]:
                return self._property_cache[symbol][property_name]
        
        # Fallback to direct lookup
        try:
            el = element(symbol)
            if property_name == 'atomic_mass':
                return el.atomic_mass
            elif property_name == 'electronegativity':
                return el.en
            elif property_name == 'atomic_radius':
                return el.covalent_radius
            elif property_name == 'melting_point':
                return el.melting_point
            elif property_name == 'valence_electrons':
                return el.valence_electrons
        except Exception as e:
            logger.warning(f"Could not retrieve {property_name} for {symbol}: {e}")
        
        return None

    def compute_weighted_mean(self, composition: Dict[str, float], property_name: str) -> float:
        """
        Compute weighted mean of a property using raw elemental percentages.

        Args:
            composition: Dict mapping element symbols to their percentage (0-100 or 0-1).
            property_name: Name of the property to compute.

        Returns:
            Weighted mean value.
        """
        total_weight = 0.0
        weighted_sum = 0.0

        for symbol, weight in composition.items():
            prop_value = self._get_element_property(symbol, property_name)
            if prop_value is not None:
                weighted_sum += weight * prop_value
                total_weight += weight
            else:
                logger.warning(f"Missing property {property_name} for element {symbol}")

        if total_weight == 0:
            return 0.0

        return weighted_sum / total_weight

    def compute_variance(self, composition: Dict[str, float], property_name: str) -> float:
        """
        Compute weighted variance of a property.

        Args:
            composition: Dict mapping element symbols to their percentage.
            property_name: Name of the property.

        Returns:
            Weighted variance.
        """
        mean_val = self.compute_weighted_mean(composition, property_name)
        total_weight = 0.0
        weighted_sq_diff_sum = 0.0

        for symbol, weight in composition.items():
            prop_value = self._get_element_property(symbol, property_name)
            if prop_value is not None:
                diff = prop_value - mean_val
                weighted_sq_diff_sum += weight * (diff ** 2)
                total_weight += weight

        if total_weight == 0:
            return 0.0

        return weighted_sq_diff_sum / total_weight

    def transform(self, df: pd.DataFrame, composition_cols: List[str]) -> pd.DataFrame:
        """
        Transform a dataframe by adding computed descriptors.

        Args:
            df: Input dataframe with composition columns.
            composition_cols: List of column names representing elemental percentages.

        Returns:
            DataFrame with added descriptor columns.
        """
        result = df.copy()
        descriptors = []

        logger.info(f"Computing descriptors for {len(df)} samples")

        for idx, row in df.iterrows():
            # Extract composition as dict
            composition = {col: row[col] for col in composition_cols if col in row.index and pd.notna(row[col])}
            
            if not composition:
                logger.warning(f"Row {idx} has no valid composition data")
                continue

            # Compute physical descriptors
            desc = {
                'weighted_mean_atomic_mass': self.compute_weighted_mean(composition, 'atomic_mass'),
                'electronegativity_variance': self.compute_variance(composition, 'electronegativity'),
                'atomic_radius_variance': self.compute_variance(composition, 'atomic_radius'),
                'weighted_mean_melting_point': self.compute_weighted_mean(composition, 'melting_point'),
                'weighted_mean_valence_electrons': self.compute_weighted_mean(composition, 'valence_electrons')
            }

            descriptors.append(desc)

        if descriptors:
          desc_df = pd.DataFrame(descriptors)
          # Ensure index alignment
          desc_df.index = df.index[:len(desc_df)]
          result = pd.concat([result, desc_df], axis=1)

        logger.info(f"Descriptor computation complete. Added {len(descriptors)} rows of descriptors.")
        return result

def main():
    """
    Main entry point for testing the DescriptorEngine.
    """
    logger.info("Starting DescriptorEngine test")
    set_seed(42)

    # Create sample data
    data = {
        'Sn': [63.0, 95.0, 50.0],
        'Ag': [2.5, 0.0, 10.0],
        'Cu': [0.5, 0.0, 5.0],
        'Pb': [34.0, 5.0, 35.0]
    }
    df = pd.DataFrame(data)

    engine = DescriptorEngine()
    composition_cols = ['Sn', 'Ag', 'Cu', 'Pb']
    result = engine.transform(df, composition_cols)

    logger.info("Original data:")
    logger.info(result[composition_cols].head())
    logger.info("Computed descriptors:")
    desc_cols = [c for c in result.columns if c not in composition_cols]
    logger.info(result[desc_cols].head())

    logger.info("DescriptorEngine test completed successfully")

if __name__ == "__main__":
    main()
