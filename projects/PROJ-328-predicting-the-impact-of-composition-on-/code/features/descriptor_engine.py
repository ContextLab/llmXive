"""
Descriptor engineering for solder alloy compositions.

Computes weighted physical property descriptors from compositional data
using CLR-transformed coefficients as weights.
"""

import numpy as np
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import os

from .transformer import CLRTransformer
from config import get_data_processed_dir

logger = logging.getLogger(__name__)

class DescriptorEngine:
    """
    Engine for computing compositional descriptors from solder alloy data.
    
    This class calculates weighted mean atomic mass, electronegativity variance,
    atomic radius variance, weighted average melting point, and valence electron
    concentration using CLR-transformed composition coefficients as weights.
    
    Attributes:
        property_tables (dict): Dictionary mapping property names to DataFrames
                               containing elemental property values.
        elements (list): Ordered list of elements used in transformations.
    """
    
    # Standard elemental properties (periodic table data)
    # These are approximated values for common solder alloy elements
    ELEMENT_PROPERTIES = {
        'atomic_mass': {
            'Sn': 118.71, 'Pb': 207.2, 'Ag': 107.87, 'Cu': 63.55,
            'Bi': 208.98, 'In': 114.82, 'Sb': 121.76, 'Zn': 65.38,
            'Al': 26.98, 'Au': 196.97, 'Ni': 58.69, 'Fe': 55.85,
            'Mn': 54.94, 'Cr': 52.00, 'Co': 58.93, 'Ti': 47.87
        },
        'electronegativity': {
            'Sn': 1.96, 'Pb': 2.33, 'Ag': 1.93, 'Cu': 1.90,
            'Bi': 2.02, 'In': 1.78, 'Sb': 2.05, 'Zn': 1.65,
            'Al': 1.61, 'Au': 2.54, 'Ni': 1.91, 'Fe': 1.83,
            'Mn': 1.55, 'Cr': 1.66, 'Co': 1.88, 'Ti': 1.54
        },
        'atomic_radius': {
            'Sn': 140, 'Pb': 175, 'Ag': 144, 'Cu': 128,
            'Bi': 156, 'In': 166, 'Sb': 140, 'Zn': 134,
            'Al': 143, 'Au': 144, 'Ni': 124, 'Fe': 126,
            'Mn': 127, 'Cr': 128, 'Co': 125, 'Ti': 147
        },
        'melting_point': {
            'Sn': 231.93, 'Pb': 327.46, 'Ag': 961.78, 'Cu': 1084.62,
            'Bi': 271.3, 'In': 156.6, 'Sb': 630.63, 'Zn': 419.53,
            'Al': 660.32, 'Au': 1064.18, 'Ni': 1455, 'Fe': 1538,
            'Mn': 1246, 'Cr': 1907, 'Co': 1495, 'Ti': 1668
        },
        'valence_electrons': {
            'Sn': 4, 'Pb': 4, 'Ag': 1, 'Cu': 1,
            'Bi': 5, 'In': 3, 'Sb': 5, 'Zn': 2,
            'Al': 3, 'Au': 1, 'Ni': 2, 'Fe': 2,
            'Mn': 2, 'Cr': 1, 'Co': 2, 'Ti': 4
        }
    }
    
    def __init__(self, elements: Optional[List[str]] = None):
        """
        Initialize the DescriptorEngine.
        
        Args:
            elements: Optional list of element names. If provided, only these
                     elements will be used in descriptor computation.
        """
        self.elements = elements if elements else list(self.ELEMENT_PROPERTIES['atomic_mass'].keys())
        self.property_tables = {}
        self._build_property_tables()
        self.logger = logging.getLogger(__name__)
    
    def _build_property_tables(self) -> None:
        """Build DataFrames for each elemental property."""
        for prop_name, prop_dict in self.ELEMENT_PROPERTIES.items():
            df = pd.DataFrame({
                'element': list(prop_dict.keys()),
                prop_name: list(prop_dict.values())
            })
            self.property_tables[prop_name] = df
    
    def _get_property_values(self, property_name: str, elements: List[str]) -> np.ndarray:
        """
        Get property values for a list of elements.
        
        Args:
            property_name: Name of the property to retrieve.
            elements: List of element names.
        
        Returns:
            np.ndarray: Array of property values in the same order as elements.
        """
        if property_name not in self.property_tables:
            raise ValueError(f"Unknown property: {property_name}")
        
        df = self.property_tables[property_name]
        values = []
        for elem in elements:
            if elem in df['element'].values:
                values.append(df.loc[df['element'] == elem, property_name].values[0])
            else:
                # Default value or raise error
                self.logger.warning(f"Property {property_name} not found for element {elem}. Using 0.")
                values.append(0.0)
        
        return np.array(values)
    
    def compute_weighted_mean_atomic_mass(self, composition_df: pd.DataFrame) -> pd.Series:
        """
        Compute weighted mean atomic mass for each alloy.
        
        Uses CLR-transformed coefficients as weights.
        
        Args:
            composition_df: DataFrame with composition columns (element names).
        
        Returns:
            pd.Series: Weighted mean atomic mass for each sample.
        """
        elements = [col for col in composition_df.columns if col in self.elements]
        if not elements:
            raise ValueError("No valid element columns found in composition data")
        
        atomic_masses = self._get_property_values('atomic_mass', elements)
        
        # Apply CLR transformation to get weights
        X = composition_df[elements].values.astype(float)
        transformer = CLRTransformer(elements=elements)
        X_clr = transformer.fit_transform(X)
        
        # Use absolute values of CLR coefficients as weights (normalized)
        weights = np.abs(X_clr)
        weights = weights / weights.sum(axis=1, keepdims=True)
        
        # Compute weighted mean
        weighted_means = np.sum(weights * atomic_masses, axis=1)
        
        return pd.Series(weighted_means, index=composition_df.index, name='weighted_mean_atomic_mass')
    
    def compute_electronegativity_variance(self, composition_df: pd.DataFrame) -> pd.Series:
        """
        Compute electronegativity variance for each alloy.
        
        Uses CLR-transformed coefficients as weights for variance calculation.
        
        Args:
            composition_df: DataFrame with composition columns.
        
        Returns:
            pd.Series: Electronegativity variance for each sample.
        """
        elements = [col for col in composition_df.columns if col in self.elements]
        if not elements:
            raise ValueError("No valid element columns found")
        
        electronegativities = self._get_property_values('electronegativity', elements)
        
        X = composition_df[elements].values.astype(float)
        transformer = CLRTransformer(elements=elements)
        X_clr = transformer.fit_transform(X)
        
        weights = np.abs(X_clr)
        weights = weights / weights.sum(axis=1, keepdims=True)
        
        # Weighted variance
        weighted_means = np.sum(weights * electronegativities, axis=1)
        weighted_variances = np.sum(weights * (electronegativities - weighted_means[:, np.newaxis])**2, axis=1)
        
        return pd.Series(weighted_variances, index=composition_df.index, name='electronegativity_variance')
    
    def compute_atomic_radius_variance(self, composition_df: pd.DataFrame) -> pd.Series:
        """
        Compute atomic radius variance for each alloy.
        
        Args:
            composition_df: DataFrame with composition columns.
        
        Returns:
            pd.Series: Atomic radius variance for each sample.
        """
        elements = [col for col in composition_df.columns if col in self.elements]
        if not elements:
            raise ValueError("No valid element columns found")
        
        atomic_radii = self._get_property_values('atomic_radius', elements)
        
        X = composition_df[elements].values.astype(float)
        transformer = CLRTransformer(elements=elements)
        X_clr = transformer.fit_transform(X)
        
        weights = np.abs(X_clr)
        weights = weights / weights.sum(axis=1, keepdims=True)
        
        weighted_means = np.sum(weights * atomic_radii, axis=1)
        weighted_variances = np.sum(weights * (atomic_radii - weighted_means[:, np.newaxis])**2, axis=1)
        
        return pd.Series(weighted_variances, index=composition_df.index, name='atomic_radius_variance')
    
    def compute_weighted_melting_point(self, composition_df: pd.DataFrame) -> pd.Series:
        """
        Compute weighted average melting point for each alloy.
        
        Args:
            composition_df: DataFrame with composition columns.
        
        Returns:
            pd.Series: Weighted average melting point for each sample.
        """
        elements = [col for col in composition_df.columns if col in self.elements]
        if not elements:
            raise ValueError("No valid element columns found")
        
        melting_points = self._get_property_values('melting_point', elements)
        
        X = composition_df[elements].values.astype(float)
        transformer = CLRTransformer(elements=elements)
        X_clr = transformer.fit_transform(X)
        
        weights = np.abs(X_clr)
        weights = weights / weights.sum(axis=1, keepdims=True)
        
        weighted_means = np.sum(weights * melting_points, axis=1)
        
        return pd.Series(weighted_means, index=composition_df.index, name='weighted_melting_point')
    
    def compute_valence_electron_concentration(self, composition_df: pd.DataFrame) -> pd.Series:
        """
        Compute valence electron concentration for each alloy.
        
        Args:
            composition_df: DataFrame with composition columns.
        
        Returns:
            pd.Series: Valence electron concentration for each sample.
        """
        elements = [col for col in composition_df.columns if col in self.elements]
        if not elements:
            raise ValueError("No valid element columns found")
        
        valence_electrons = self._get_property_values('valence_electrons', elements)
        
        # For VEC, we use the actual composition (not CLR) as weights
        # since VEC is a linear combination
        compositions = composition_df[elements].values.astype(float)
        # Normalize compositions to sum to 1
        compositions = compositions / compositions.sum(axis=1, keepdims=True)
        
        vec = np.sum(compositions * valence_electrons, axis=1)
        
        return pd.Series(vec, index=composition_df.index, name='valence_electron_concentration')
    
    def compute_all_descriptors(self, composition_df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute all descriptors for the given composition data.
        
        Args:
            composition_df: DataFrame with composition columns.
        
        Returns:
            pd.DataFrame: DataFrame with all computed descriptors.
        """
        descriptors = pd.DataFrame(index=composition_df.index)
        
        try:
            descriptors['weighted_mean_atomic_mass'] = self.compute_weighted_mean_atomic_mass(composition_df)
        except Exception as e:
            self.logger.error(f"Failed to compute weighted_mean_atomic_mass: {e}")
        
        try:
            descriptors['electronegativity_variance'] = self.compute_electronegativity_variance(composition_df)
        except Exception as e:
            self.logger.error(f"Failed to compute electronegativity_variance: {e}")
        
        try:
            descriptors['atomic_radius_variance'] = self.compute_atomic_radius_variance(composition_df)
        except Exception as e:
            self.logger.error(f"Failed to compute atomic_radius_variance: {e}")
        
        try:
            descriptors['weighted_melting_point'] = self.compute_weighted_melting_point(composition_df)
        except Exception as e:
            self.logger.error(f"Failed to compute weighted_melting_point: {e}")
        
        try:
            descriptors['valence_electron_concentration'] = self.compute_valence_electron_concentration(composition_df)
        except Exception as e:
            self.logger.error(f"Failed to compute valence_electron_concentration: {e}")
        
        return descriptors
    
    def save_descriptors(self, composition_df: pd.DataFrame, output_path: Optional[str] = None) -> str:
        """
        Compute and save descriptors to a file.
        
        Args:
            composition_df: DataFrame with composition columns.
            output_path: Optional path to save the descriptors. If None, uses default.
        
        Returns:
            str: Path to the saved file.
        """
        if output_path is None:
            processed_dir = get_data_processed_dir()
            output_path = str(Path(processed_dir) / 'descriptors.csv')
        
        descriptors = self.compute_all_descriptors(composition_df)
        
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        descriptors.to_csv(output_path, index=False)
        self.logger.info(f"Descriptors saved to {output_path}")
        
        return output_path

def main():
    """
    Main function to demonstrate descriptor engineering.
    
    This function loads sample data, computes descriptors, and saves them.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Create a sample composition DataFrame for demonstration
    # In practice, this would be loaded from data/processed/solder_hardness_validated.csv
    sample_data = pd.DataFrame({
        'Sn': [0.63, 0.96, 0.50, 0.70],
        'Pb': [0.37, 0.04, 0.00, 0.00],
        'Ag': [0.00, 0.00, 0.50, 0.30],
        'Cu': [0.00, 0.00, 0.00, 0.00]
    })
    
    engine = DescriptorEngine(elements=['Sn', 'Pb', 'Ag', 'Cu'])
    descriptors = engine.compute_all_descriptors(sample_data)
    
    print("Computed Descriptors:")
    print(descriptors)
    
    # Save to file
    output_path = engine.save_descriptors(sample_data)
    print(f"\nDescriptors saved to: {output_path}")

if __name__ == "__main__":
    main()
