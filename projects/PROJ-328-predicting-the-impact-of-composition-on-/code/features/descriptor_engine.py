"""
Descriptor engineering for compositional data.

Calculates weighted atomic properties and derived descriptors
from compositional data using CLR coefficients.
"""
import numpy as np
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from features.transformer import CLRTransformer
from utils.logging_config import get_logger

logger = get_logger(__name__)


class DescriptorEngine:
    """
    Engine for computing compositional descriptors.

    This class calculates various atomic and electronic properties
    from compositional data, using CLR-transformed coefficients
    as weights for the original elemental properties.

    Descriptors computed:
    - Weighted mean atomic mass
    - Electronegativity variance
    - Atomic radius variance
    - Weighted average melting point
    - Valence electron concentration (VEC)
    """

    # Element property tables (simplified for demonstration)
    # In production, these would be loaded from external databases
    ELEMENT_PROPERTIES = {
        'atomic_mass': {
            'Sn': 118.71, 'Ag': 107.87, 'Cu': 63.55, 'In': 114.82,
            'Bi': 208.98, 'Sb': 121.76, 'Pb': 207.2, 'Zn': 65.38,
            'Ni': 58.69, 'Au': 196.97, 'Fe': 55.85, 'Co': 58.93,
            'Mn': 54.94, 'Cr': 52.00, 'Al': 26.98, 'Ga': 69.72,
            'Ge': 72.63, 'Ti': 47.87, 'Mo': 95.95, 'W': 183.84
        },
        'electronegativity': {
            'Sn': 1.96, 'Ag': 1.93, 'Cu': 1.90, 'In': 1.78,
            'Bi': 2.02, 'Sb': 2.05, 'Pb': 2.33, 'Zn': 1.65,
            'Ni': 1.91, 'Au': 2.54, 'Fe': 1.83, 'Co': 1.88,
            'Mn': 1.55, 'Cr': 1.66, 'Al': 1.61, 'Ga': 1.81,
            'Ge': 2.01, 'Ti': 1.54, 'Mo': 2.16, 'W': 2.36
        },
        'atomic_radius': {
            'Sn': 140, 'Ag': 144, 'Cu': 128, 'In': 166,
            'Bi': 156, 'Sb': 140, 'Pb': 175, 'Zn': 134,
            'Ni': 124, 'Au': 144, 'Fe': 126, 'Co': 125,
            'Mn': 127, 'Cr': 128, 'Al': 143, 'Ga': 135,
            'Ge': 122, 'Ti': 147, 'Mo': 139, 'W': 139
        },
        'melting_point': {
            'Sn': 231.93, 'Ag': 961.78, 'Cu': 1084.62, 'In': 156.60,
            'Bi': 271.40, 'Sb': 630.63, 'Pb': 327.46, 'Zn': 419.53,
            'Ni': 1455.00, 'Au': 1064.18, 'Fe': 1538.00, 'Co': 1495.00,
            'Mn': 1246.00, 'Cr': 1907.00, 'Al': 660.32, 'Ga': 29.76,
            'Ge': 938.25, 'Ti': 1668.00, 'Mo': 2623.00, 'W': 3422.00
        },
        'valence_electrons': {
            'Sn': 4, 'Ag': 1, 'Cu': 1, 'In': 3,
            'Bi': 5, 'Sb': 5, 'Pb': 4, 'Zn': 2,
            'Ni': 10, 'Au': 1, 'Fe': 8, 'Co': 9,
            'Mn': 7, 'Cr': 6, 'Al': 3, 'Ga': 3,
            'Ge': 4, 'Ti': 4, 'Mo': 6, 'W': 6
        }
    }

    def __init__(self):
        """Initialize the descriptor engine."""
        self._element_names = list(self.ELEMENT_PROPERTIES['atomic_mass'].keys())
        self._element_to_idx = {name: i for i, name in enumerate(self._element_names)}
        logger.debug(f"DescriptorEngine initialized with {len(self._element_names)} elements")

    def _get_element_indices(self, elements: List[str]) -> List[int]:
        """
        Map element symbols to indices in the property tables.

        Args:
            elements: List of element symbols

        Returns:
            List of indices
        """
        indices = []
        for elem in elements:
            if elem in self._element_to_idx:
                indices.append(self._element_to_idx[elem])
            else:
                logger.warning(f"Element {elem} not found in property tables, skipping")
                indices.append(-1)
        return indices

    def _compute_weighted_mean(self, weights: np.ndarray, property_values: np.ndarray) -> float:
        """Compute weighted mean of a property."""
        valid_mask = weights >= 0  # CLR weights can be negative, but we use them as-is
        if not np.any(valid_mask):
            return 0.0
        return np.sum(weights[valid_mask] * property_values[valid_mask]) / np.sum(weights[valid_mask])

    def _compute_weighted_variance(self, weights: np.ndarray, property_values: np.ndarray) -> float:
        """Compute weighted variance of a property."""
        if np.sum(weights) == 0:
            return 0.0
        mean = self._compute_weighted_mean(weights, property_values)
        variance = np.sum(weights * (property_values - mean) ** 2) / np.sum(weights)
        return variance

    def compute(self, clr_data: np.ndarray, raw_composition: pd.DataFrame) -> pd.DataFrame:
        """
        Compute descriptors from CLR-transformed data and raw composition.

        The CLR coefficients are used as weights for the original elemental properties.

        Args:
            clr_data: CLR-transformed data array of shape (n_samples, n_components)
            raw_composition: DataFrame with raw composition columns (element symbols as columns)

        Returns:
            DataFrame with computed descriptors
        """
        if clr_data.shape[0] != len(raw_composition):
            raise ValueError(f"clr_data rows ({clr_data.shape[0]}) != raw_composition rows ({len(raw_composition)})")

        descriptors = {}

        # Get element names from raw_composition columns
        element_cols = [col for col in raw_composition.columns if col in self._element_to_idx]
        if not element_cols:
            logger.error("No valid element columns found in raw_composition")
            raise ValueError("No valid element columns found")

        element_indices = self._get_element_indices(element_cols)

        for i, (prop_name, prop_dict) in enumerate(self.ELEMENT_PROPERTIES.items()):
            prop_values = np.array([prop_dict.get(elem, 0.0) for elem in element_cols])
            prop_values = np.array([prop_dict.get(element_cols[j], 0.0) for j in range(len(element_cols))])

            # Compute descriptor for each sample
            desc_values = []
            for sample_idx in range(clr_data.shape[0]):
                clr_weights = clr_data[sample_idx]
                # Use CLR weights as-is (they can be negative)
                desc = np.sum(clr_weights * prop_values)
                desc_values.append(desc)

            descriptors[f"{prop_name}_weighted"] = desc_values

        # Compute variance-based descriptors
        for prop_name in ['electronegativity', 'atomic_radius']:
            prop_dict = self.ELEMENT_PROPERTIES[prop_name]
            prop_values = np.array([prop_dict.get(elem, 0.0) for elem in element_cols])

            variance_values = []
            for sample_idx in range(clr_data.shape[0]):
                clr_weights = clr_data[sample_idx]
                # Weighted variance
                mean_val = np.sum(clr_weights * prop_values) / (np.sum(clr_weights) + 1e-10)
                variance = np.sum(clr_weights * (prop_values - mean_val) ** 2) / (np.sum(clr_weights) + 1e-10)
                variance_values.append(variance)

            descriptors[f"{prop_name}_variance"] = variance_values

        # Valence electron concentration (VEC) - weighted average
        vec_values = []
        for sample_idx in range(clr_data.shape[0]):
            clr_weights = clr_data[sample_idx]
            vec = np.sum(clr_weights * self.ELEMENT_PROPERTIES['valence_electrons'])
            vec_values.append(vec)
        descriptors['vec'] = vec_values

        return pd.DataFrame(descriptors, index=raw_composition.index)

    def compute_all(self, raw_composition: pd.DataFrame) -> pd.DataFrame:
        """
        Compute all descriptors directly from raw composition data.

        This method handles the full pipeline: closure -> CLR -> descriptor computation.

        Args:
            raw_composition: DataFrame with raw composition columns

        Returns:
            DataFrame with all computed descriptors
        """
        # Ensure closure (sum to 1)
        composition_closed = raw_composition.div(raw_composition.sum(axis=1), axis=0)

        # Apply CLR transformation
        transformer = CLRTransformer()
        clr_data = transformer.fit_transform(composition_closed.values)

        # Compute descriptors
        descriptors = self.compute(clr_data, raw_composition)

        logger.info(f"Computed {len(descriptors.columns)} descriptors for {len(descriptors)} samples")
        return descriptors

def main():
    """
    Main function for testing the descriptor engine.
    """
    from seed import init_reproducibility
    init_reproducibility()

    logger.info("Testing DescriptorEngine")

    # Sample raw composition data
    sample_composition = pd.DataFrame({
        'Sn': [0.5, 0.6, 0.4],
        'Ag': [0.3, 0.3, 0.4],
        'Cu': [0.2, 0.1, 0.2],
    })

    engine = DescriptorEngine()
    descriptors = engine.compute_all(sample_composition)

    logger.info(f"Sample composition:\n{sample_composition}")
    logger.info(f"Computed descriptors:\n{descriptors}")

    # Verify descriptors are computed
    expected_cols = [
        'atomic_mass_weighted', 'electronegativity_weighted',
        'atomic_radius_weighted', 'melting_point_weighted',
        'valence_electrons_weighted', 'electronegativity_variance',
        'atomic_radius_variance', 'vec'
    ]

    for col in expected_cols:
        if col in descriptors.columns:
            logger.info(f"✓ Descriptor {col} computed")
        else:
            logger.warning(f"✗ Descriptor {col} missing")

if __name__ == "__main__":
    main()
