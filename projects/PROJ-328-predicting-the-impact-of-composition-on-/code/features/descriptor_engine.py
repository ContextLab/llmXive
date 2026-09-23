"""
Descriptor Engine for Solder Hardness Prediction.

Computes physical descriptors from raw elemental composition percentages
using Mendeleev elemental properties.

CRITICAL: This module calculates physical descriptors (weighted mean atomic mass,
electronegativity variance, etc.) using RAW percentages. It does NOT use CLR
transformed data for these calculations. CLR is applied separately for model input.
"""

import numpy as np
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import json

try:
    from mendeleev import element
except ImportError:
    raise ImportError("mendeleev package is required. Install with: pip install mendeleev")

from utils.logging_config import get_logger
from seed import set_seed
from config import get_config, get_data_processed_dir

logger = get_logger(__name__)

# Define the physical descriptors to compute
DESCRIPTORS = [
    'weighted_mean_atomic_mass',
    'electronegativity_variance',
    'atomic_radius_variance',
    'weighted_avg_melting_point',
    'valence_electron_concentration'
]

class DescriptorEngine:
    """
    Engine to compute physical descriptors from elemental compositions.
    
    Uses Mendeleev database for elemental properties.
    Computes descriptors from RAW elemental percentages (not CLR transformed).
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.element_cache: Dict[str, Any] = {}
        
    def _get_element(self, symbol: str):
        """Get element from Mendeleev with caching."""
        symbol = symbol.strip().upper()
        if symbol not in self.element_cache:
            try:
                self.element_cache[symbol] = element(symbol)
            except Exception as e:
                self.logger.warning(f"Could not find element {symbol}: {e}")
                return None
        return self.element_cache[symbol]
    
    def _safe_get_property(self, elem, prop_name: str, default: float = 0.0) -> float:
        """Safely get a property from an element, returning default if missing."""
        if elem is None:
            return default
        try:
            val = getattr(elem, prop_name, None)
            if val is None:
                return default
            return float(val)
        except Exception as e:
            self.logger.warning(f"Could not get {prop_name} for {elem.symbol}: {e}")
            return default
    
    def compute_weighted_mean_atomic_mass(self, composition: Dict[str, float]) -> float:
        """
        Compute weighted mean atomic mass.
        
        Args:
            composition: Dict mapping element symbol to percentage (0-100)
        
        Returns:
            Weighted mean atomic mass
        """
        total_mass = 0.0
        total_weight = 0.0
        
        for symbol, pct in composition.items():
            if pct <= 0:
                continue
            elem = self._get_element(symbol)
            atomic_mass = self._safe_get_property(elem, 'atomic_mass', 0.0)
            total_mass += atomic_mass * pct
            total_weight += pct
        
        if total_weight == 0:
            return 0.0
        
        return total_mass / total_weight
    
    def compute_electronegativity_variance(self, composition: Dict[str, float]) -> float:
        """
        Compute variance of electronegativity weighted by composition.
        
        Args:
            composition: Dict mapping element symbol to percentage (0-100)
        
        Returns:
            Electronegativity variance
        """
        en_values = []
        weights = []
        
        for symbol, pct in composition.items():
            if pct <= 0:
                continue
            elem = self._get_element(symbol)
            en = self._safe_get_property(elem, 'electronegativity', None)
            if en is not None:
                en_values.append(en)
                weights.append(pct)
        
        if len(en_values) == 0:
            return 0.0
        
        weights = np.array(weights)
        en_values = np.array(en_values)
        
        # Normalize weights to sum to 1
        weights = weights / weights.sum()
        
        # Compute weighted mean
        mean_en = np.sum(weights * en_values)
        
        # Compute weighted variance
        variance = np.sum(weights * (en_values - mean_en) ** 2)
        
        return float(variance)
    
    def compute_atomic_radius_variance(self, composition: Dict[str, float]) -> float:
        """
        Compute variance of atomic radius weighted by composition.
        
        Args:
            composition: Dict mapping element symbol to percentage (0-100)
        
        Returns:
            Atomic radius variance
        """
        radius_values = []
        weights = []
        
        for symbol, pct in composition.items():
            if pct <= 0:
                continue
            elem = self._get_element(symbol)
            # Try different radius properties
            radius = self._safe_get_property(elem, 'atomic_radius', None)
            if radius is None:
                radius = self._safe_get_property(elem, 'covalent_radius', None)
            if radius is None:
                radius = self._safe_get_property(elem, 'vdw_radius', None)
            
            if radius is not None:
                radius_values.append(radius)
                weights.append(pct)
        
        if len(radius_values) == 0:
            return 0.0
        
        weights = np.array(weights)
        radius_values = np.array(radius_values)
        
        # Normalize weights
        weights = weights / weights.sum()
        
        # Compute weighted mean
        mean_radius = np.sum(weights * radius_values)
        
        # Compute weighted variance
        variance = np.sum(weights * (radius_values - mean_radius) ** 2)
        
        return float(variance)
    
    def compute_weighted_avg_melting_point(self, composition: Dict[str, float]) -> float:
        """
        Compute weighted average melting point.
        
        Args:
            composition: Dict mapping element symbol to percentage (0-100)
        
        Returns:
            Weighted average melting point in Kelvin
        """
        total_mp = 0.0
        total_weight = 0.0
        
        for symbol, pct in composition.items():
            if pct <= 0:
                continue
            elem = self._get_element(symbol)
            melting_point = self._safe_get_property(elem, 'melting_point', 0.0)
            total_mp += melting_point * pct
            total_weight += pct
        
        if total_weight == 0:
            return 0.0
        
        return float(total_mp / total_weight)
    
    def compute_valence_electron_concentration(self, composition: Dict[str, float]) -> float:
        """
        Compute valence electron concentration.
        
        Args:
            composition: Dict mapping element symbol to percentage (0-100)
        
        Returns:
            Valence electron concentration (average valence electrons per atom)
        """
        total_valence = 0.0
        total_weight = 0.0
        
        for symbol, pct in composition.items():
            if pct <= 0:
                continue
            elem = self._get_element(symbol)
            # Get group number as a proxy for valence electrons
            valence = self._safe_get_property(elem, 'group', 0)
            # For transition metals, group number - 10 might be more accurate for d-electrons
            # But for simplicity, we use group number or estimate from electron configuration
            if valence == 0 and elem is not None:
                # Fallback: estimate from electron configuration
                try:
                    # Get the number of electrons in the outermost shell
                    ec = elem.electron_configuration
                    if ec:
                        # Simple heuristic: last group in config
                        parts = ec.split()
                        if parts:
                            last_part = parts[-1]
                            # Extract the coefficient (e.g., "4s2" -> 2)
                            import re
                            match = re.search(r'(\d+)$', last_part)
                            if match:
                                valence = int(match.group(1))
                except:
                    pass
            
            total_valence += valence * pct
            total_weight += pct
        
        if total_weight == 0:
            return 0.0
        
        return float(total_valence / total_weight)
    
    def compute_all_descriptors(self, composition: Dict[str, float]) -> Dict[str, float]:
        """
        Compute all physical descriptors for a single composition.
        
        Args:
            composition: Dict mapping element symbol to percentage (0-100)
        
        Returns:
            Dict mapping descriptor name to value
        """
        descriptors = {}
        
        descriptors['weighted_mean_atomic_mass'] = self.compute_weighted_mean_atomic_mass(composition)
        descriptors['electronegativity_variance'] = self.compute_electronegativity_variance(composition)
        descriptors['atomic_radius_variance'] = self.compute_atomic_radius_variance(composition)
        descriptors['weighted_avg_melting_point'] = self.compute_weighted_avg_melting_point(composition)
        descriptors['valence_electron_concentration'] = self.compute_valence_electron_concentration(composition)
        
        return descriptors
    
    def process_dataframe(self, df: pd.DataFrame, output_path: Path) -> pd.DataFrame:
        """
        Process a DataFrame of solder compositions and compute descriptors.
        
        CRITICAL: This uses RAW elemental percentages from the input DataFrame,
        NOT CLR transformed data.
        
        Args:
            df: DataFrame with columns for elemental percentages (e.g., 'Sn', 'Ag', 'Cu')
                and other metadata
            output_path: Path to save the output descriptors CSV
        
        Returns:
            DataFrame with original columns plus descriptor columns
        """
        self.logger.info(f"Processing {len(df)} compositions for descriptor computation")
        
        # Identify elemental columns (columns that are not metadata)
        # Assume elemental columns are uppercase letters or common element symbols
        elemental_cols = []
        for col in df.columns:
            # Skip known non-elemental columns
            if col.lower() in ['hardness_hv', 'alloy_family', 'source_citation', 'measurement_temp_c', 
                               'composition_sum', 'index', 'id', 'record_id']:
                continue
            # Check if it looks like an element symbol (1-2 uppercase letters, maybe followed by lowercase)
            if col.replace('.', '').replace('-', '').strip().isalpha() and len(col.strip()) <= 3:
                elemental_cols.append(col)
        
        self.logger.info(f"Identified {len(elemental_cols)} elemental columns: {elemental_cols}")
        
        if len(elemental_cols) == 0:
            self.logger.error("No elemental columns found in the DataFrame")
            # Create empty descriptors dataframe
            descriptors_df = pd.DataFrame()
            for desc in DESCRIPTORS:
                descriptors_df[desc] = np.nan
            descriptors_df.to_csv(output_path, index=False)
            return descriptors_df
        
        # Compute descriptors for each row
        descriptors_list = []
        valid_count = 0
        
        for idx, row in df.iterrows():
            composition = {}
            for col in elemental_cols:
                val = row[col]
                if pd.notna(val) and val > 0:
                    composition[col] = float(val)
            
            if len(composition) == 0:
                self.logger.warning(f"Row {idx} has no valid elemental composition")
                descriptors_list.append({desc: np.nan for desc in DESCRIPTORS})
                continue
            
            try:
                descriptors = self.compute_all_descriptors(composition)
                descriptors_list.append(descriptors)
                valid_count += 1
            except Exception as e:
                self.logger.error(f"Error computing descriptors for row {idx}: {e}")
                descriptors_list.append({desc: np.nan for desc in DESCRIPTORS})
        
        self.logger.info(f"Successfully computed descriptors for {valid_count}/{len(df)} compositions")
        
        # Create output DataFrame
        descriptors_df = pd.DataFrame(descriptors_list)
        
        # Ensure all descriptor columns exist
        for desc in DESCRIPTORS:
            if desc not in descriptors_df.columns:
                descriptors_df[desc] = np.nan
        
        # Concatenate with original data if needed, or just save descriptors
        # For this task, we save the descriptors separately
        descriptors_df.to_csv(output_path, index=False)
        
        self.logger.info(f"Saved descriptors to {output_path}")
        
        return descriptors_df

def main():
    """Main entry point for descriptor computation."""
    config = get_config()
    processed_dir = get_data_processed_dir()
    
    # Input file
    input_file = processed_dir / "solder_hardness_cleaned.csv"
    output_file = processed_dir / "descriptors.csv"
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please run T013 (cleaner.py) first to generate solder_hardness_cleaned.csv")
        return 1
    
    logger.info(f"Loading data from {input_file}")
    df = pd.read_csv(input_file)
    logger.info(f"Loaded {len(df)} records")
    
    # Initialize seed for reproducibility
    set_seed(42)
    
    # Create engine and process
    engine = DescriptorEngine()
    descriptors_df = engine.process_dataframe(df, output_file)
    
    if descriptors_df.empty:
        logger.error("No descriptors were computed. Check input data.")
        return 1
    
    logger.info(f"Descriptor computation complete. Output: {output_file}")
    logger.info(f"Descriptors computed: {list(descriptors_df.columns)}")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())