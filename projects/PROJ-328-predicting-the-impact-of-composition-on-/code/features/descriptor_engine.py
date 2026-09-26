"""
Descriptor Engine for Solder Alloy Hardness Prediction.

This module implements the calculation of physical descriptors based on
elemental composition data. It uses the Mendeleev library to fetch
elemental properties.

CRITICAL DISTINCTION (FR-003 & Plan.md):
-------------------------------------------------------
This engine computes PHYSICAL DESCRIPTORS (weighted mean atomic mass,
electronegativity variance, etc.) using the RAW elemental composition
percentages (e.g., 60% Sn, 40% Pb). These are physical properties of the
mixture.

DO NOT use CLR-transformed data here. The CLR transform (log-ratio) is
applied in `code/features/transformer.py` to create the input matrix for
the ML model to handle the compositional constraint (sum=1).

Physical Descriptors are calculated as:
  1. Weighted Mean Atomic Mass
  2. Electronegativity Variance
  3. Atomic Radius Variance
  4. Weighted Average Melting Point
  5. Valence Electron Concentration (VEC)

Input: data/processed/solder_hardness_cleaned.csv (RAW percentages)
Output: data/processed/descriptors.csv
"""

import numpy as np
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import json

from mendeleev import element
from config import get_max_elements, get_composition_sum_threshold, get_data_processed_dir
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Constants for physical property mapping
# Mendeleev element symbols are case-sensitive (e.g., 'Sn', 'Pb')
PHYSICAL_PROPERTIES = {
    'atomic_mass': 'atomic_mass',
    'electronegativity': 'electronegativity',
    'atomic_radius': 'atomic_radius',
    'melting_point': 'melting_point', # in Kelvin
    'valence': 'valence' # or 'electron_configuration'
}

class DescriptorEngine:
    """
    Calculates physical descriptors from raw elemental composition data.

    Attributes:
        max_elements (int): Maximum allowed number of elements per alloy (from config).
        composition_threshold (float): Minimum sum of composition percentages (from config).
        element_cache (dict): Cache for Mendeleev element objects to avoid repeated API/DB hits.
    """

    def __init__(self):
        self.max_elements = get_max_elements()
        self.composition_threshold = get_composition_sum_threshold()
        self.element_cache: Dict[str, Any] = {}
        logger.info(f"DescriptorEngine initialized. Max elements: {self.max_elements}, Threshold: {self.composition_threshold}")

    def _get_element(self, symbol: str) -> Optional[Any]:
        """
        Retrieves an element object from Mendeleev with caching.

        Args:
            symbol: Element symbol (e.g., 'Sn', 'Pb').

        Returns:
            Element object or None if not found.
        """
        symbol = symbol.strip()
        if symbol in self.element_cache:
            return self.element_cache[symbol]

        try:
            elem = element(symbol)
            self.element_cache[symbol] = elem
            return elem
        except Exception as e:
            logger.warning(f"Could not retrieve element '{symbol}': {e}")
            self.element_cache[symbol] = None
            return None

    def _get_property(self, elem: Any, prop_name: str) -> Optional[float]:
        """
        Safely retrieves a property from an element object.

        Args:
            elem: Mendeleev element object.
            prop_name: Name of the property.

        Returns:
            Property value or None if missing.
        """
        if elem is None:
            return None
        try:
            val = getattr(elem, prop_name)
            return float(val) if val is not None else None
        except Exception:
            return None

    def calculate_weighted_mean_atomic_mass(self, composition: Dict[str, float]) -> float:
        """
        Calculates the weighted mean atomic mass.
        Formula: sum(atomic_mass_i * fraction_i)

        Note: Composition values are expected as percentages (0-100) or fractions (0-1).
        We normalize to fractions internally.
        """
        total_mass = 0.0
        total_weight = 0.0

        for elem_symbol, percentage in composition.items():
            if percentage <= 0:
                continue
            elem = self._get_element(elem_symbol)
            mass = self._get_property(elem, 'atomic_mass')
            if mass is not None:
                total_mass += mass * percentage
                total_weight += percentage

        if total_weight == 0:
            return 0.0
        return total_mass / total_weight

    def calculate_electronegativity_variance(self, composition: Dict[str, float]) -> float:
        """
        Calculates the variance of electronegativity weighted by composition.
        Formula: sum( (EN_i - mean_EN)^2 * fraction_i )
        """
        # First pass: calculate weighted mean EN
        mean_en = 0.0
        total_weight = 0.0
        en_values = []
        en_weights = []

        for elem_symbol, percentage in composition.items():
            if percentage <= 0:
                continue
            elem = self._get_element(elem_symbol)
            en = self._get_property(elem, 'electronegativity')
            if en is not None:
                en_values.append(en)
                en_weights.append(percentage)
                mean_en += en * percentage
                total_weight += percentage

        if total_weight == 0:
            return 0.0

        mean_en /= total_weight

        # Second pass: calculate variance
        variance = 0.0
        for en, weight in zip(en_values, en_weights):
            variance += ((en - mean_en) ** 2) * weight

        return variance / total_weight

    def calculate_atomic_radius_variance(self, composition: Dict[str, float]) -> float:
        """
        Calculates the variance of atomic radius weighted by composition.
        """
        mean_radius = 0.0
        total_weight = 0.0
        radius_values = []
        radius_weights = []

        for elem_symbol, percentage in composition.items():
            if percentage <= 0:
                continue
            elem = self._get_element(elem_symbol)
            radius = self._get_property(elem, 'atomic_radius')
            if radius is not None:
                radius_values.append(radius)
                radius_weights.append(percentage)
                mean_radius += radius * percentage
                total_weight += percentage

        if total_weight == 0:
            return 0.0

        mean_radius /= total_weight

        variance = 0.0
        for radius, weight in zip(radius_values, radius_weights):
            variance += ((radius - mean_radius) ** 2) * weight

        return variance / total_weight

    def calculate_weighted_avg_melting_point(self, composition: Dict[str, float]) -> float:
        """
        Calculates the weighted average melting point.
        Note: Mendeleev returns melting point in Kelvin.
        """
        total_mp = 0.0
        total_weight = 0.0

        for elem_symbol, percentage in composition.items():
            if percentage <= 0:
                continue
            elem = self._get_element(elem_symbol)
            mp = self._get_property(elem, 'melting_point')
            if mp is not None:
                total_mp += mp * percentage
                total_weight += percentage

        if total_weight == 0:
            return 0.0
        return total_mp / total_weight

    def calculate_valence_electron_concentration(self, composition: Dict[str, float]) -> float:
        """
        Calculates the Valence Electron Concentration (VEC).
        VEC = sum(valence_i * fraction_i)
        """
        total_valence = 0.0
        total_weight = 0.0

        for elem_symbol, percentage in composition.items():
            if percentage <= 0:
                continue
            elem = self._get_element(elem_symbol)
            # Mendeleev 'valence' might return a string or list; handle carefully.
            # Often we use the group number or specific valence state.
            # For solder alloys (groups 13-15), we approximate with group number - 10 or similar.
            # Mendeleev `valence` attribute can be tricky. Let's try to get a numeric valence.
            # If 'valence' is not numeric, we might fallback to group number logic if needed,
            # but standard practice in literature often uses group number.
            # Let's try to fetch a numeric valence.
            try:
                val = self._get_property(elem, 'valence')
                if val is None:
                    # Fallback: use group number logic for main group elements if valence is ambiguous
                    # Group number - 10 for p-block (Sn, Pb, Sb, Bi, Ag, Cu, etc.)
                    group = elem.group
                    if group and group >= 13:
                        val = group - 10
                    elif group and group <= 2:
                        val = group
                    else:
                        val = 0
                else:
                    # Ensure it's a number (sometimes it's a list of possible valences)
                    if isinstance(val, list):
                        val = val[0]
                    val = float(val)
            except Exception:
                val = 0.0

            total_valence += val * percentage
            total_weight += percentage

        if total_weight == 0:
            return 0.0
        return total_valence / total_weight

    def process_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes a single row of raw composition data and computes all descriptors.

        Args:
            row: Dictionary containing elemental percentages and metadata.

        Returns:
            Dictionary with original row data + new descriptor columns.
        """
        # Identify elemental columns (keys that are valid element symbols)
        # We assume columns like 'Sn', 'Pb', 'Ag', etc. exist.
        # We filter out non-element columns like 'hardness_hv', 'source', etc.
        composition = {}
        for key, val in row.items():
            if key in ['hardness_hv', 'alloy_family', 'source_citation', 'measurement_temp_c', 'id']:
                continue
            try:
                # Check if key is a valid element symbol
                # Simple heuristic: 1-2 chars, first upper, second lower if exists
                if len(key) <= 2 and key[0].isupper() and (len(key) == 1 or key[1].islower()):
                    # Double check against Mendeleev to be safe
                    if self._get_element(key) is not None:
                        composition[key] = float(val) if val is not None else 0.0
            except (ValueError, TypeError):
                continue

        if not composition:
            logger.warning(f"No valid elemental composition found in row: {row.get('id', 'unknown')}")
            return {**row, **{
                'weighted_mean_atomic_mass': np.nan,
                'electronegativity_variance': np.nan,
                'atomic_radius_variance': np.nan,
                'weighted_avg_melting_point': np.nan,
                'valence_electron_concentration': np.nan
            }}

        # Validation: Check number of elements
        if len(composition) > self.max_elements:
            logger.warning(f"Row {row.get('id', 'unknown')} has {len(composition)} elements (> {self.max_elements}). Flagging.")
            # We still compute, but the cleaner should have filtered this.
            # If we are here, we compute anyway but maybe log.

        # Validation: Check composition sum
        comp_sum = sum(composition.values())
        if comp_sum < self.composition_threshold:
            logger.warning(f"Row {row.get('id', 'unknown')} composition sum {comp_sum:.2f} < {self.composition_threshold}. Flagging.")

        # Calculate Descriptors
        descriptors = {
            'weighted_mean_atomic_mass': self.calculate_weighted_mean_atomic_mass(composition),
            'electronegativity_variance': self.calculate_electronegativity_variance(composition),
            'atomic_radius_variance': self.calculate_atomic_radius_variance(composition),
            'weighted_avg_melting_point': self.calculate_weighted_avg_melting_point(composition),
            'valence_electron_concentration': self.calculate_valence_electron_concentration(composition)
        }

        return {**row, **descriptors}

    def run(self, input_path: str, output_path: str) -> pd.DataFrame:
        """
        Main entry point to process a CSV file and generate descriptors.

        Args:
            input_path: Path to input CSV (solder_hardness_cleaned.csv).
            output_path: Path to output CSV (descriptors.csv).

        Returns:
            The processed DataFrame.
        """
        logger.info(f"Starting Descriptor Engine. Input: {input_path}, Output: {output_path}")

        if not Path(input_path).exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} rows from {input_path}")

        results = []
        for idx, row in df.iterrows():
            try:
                processed_row = self.process_row(row.to_dict())
                results.append(processed_row)
            except Exception as e:
                logger.error(f"Error processing row {idx}: {e}")
                # Keep original row with NaNs for descriptors
                original = row.to_dict()
                for key in ['weighted_mean_atomic_mass', 'electronegativity_variance', 'atomic_radius_variance', 'weighted_avg_melting_point', 'valence_electron_concentration']:
                    original[key] = np.nan
                results.append(original)

        result_df = pd.DataFrame(results)
        result_df.to_csv(output_path, index=False)
        logger.info(f"Saved descriptors to {output_path}")

        return result_df

def main():
    """
    CLI entry point for the Descriptor Engine.
    Reads from data/processed/solder_hardness_cleaned.csv
    Writes to data/processed/descriptors.csv
    """
    input_file = str(get_data_processed_dir() / 'solder_hardness_cleaned.csv')
    output_file = str(get_data_processed_dir() / 'descriptors.csv')

    engine = DescriptorEngine()
    try:
        engine.run(input_file, output_file)
    except FileNotFoundError as e:
        logger.error(f"Failed to run descriptor engine: {e}")
        logger.error("Ensure that solder_hardness_cleaned.csv exists and is populated.")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in descriptor engine: {e}")
        raise

if __name__ == '__main__':
    main()