import numpy as np
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import json

from mendeleev import element
from compositional import clr
from utils.logging_config import get_logger
from config import get_data_processed_dir, get_composition_sum_threshold
from utils.error_handlers import DataValidationError

logger = get_logger(__name__)

class DescriptorEngine:
    """
    Computes physical descriptors from solder alloy compositions.

    Methodology:
    1. Load raw elemental composition percentages (which sum to 1.0).
    2. Apply CLR transform to raw percentages for model input features (to handle closure).
    3. Compute physical descriptors using RAW elemental percentages as weights.
       Formula: Descriptor = sum(raw_percent_i * property_i)
       CLR values are NOT used as weights for physical descriptors.
    """

    def __init__(self):
        self.logger = get_logger(__name__)
        self.property_cache: Dict[str, Dict[str, float]] = {}
        self._load_elemental_properties()

    def _load_elemental_properties(self) -> None:
        """
        Pre-load elemental properties from mendeleev to avoid repeated DB calls.
        Properties: atomic_mass, electronegativity, atomic_radius, melting_point, valence_electrons
        """
        properties_to_fetch = [
            'atomic_mass', 
            'electronegativity', 
            'atomic_radius', 
            'melting_point', 
            'valence_electrons'
        ]
        
        # Mendeleev element symbols we might encounter
        # We'll fetch on demand to keep cache small initially, 
        # but pre-populate common solder elements
        common_elements = ['Sn', 'Pb', 'Ag', 'Cu', 'Bi', 'In', 'Sb', 'Zn', 'Al', 'Ni']
        
        for symbol in common_elements:
            try:
                el = element(symbol)
                self.property_cache[symbol] = {
                    'atomic_mass': float(el.atomic_mass) if el.atomic_mass is not None else 0.0,
                    'electronegativity': float(el.electronegativity) if el.electronegativity is not None else 0.0,
                    'atomic_radius': float(el.atomic_radius) if el.atomic_radius is not None else 0.0,
                    'melting_point': float(el.melting_point) if el.melting_point is not None else 0.0,
                    'valence_electrons': float(el.valence_electrons) if el.valence_electrons is not None else 0.0
                }
            except Exception as e:
                self.logger.warning(f"Could not fetch properties for element {symbol}: {e}")
                self.property_cache[symbol] = {
                    'atomic_mass': 0.0,
                    'electronegativity': 0.0,
                    'atomic_radius': 0.0,
                    'melting_point': 0.0,
                    'valence_electrons': 0.0
                }

    def _get_element_property(self, symbol: str, property_name: str) -> float:
        """
        Get a specific property for an element, fetching from mendeleev if not cached.
        """
        symbol = symbol.upper()
        
        if symbol not in self.property_cache:
            try:
                el = element(symbol)
                self.property_cache[symbol] = {
                    'atomic_mass': float(el.atomic_mass) if el.atomic_mass is not None else 0.0,
                    'electronegativity': float(el.electronegativity) if el.electronegativity is not None else 0.0,
                    'atomic_radius': float(el.atomic_radius) if el.atomic_radius is not None else 0.0,
                    'melting_point': float(el.melting_point) if el.melting_point is not None else 0.0,
                    'valence_electrons': float(el.valence_electrons) if el.valence_electrons is not None else 0.0
                }
            except Exception as e:
                self.logger.warning(f"Could not fetch properties for element {symbol}: {e}")
                self.property_cache[symbol] = {
                    'atomic_mass': 0.0,
                    'electronegativity': 0.0,
                    'atomic_radius': 0.0,
                    'melting_point': 0.0,
                    'valence_electrons': 0.0
                }
        
        return self.property_cache[symbol].get(property_name, 0.0)

    def _apply_clr_transform(self, composition: Dict[str, float]) -> Dict[str, float]:
        """
        Apply CLR (Centered Log-Ratio) transform to raw composition.
        
        Args:
            composition: Dict of element -> percentage (should sum to ~1.0 or 100)
        
        Returns:
            Dict of element -> CLR transformed value
        """
        # Ensure we have a vector of values
        elements = list(composition.keys())
        values = np.array([composition[e] for e in elements], dtype=float)
        
        # Handle zero values by replacing with small epsilon (standard CLR practice)
        epsilon = 1e-10
        values = np.where(values == 0, epsilon, values)
        
        # Apply CLR transform
        try:
            clr_values = clr(values)
            return dict(zip(elements, clr_values))
        except Exception as e:
            self.logger.error(f"CLR transform failed: {e}")
            raise

    def _compute_weighted_mean(self, composition: Dict[str, float], property_name: str) -> float:
        """
        Compute weighted mean of a property using RAW percentages as weights.
        
        Formula: sum(raw_percent_i * property_i)
        
        Args:
            composition: Dict of element -> percentage (RAW, not CLR)
            property_name: Name of property to compute weighted mean for
        
        Returns:
            Weighted mean value
        """
        total = 0.0
        sum_weights = 0.0
        
        for symbol, weight in composition.items():
            prop_value = self._get_element_property(symbol, property_name)
            total += weight * prop_value
            sum_weights += weight
        
        if sum_weights == 0:
            return 0.0
        
        return total / sum_weights

    def _compute_weighted_variance(self, composition: Dict[str, float], property_name: str) -> float:
        """
        Compute weighted variance of a property using RAW percentages as weights.
        
        Formula: sum(w_i * (x_i - mean)^2) / sum(w_i)
        
        Args:
            composition: Dict of element -> percentage (RAW, not CLR)
            property_name: Name of property to compute weighted variance for
        
        Returns:
            Weighted variance value
        """
        # First compute weighted mean
        mean = self._compute_weighted_mean(composition, property_name)
        
        total_variance = 0.0
        sum_weights = 0.0
        
        for symbol, weight in composition.items():
            prop_value = self._get_element_property(symbol, property_name)
            diff = prop_value - mean
            total_variance += weight * (diff ** 2)
            sum_weights += weight
        
        if sum_weights == 0:
            return 0.0
        
        return total_variance / sum_weights

    def compute_descriptors(self, composition: Dict[str, float]) -> Dict[str, float]:
        """
        Compute all physical descriptors for a given composition.
        
        Args:
            composition: Dict of element -> percentage (RAW values, should sum to ~1.0 or 100)
        
        Returns:
            Dict of descriptor name -> computed value
        """
        # Validate composition sum
        comp_sum = sum(composition.values())
        threshold = get_composition_sum_threshold()
        
        if comp_sum < threshold:
            raise DataValidationError(
                f"Composition sum {comp_sum} is below threshold {threshold}. "
                "Cannot compute descriptors for invalid composition."
            )
        
        # Normalize to 1.0 if sum is close to 100 (percentage format)
        if comp_sum > 1.1:
            composition = {k: v / comp_sum for k, v in composition.items()}
        
        descriptors = {}
        
        # 1. Weighted Mean Atomic Mass (using RAW percentages)
        descriptors['weighted_mean_atomic_mass'] = self._compute_weighted_mean(
            composition, 'atomic_mass'
        )
        
        # 2. Electronegativity Variance (using RAW percentages)
        descriptors['electronegativity_variance'] = self._compute_weighted_variance(
            composition, 'electronegativity'
        )
        
        # 3. Atomic Radius Variance (using RAW percentages)
        descriptors['atomic_radius_variance'] = self._compute_weighted_variance(
            composition, 'atomic_radius'
        )
        
        # 4. Weighted Average Melting Point (using RAW percentages)
        descriptors['weighted_avg_melting_point'] = self._compute_weighted_mean(
            composition, 'melting_point'
        )
        
        # 5. Valence Electron Concentration (using RAW percentages)
        descriptors['valence_electron_concentration'] = self._compute_weighted_mean(
            composition, 'valence_electrons'
        )
        
        return descriptors

    def transform_dataframe(self, df: pd.DataFrame, composition_cols: List[str]) -> pd.DataFrame:
        """
        Transform a dataframe of compositions into a feature matrix.
        
        Args:
            df: Input dataframe with composition columns
            composition_cols: List of column names representing elemental percentages
        
        Returns:
            DataFrame with CLR-transformed composition features and physical descriptors
        """
        # Create a copy to avoid modifying original
        result_df = df.copy()
        
        # Apply CLR transform to composition columns
        clr_features = {}
        for idx, row in df.iterrows():
            composition = {col: row[col] for col in composition_cols}
            clr_transformed = self._apply_clr_transform(composition)
            for elem, value in clr_transformed.items():
                col_name = f"clr_{elem}"
                if col_name not in clr_features:
                    clr_features[col_name] = []
                clr_features[col_name].append(value)
        
        # Add CLR features to result
        for col_name, values in clr_features.items():
            result_df[col_name] = values
        
        # Compute physical descriptors using RAW percentages
        descriptors = {
            'weighted_mean_atomic_mass': [],
            'electronegativity_variance': [],
            'atomic_radius_variance': [],
            'weighted_avg_melting_point': [],
            'valence_electron_concentration': []
        }
        
        for idx, row in df.iterrows():
            composition = {col: row[col] for col in composition_cols}
            desc_values = self.compute_descriptors(composition)
            for desc_name, value in desc_values.items():
                descriptors[desc_name].append(value)
        
        # Add descriptor features to result
        for desc_name, values in descriptors.items():
            result_df[desc_name] = values
        
        return result_df

    def main(self):
        """
        Main entry point for descriptor engine.
        Reads cleaned data, computes descriptors, and saves output.
        """
        logger.info("Starting Descriptor Engine")
        
        # Load cleaned data
        cleaned_path = get_data_processed_dir() / "solder_hardness_cleaned.csv"
        if not cleaned_path.exists():
            logger.error(f"Cleaned data not found at {cleaned_path}")
            return
        
        df = pd.read_csv(cleaned_path)
        logger.info(f"Loaded {len(df)} records from {cleaned_path}")
        
        # Identify composition columns (assuming they start with 'element_' or are known elements)
        # Common approach: look for columns that are elements
        known_elements = ['Sn', 'Pb', 'Ag', 'Cu', 'Bi', 'In', 'Sb', 'Zn', 'Al', 'Ni', 'Fe', 'Mn', 'Cr', 'Co', 'Mo', 'W', 'Ti', 'V', 'Nb', 'Ta', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Pd', 'Rh', 'Ru', 'Ce', 'La', 'Nd', 'Pr', 'Sm', 'Gd', 'Dy', 'Ho', 'Er', 'Tm', 'Yb', 'Lu', 'Sc', 'Y', 'Zr', 'Hf', 'Be', 'Mg', 'Ca', 'Sr', 'Ba', 'Li', 'Na', 'K', 'Rb', 'Cs', 'Fr', 'He', 'Ne', 'Ar', 'Kr', 'Xe', 'Rn']
        
        composition_cols = [col for col in df.columns if col.upper() in known_elements or col.startswith('element_')]
        
        if not composition_cols:
            logger.error("No composition columns found in dataframe")
            return
        
        logger.info(f"Found composition columns: {composition_cols}")
        
        # Transform dataframe
        try:
            transformed_df = self.transform_dataframe(df, composition_cols)
            logger.info(f"Transformed dataframe with {len(transformed_df.columns)} columns")
        except Exception as e:
            logger.error(f"Transformation failed: {e}")
            return
        
        # Save output
        output_path = get_data_processed_dir() / "solder_hardness_features.csv"
        transformed_df.to_csv(output_path, index=False)
        logger.info(f"Saved feature matrix to {output_path}")
        
        # Log summary
        logger.info(f"Descriptor computation complete. Output: {output_path}")
        logger.info(f"Features computed: {list(transformed_df.columns)}")

def main():
    """Main entry point"""
    engine = DescriptorEngine()
    engine.main()

if __name__ == "__main__":
    main()