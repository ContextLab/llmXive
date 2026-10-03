"""
DescriptorEngine: Computes physical descriptors from raw elemental composition.
Uses mendeleev for elemental properties.
"""
import numpy as np
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import json
from mendeleev import element
from utils.logging_config import get_logger

logger = get_logger(__name__)

class DescriptorEngine:
    """
    Engine to calculate weighted mean atomic mass, electronegativity variance,
    atomic radius variance, weighted average melting point, and valence electron concentration.
    """

    def __init__(self):
        self.element_cache: Dict[str, Any] = {}
        logger.info("DescriptorEngine initialized")

    def _get_element(self, symbol: str) -> Any:
        """Cache element lookups."""
        symbol = symbol.strip().upper()
        if symbol not in self.element_cache:
            try:
                self.element_cache[symbol] = element(symbol)
            except Exception as e:
                logger.error(f"Could not find element {symbol}: {e}")
                raise
        return self.element_cache[symbol]

    def calculate_weighted_mean_atomic_mass(self, composition: Dict[str, float]) -> float:
        """
        Calculate weighted mean atomic mass.
        Formula: sum(percent_i * atomic_mass_i) / 100
        """
        total_mass = 0.0
        total_percent = 0.0
        for symbol, percent in composition.items():
            el = self._get_element(symbol)
            if el.atomic_mass is not None:
                total_mass += percent * el.atomic_mass
                total_percent += percent
        
        if total_percent == 0:
            return 0.0
        return total_mass / total_percent

    def calculate_electronegativity_variance(self, composition: Dict[str, float]) -> float:
        """
        Calculate variance of electronegativity weighted by composition.
        First compute weighted mean, then weighted variance.
        """
        en_values = []
        weights = []
        
        for symbol, percent in composition.items():
            el = self._get_element(symbol)
            if el.electronegativity_pauling is not None:
                en_values.append(el.electronegativity_pauling)
                weights.append(percent)
        
        if not en_values:
            return 0.0

        weights = np.array(weights)
        en_vals = np.array(en_values)
        
        # Normalize weights
        w_sum = weights.sum()
        if w_sum == 0:
            return 0.0
        
        weights_norm = weights / w_sum
        mean_en = np.average(en_vals, weights=weights_norm)
        
        # Variance = sum(w * (x - mean)^2)
        variance = np.sum(weights_norm * (en_vals - mean_en) ** 2)
        return float(variance)

    def calculate_atomic_radius_variance(self, composition: Dict[str, float]) -> float:
        """
        Calculate variance of atomic radius weighted by composition.
        Note: mendeleev uses covalent_radius or atomic_radius. We use covalent_radius if available.
        """
        radius_values = []
        weights = []
        
        for symbol, percent in composition.items():
            el = self._get_element(symbol)
            # Prefer covalent radius, fallback to atomic radius
            r = el.covalent_radius if el.covalent_radius is not None else el.atomic_radius
            if r is not None:
                radius_values.append(r)
                weights.append(percent)
        
        if not radius_values:
            return 0.0

        weights = np.array(weights)
        r_vals = np.array(radius_values)
        
        w_sum = weights.sum()
        if w_sum == 0:
            return 0.0
        
        weights_norm = weights / w_sum
        mean_r = np.average(r_vals, weights=weights_norm)
        variance = np.sum(weights_norm * (r_vals - mean_r) ** 2)
        return float(variance)

    def calculate_weighted_avg_melting_point(self, composition: Dict[str, float]) -> float:
        """
        Calculate weighted average melting point.
        """
        mp_values = []
        weights = []
        
        for symbol, percent in composition.items():
            el = self._get_element(symbol)
            if el.melting_point is not None:
                mp_values.append(el.melting_point)
                weights.append(percent)
        
        if not mp_values:
            return 0.0

        weights = np.array(weights)
        mp_vals = np.array(mp_values)
        
        w_sum = weights.sum()
        if w_sum == 0:
            return 0.0
        
        return float(np.average(mp_vals, weights=weights / w_sum))

    def calculate_valence_electron_concentration(self, composition: Dict[str, float]) -> float:
        """
        Calculate Valence Electron Concentration (VEC).
        VEC = sum(percent_i * valence_i) / 100
        Mendeleev provides 'valence_electrons' or we infer from group.
        """
        total_valence = 0.0
        total_percent = 0.0
        
        for symbol, percent in composition.items():
            el = self._get_element(symbol)
            # Mendeleev attribute for valence electrons
            valence = el.valence_electrons
            if valence is not None:
                total_valence += percent * valence
                total_percent += percent
        
        if total_percent == 0:
            return 0.0
        return total_valence / total_percent

    def compute_all_descriptors(self, composition: Dict[str, float]) -> Dict[str, float]:
        """
        Compute all descriptors for a single composition.
        """
        return {
            'weighted_mean_atomic_mass': self.calculate_weighted_mean_atomic_mass(composition),
            'electronegativity_variance': self.calculate_electronegativity_variance(composition),
            'atomic_radius_variance': self.calculate_atomic_radius_variance(composition),
            'weighted_avg_melting_point': self.calculate_weighted_avg_melting_point(composition),
            'valence_electron_concentration': self.calculate_valence_electron_concentration(composition)
        }

def main():
    """
    Main entry point.
    Reads cleaned solder data, computes physical descriptors, and writes output.
    """
    logger.info("Starting Descriptor Engine Pipeline")

    input_path = Path("data/processed/solder_hardness_cleaned.csv")
    output_path = Path("data/processed/descriptors.csv")

    if not input_path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {input_path}. "
            "Run T013 (cleaner) first."
        )

    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} records from {input_path}")

    exclude_cols = ['hardness_hv', 'alloy_family', 'source_citation', 'alloy_id']
    composition_cols = [c for c in df.columns if c not in exclude_cols and not c.startswith('meta_')]

    if not composition_cols:
        raise ValueError("No composition columns found.")

    engine = DescriptorEngine()
    descriptors_list = []

    for idx, row in df.iterrows():
        comp = {col: row[col] for col in composition_cols}
        desc = engine.compute_all_descriptors(comp)
        descriptors_list.append(desc)

    df_desc = pd.DataFrame(descriptors_list)
    df_desc.to_csv(output_path, index=False)

    logger.info(f"Descriptors written to {output_path}")
    logger.info("Descriptor Engine Pipeline completed successfully")

if __name__ == "__main__":
    main()
