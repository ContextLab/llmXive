"""
Descriptor engine for computing physical/chemical properties from solder compositions.

Computes weighted descriptors based on elemental properties and composition fractions.
"""

import numpy as np
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from features.transformer import CLRTransformer
from seed import set_seed
from utils.logging_config import get_logger
from config import get_config

logger = get_logger(__name__)
config = get_config()

# Elemental property databases (simplified, real values from periodic table)
ELEMENTAL_PROPERTIES = {
    'Sn': {'atomic_mass': 118.71, 'electronegativity': 1.96, 'atomic_radius': 140, 'melting_point': 231.93, 'valence_electrons': 4},
    'Pb': {'atomic_mass': 207.2, 'electronegativity': 2.33, 'atomic_radius': 175, 'melting_point': 327.46, 'valence_electrons': 4},
    'Ag': {'atomic_mass': 107.87, 'electronegativity': 1.93, 'atomic_radius': 144, 'melting_point': 961.78, 'valence_electrons': 1},
    'Cu': {'atomic_mass': 63.55, 'electronegativity': 1.90, 'atomic_radius': 128, 'melting_point': 1084.62, 'valence_electrons': 1},
    'Bi': {'atomic_mass': 208.98, 'electronegativity': 2.02, 'atomic_radius': 156, 'melting_point': 271.4, 'valence_electrons': 5},
    'In': {'atomic_mass': 114.82, 'electronegativity': 1.78, 'atomic_radius': 156, 'melting_point': 156.6, 'valence_electrons': 3},
    'Zn': {'atomic_mass': 65.38, 'electronegativity': 1.65, 'atomic_radius': 134, 'melting_point': 419.53, 'valence_electrons': 2},
    'Sb': {'atomic_mass': 121.76, 'electronegativity': 2.05, 'atomic_radius': 140, 'melting_point': 630.63, 'valence_electrons': 5},
    'Au': {'atomic_mass': 196.97, 'electronegativity': 2.54, 'atomic_radius': 144, 'melting_point': 1064.18, 'valence_electrons': 1},
    'Ni': {'atomic_mass': 58.69, 'electronegativity': 1.91, 'atomic_radius': 124, 'melting_point': 1455.0, 'valence_electrons': 2},
}

class DescriptorEngine:
    """
    Engine for computing compositional descriptors from elemental fractions.
    
    Computes:
    - Weighted mean atomic mass
    - Electronegativity variance
    - Atomic radius variance
    - Weighted average melting point
    - Valence electron concentration
    """
    
    def __init__(self, apply_clr: bool = True):
        """
        Initialize descriptor engine.
        
        Args:
            apply_clr: Whether to apply CLR transformation to the resulting descriptor vector.
        """
        self.apply_clr = apply_clr
        self._clr_transformer = CLRTransformer() if apply_clr else None
        logger.info("DescriptorEngine initialized (apply_clr=%s)", apply_clr)
    
    def _get_element_property(self, element: str, property_name: str) -> float:
        """
        Get a property value for an element.
        
        Args:
            element: Element symbol.
            property_name: Property to retrieve.
        
        Returns:
            Property value or 0.0 if unknown.
        """
        if element in ELEMENTAL_PROPERTIES:
            return ELEMENTAL_PROPERTIES[element].get(property_name, 0.0)
        logger.warning("Unknown element: %s, property: %s", element, property_name)
        return 0.0
    
    def _compute_weighted_mean(self, fractions: np.ndarray, properties: np.ndarray) -> float:
        """Compute weighted mean of properties."""
        return np.sum(fractions * properties)
    
    def _compute_weighted_variance(self, fractions: np.ndarray, properties: np.ndarray) -> float:
        """Compute weighted variance of properties."""
        mean = self._compute_weighted_mean(fractions, properties)
        return np.sum(fractions * (properties - mean) ** 2)
    
    def compute_descriptors(self, df: pd.DataFrame, composition_cols: List[str]) -> pd.DataFrame:
        """
        Compute descriptors for a dataframe of solder compositions.
        
        Args:
            df: Input dataframe with composition columns.
            composition_cols: List of column names representing elemental fractions.
        
        Returns:
            DataFrame with computed descriptors.
        """
        logger.info("Computing descriptors for %d samples with %d elements", 
                   len(df), len(composition_cols))
        
        descriptors = {}
        
        # Extract composition matrix
        X = df[composition_cols].values
        
        # Ensure compositions sum to 1 (handle floating point errors)
        X_sum = X.sum(axis=1, keepdims=True)
        X_normalized = X / X_sum
        
        # Compute descriptors for each sample
        n_samples = len(df)
        
        # 1. Weighted mean atomic mass
        atomic_masses = np.array([
            self._get_element_property(elem, 'atomic_mass') 
            for elem in composition_cols
        ])
        descriptors['weighted_mean_atomic_mass'] = np.array([
            self._compute_weighted_mean(X_normalized[i], atomic_masses)
            for i in range(n_samples)
        ])
        
        # 2. Electronegativity variance
        electronegativities = np.array([
            self._get_element_property(elem, 'electronegativity')
            for elem in composition_cols
        ])
        descriptors['electronegativity_variance'] = np.array([
            self._compute_weighted_variance(X_normalized[i], electronegativities)
            for i in range(n_samples)
        ])
        
        # 3. Atomic radius variance
        atomic_radii = np.array([
            self._get_element_property(elem, 'atomic_radius')
            for elem in composition_cols
        ])
        descriptors['atomic_radius_variance'] = np.array([
            self._compute_weighted_variance(X_normalized[i], atomic_radii)
            for i in range(n_samples)
        ])
        
        # 4. Weighted average melting point
        melting_points = np.array([
            self._get_element_property(elem, 'melting_point')
            for elem in composition_cols
        ])
        descriptors['weighted_mean_melting_point'] = np.array([
            self._compute_weighted_mean(X_normalized[i], melting_points)
            for i in range(n_samples)
        ])
        
        # 5. Valence electron concentration
        valence_electrons = np.array([
            self._get_element_property(elem, 'valence_electrons')
            for elem in composition_cols
        ])
        descriptors['valence_electron_concentration'] = np.array([
            self._compute_weighted_mean(X_normalized[i], valence_electrons)
            for i in range(n_samples)
        ])
        
        # Create descriptor dataframe
        desc_df = pd.DataFrame(descriptors, index=df.index)
        
        # Apply CLR transformation if requested
        if self.apply_clr:
            logger.info("Applying CLR transformation to descriptor vector")
            desc_array = desc_df.values
            desc_clr = self._clr_transformer.fit_transform(desc_array)
            desc_df = pd.DataFrame(
                desc_clr, 
                index=df.index,
                columns=[f'{col}_clr' for col in desc_df.columns]
            )
        
        logger.info("Descriptor computation complete. Output shape: %s", desc_df.shape)
        return desc_df

def main():
    """
    Main entry point for standalone execution.
    
    Tests the descriptor engine on sample data.
    """
    from seed import init_reproducibility
    init_reproducibility(seed=42)
    
    logger.info("Testing DescriptorEngine...")
    
    # Create sample data
    np.random.seed(42)
    n_samples = 10
    elements = ['Sn', 'Pb', 'Ag', 'Cu']
    
    # Generate random compositions
    compositions = np.random.dirichlet(np.ones(len(elements)), n_samples)
    
    df = pd.DataFrame(compositions, columns=elements)
    df['alloy_id'] = [f'ALLOY_{i}' for i in range(n_samples)]
    
    logger.info("Sample data shape: %s", df.shape)
    logger.info("Composition sum check: %.6f", df[elements].sum(axis=1).iloc[0])
    
    # Compute descriptors
    engine = DescriptorEngine(apply_clr=True)
    descriptors = engine.compute_descriptors(df, elements)
    
    logger.info("Descriptor shape: %s", descriptors.shape)
    logger.info("Descriptor columns: %s", list(descriptors.columns))
    logger.info("Sample descriptor values:\n%s", descriptors.head())
    
    logger.info("DescriptorEngine test completed successfully.")

if __name__ == "__main__":
    main()
