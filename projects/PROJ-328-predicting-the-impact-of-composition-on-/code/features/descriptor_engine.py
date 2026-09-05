"""
DescriptorEngine: Computes physical and chemical descriptors from elemental compositions.

Calculates weighted mean atomic mass, electronegativity variance, atomic radius variance,
weighted average melting point, and valence electron concentration using the mendeleev library.

IMPORTANT: Physical descriptors are computed using RAW elemental percentages (normalized to sum to 1).
CLR-transformed values are NOT used as weights for physical descriptors, as they can be negative.
"""
import numpy as np
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from features.transformer import CLRTransformer
from utils.logging_config import get_logger
from seed import set_seed
from mendeleev import element
from utils.error_handlers import ConfigurationError

logger = get_logger(__name__)

class DescriptorEngine:
    """
    Engine for computing compositional descriptors and CLR features.
    """

    def __init__(self, element_properties: Optional[List[str]] = None):
        """
        Initialize the Descriptor Engine.

        Args:
            element_properties: List of property names to fetch from mendeleev.
                               Defaults to standard set if None.
        """
        self.element_properties = element_properties or [
            'atomic_mass', 'electronegativity', 'atomic_radius', 
            'melting_point', 'valence'
        ]
        logger.info("DescriptorEngine initialized")

    def _get_element_property(self, symbol: str, prop: str) -> float:
        """
        Safely fetch a property for an element symbol.

        Args:
            symbol: Element symbol (e.g., 'Sn', 'Ag').
            prop: Property name.

        Returns:
            Property value or np.nan if not found.
        """
        try:
            el = element(symbol)
            val = getattr(el, prop, None)
            if val is None:
                logger.warning(f"Property '{prop}' not found for element '{symbol}'")
                return np.nan
            return float(val)
        except Exception as e:
            logger.error(f"Failed to fetch {prop} for {symbol}: {e}")
            return np.nan

    def compute_physical_descriptors(self, composition: Dict[str, float]) -> Dict[str, float]:
        """
        Compute physical descriptors from a raw composition dictionary.
        
        CRITICAL: Uses raw percentages (normalized to sum to 1) as weights.
        Does NOT use CLR-transformed values.

        Args:
            composition: Dict mapping element symbol to percentage (e.g., {'Sn': 60.0, 'Ag': 40.0}).

        Returns:
            Dictionary of computed physical descriptors.
        """
        if not composition:
            raise ValueError("Composition cannot be empty")

        # Normalize to sum to 1.0
        total = sum(composition.values())
        if total == 0:
            raise ValueError("Total composition sum is zero")
        
        weights = {k: v / total for k, v in composition.items()}

        descriptors = {}
        
        # 1. Weighted Mean Atomic Mass
        atomic_masses = {sym: self._get_element_property(sym, 'atomic_mass') for sym in composition}
        descriptors['weighted_mean_atomic_mass'] = sum(
            weights[sym] * (mass if not np.isnan(mass) else 0) 
            for sym, mass in atomic_masses.items()
        )

        # 2. Electronegativity Variance
        electronegativities = {sym: self._get_element_property(sym, 'electronegativity') for sym in composition}
        valid_en = [(w, en) for w, en in zip(weights.values(), electronegativities.values()) if not np.isnan(en)]
        if valid_en:
            w_en_vals, w_weights = zip(*valid_en)
            w_mean_en = sum(w * v for w, v in zip(w_weights, w_en_vals))
            descriptors['electronegativity_variance'] = sum(
                w * (v - w_mean_en)**2 for w, v in zip(w_weights, w_en_vals)
            )
        else:
            descriptors['electronegativity_variance'] = np.nan

        # 3. Atomic Radius Variance
        atomic_radii = {sym: self._get_element_property(sym, 'atomic_radius') for sym in composition}
        valid_ar = [(w, ar) for w, ar in zip(weights.values(), atomic_radii.values()) if not np.isnan(ar)]
        if valid_ar:
            w_ar_vals, w_weights = zip(*valid_ar)
            w_mean_ar = sum(w * v for w, v in zip(w_weights, w_ar_vals))
            descriptors['atomic_radius_variance'] = sum(
                w * (v - w_mean_ar)**2 for w, v in zip(w_weights, w_ar_vals)
            )
        else:
            descriptors['atomic_radius_variance'] = np.nan

        # 4. Weighted Average Melting Point
        melting_points = {sym: self._get_element_property(sym, 'melting_point') for sym in composition}
        descriptors['weighted_avg_melting_point'] = sum(
            weights[sym] * (mp if not np.isnan(mp) else 0) 
            for sym, mp in melting_points.items()
        )

        # 5. Valence Electron Concentration (VEC)
        # Simplified: weighted average of valence electrons
        valences = {sym: self._get_element_property(sym, 'valence') for sym in composition}
        valid_v = [(w, v) for w, v in zip(weights.values(), valences.values()) if not np.isnan(v)]
        if valid_v:
            w_v_vals, w_weights = zip(*valid_v)
            descriptors['valence_electron_concentration'] = sum(
                w * v for w, v in zip(w_weights, w_v_vals)
            )
        else:
            descriptors['valence_electron_concentration'] = np.nan

        return descriptors

    def compute_clr_features(self, composition: Dict[str, float], element_order: List[str]) -> np.ndarray:
        """
        Compute CLR-transformed feature vector for a composition.

        Args:
            composition: Dict mapping element symbol to percentage.
            element_order: Ordered list of all possible elements to ensure consistent vector length.

        Returns:
            CLR-transformed numpy array of shape (n_elements,).
        """
        # Create vector in consistent order
        vector = np.array([composition.get(el, 0.0) for el in element_order], dtype=float)
        
        if vector.sum() == 0:
            raise ValueError("Composition vector is all zeros")

        # Apply CLR transform
        transformer = CLRTransformer()
        return transformer.transform(vector.reshape(1, -1))[0]

    def process_dataframe(self, df: pd.DataFrame, composition_col: str = 'elemental_breakdown') -> pd.DataFrame:
        """
        Process a dataframe of solder compositions, adding physical descriptors and CLR features.

        Args:
            df: DataFrame with a column containing composition dictionaries.
            composition_col: Name of the column containing composition dicts.

        Returns:
            DataFrame with added descriptor columns and CLR feature columns.
        """
        logger.info(f"Processing {len(df)} rows for descriptor engineering")
        
        # Determine all unique elements to define vector order
        all_elements = set()
        for comp in df[composition_col]:
            if isinstance(comp, dict):
                all_elements.update(comp.keys())
        
        element_order = sorted(list(all_elements))
        logger.info(f"Detected {len(element_order)} unique elements: {element_order}")

        # Compute physical descriptors
        descriptors_list = []
        for comp in df[composition_col]:
            if isinstance(comp, dict):
                descriptors_list.append(self.compute_physical_descriptors(comp))
            else:
                descriptors_list.append({})
        
        desc_df = pd.DataFrame(descriptors_list)
        
        # Compute CLR features
        clr_features = []
        for comp in df[composition_col]:
            if isinstance(comp, dict):
                clr_vec = self.compute_clr_features(comp, element_order)
                clr_features.append(clr_vec)
            else:
                clr_features.append(np.zeros(len(element_order)))
        
        clr_df = pd.DataFrame(clr_features, columns=[f'clr_{el}' for el in element_order])

        # Combine
        result = pd.concat([df, desc_df, clr_df], axis=1)
        logger.info(f"Descriptor engineering complete. Shape: {result.shape}")
        return result

def main():
    """
    Main entry point for testing the DescriptorEngine.
    """
    logger.info("Starting DescriptorEngine test")
    set_seed(42)

    # Example usage
    test_compositions = [
        {'Sn': 60.0, 'Pb': 40.0},
        {'Sn': 99.0, 'Ag': 1.0},
        {'Sn': 96.5, 'Ag': 3.0, 'Cu': 0.5}
    ]

    engine = DescriptorEngine()
    
    for i, comp in enumerate(test_compositions):
        logger.info(f"\n--- Processing Composition {i+1}: {comp} ---")
        phys_desc = engine.compute_physical_descriptors(comp)
        logger.info(f"Physical Descriptors: {phys_desc}")
        
        element_order = sorted(list(comp.keys()))
        clr_vec = engine.compute_clr_features(comp, element_order)
        logger.info(f"CLR Vector: {clr_vec}")

    logger.info("DescriptorEngine test completed successfully")

if __name__ == "__main__":
    main()
