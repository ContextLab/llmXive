"""
Descriptor Engine for Solder Alloy Hardness Prediction.

This module implements the computation of compositional descriptors from raw
solder alloy fractions. It calculates physical property-based features (weighted
means and variances) and applies a Centered Log-Ratio (CLR) transform to handle
the compositional closure problem before returning the feature matrix.
"""

import numpy as np
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from features.transformer import CLRTransformer
from utils.logging_config import get_logger
from utils.error_handlers import DataValidationError
from seed import set_seed

# Initialize logger
logger = get_logger(__name__)

# Periodic Table Data (Atomic Mass, Electronegativity (Pauling), Atomic Radius (pm), Melting Point (C), Valence Electrons)
# Source: Standard periodic table data, curated for common solder elements (Sn, Pb, Ag, Cu, Bi, In, Sb, Zn, Al, Ni)
# Note: Values are approximate averages where isotopes or allotropes vary slightly.
ELEMENT_PROPERTIES = {
    'Sn': {'mass': 118.71, 'en': 1.96, 'radius': 145, 'mp': 231.93, 'valence': 4},
    'Pb': {'mass': 207.2,  'en': 2.33, 'radius': 175, 'mp': 327.46, 'valence': 4},
    'Ag': {'mass': 107.87, 'en': 1.93, 'radius': 165, 'mp': 961.78, 'valence': 1},
    'Cu': {'mass': 63.55,  'en': 1.90, 'radius': 128, 'mp': 1084.62, 'valence': 1}, # Often treated as 1 or 2, using 1 for simplicity
    'Bi': {'mass': 208.98, 'en': 2.02, 'radius': 160, 'mp': 271.3, 'valence': 3},
    'In': {'mass': 114.82, 'en': 1.78, 'radius': 156, 'mp': 156.6, 'valence': 3},
    'Sb': {'mass': 121.76, 'en': 2.05, 'radius': 140, 'mp': 630.6, 'valence': 3},
    'Zn': {'mass': 65.38,  'en': 1.65, 'radius': 134, 'mp': 419.53, 'valence': 2},
    'Al': {'mass': 26.98,  'en': 1.61, 'radius': 143, 'mp': 660.32, 'valence': 3},
    'Ni': {'mass': 58.69,  'en': 1.91, 'radius': 124, 'mp': 1455.0, 'valence': 2},
    'Au': {'mass': 196.97, 'en': 2.54, 'radius': 144, 'mp': 1064.18, 'valence': 1},
    'Ge': {'mass': 72.63,  'en': 2.01, 'radius': 122, 'mp': 938.25, 'valence': 4},
    'Ga': {'mass': 69.72,  'en': 1.81, 'radius': 135, 'mp': 29.76, 'valence': 3},
}

DESCRIPTOR_NAMES = [
    'weighted_mean_atomic_mass',
    'electronegativity_variance',
    'atomic_radius_variance',
    'weighted_avg_melting_point',
    'valence_electron_concentration'
]

class DescriptorEngine:
    """
    Computes compositional descriptors from raw solder alloy fractions.

    Methodology:
    1. Uses original raw composition fractions as weights.
    2. Calculates weighted means and variances of elemental properties.
    3. Applies CLR transform to the resulting descriptor vector.
    """

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            set_seed(seed)
        self.logger = logger

    def _validate_input(self, df: pd.DataFrame) -> None:
        """Validates that the input dataframe contains expected composition columns."""
        if df.empty:
            raise DataValidationError("Input dataframe is empty.")

        # Identify composition columns (assume columns ending in '_frac' or known element names)
        # For robustness, we look for columns that are likely elemental fractions.
        # Common convention in this project: columns named by element symbol (e.g., 'Sn', 'Pb') or 'Sn_frac'.
        # We will assume columns are named by element symbol based on standard ingestion practices.
        element_cols = [col for col in df.columns if col in ELEMENT_PROPERTIES.keys()]

        if not element_cols:
            raise DataValidationError(
                f"No elemental composition columns found. "
                f"Expected columns matching known elements: {list(ELEMENT_PROPERTIES.keys())}. "
                f"Found columns: {list(df.columns)}"
            )

        return element_cols

    def _compute_raw_descriptors(self, df: pd.DataFrame, element_cols: List[str]) -> pd.DataFrame:
        """
        Computes raw (pre-CLR) descriptors using weighted averages/variances.

        Args:
            df: Input dataframe with composition columns.
            element_cols: List of column names representing element fractions.

        Returns:
            DataFrame with raw descriptor columns.
        """
        descriptors = {}

        # 1. Weighted Mean Atomic Mass
        # mass_i * fraction_i
        descriptors['weighted_mean_atomic_mass'] = 0.0
        for elem in element_cols:
            prop = ELEMENT_PROPERTIES[elem]['mass']
            descriptors['weighted_mean_atomic_mass'] += df[elem] * prop

        # 2. Weighted Average Melting Point
        descriptors['weighted_avg_melting_point'] = 0.0
        for elem in element_cols:
            prop = ELEMENT_PROPERTIES[elem]['mp']
            descriptors['weighted_avg_melting_point'] += df[elem] * prop

        # 3. Valence Electron Concentration (VEC)
        # Weighted average of valence electrons
        descriptors['valence_electron_concentration'] = 0.0
        for elem in element_cols:
            prop = ELEMENT_PROPERTIES[elem]['valence']
            descriptors['valence_electron_concentration'] += df[elem] * prop

        # 4. Electronegativity Variance
        # Var = sum( (x_i - mean_x)^2 * w_i )
        # First compute weighted mean EN
        weighted_mean_en = 0.0
        for elem in element_cols:
            prop = ELEMENT_PROPERTIES[elem]['en']
            weighted_mean_en += df[elem] * prop

        variance_en = 0.0
        for elem in element_cols:
            prop = ELEMENT_PROPERTIES[elem]['en']
            variance_en += df[elem] * ((prop - weighted_mean_en) ** 2)
        descriptors['electronegativity_variance'] = variance_en

        # 5. Atomic Radius Variance
        weighted_mean_radius = 0.0
        for elem in element_cols:
            prop = ELEMENT_PROPERTIES[elem]['radius']
            weighted_mean_radius += df[elem] * prop

        variance_radius = 0.0
        for elem in element_cols:
            prop = ELEMENT_PROPERTIES[elem]['radius']
            variance_radius += df[elem] * ((prop - weighted_mean_radius) ** 2)
        descriptors['atomic_radius_variance'] = variance_radius

        return pd.DataFrame(descriptors)

    def compute_descriptors(self, df: pd.DataFrame, input_col_prefix: str = '') -> pd.DataFrame:
        """
        Main entry point to compute CLR-transformed descriptors.

        Args:
            df: Input dataframe containing raw composition fractions.
            input_col_prefix: Optional prefix for composition columns if they are named 'Sn_frac', etc.

        Returns:
            DataFrame with CLR-transformed descriptors ready for modeling.
        """
        self.logger.info(f"Starting descriptor computation for {len(df)} samples.")

        # Determine actual column names (handle optional prefix)
        element_cols = []
        for elem in ELEMENT_PROPERTIES.keys():
            col_name = f"{elem}_{input_col_prefix}" if input_col_prefix else elem
            # Fallback if prefix was added differently
            if col_name not in df.columns:
                col_name = elem
            if col_name in df.columns:
                element_cols.append(col_name)

        if not element_cols:
            # Try to find columns that match element names directly if prefix logic failed
            element_cols = [col for col in df.columns if col in ELEMENT_PROPERTIES.keys()]

        if not element_cols:
            raise DataValidationError(
                f"Could not identify composition columns. "
                f"Expected: {list(ELEMENT_PROPERTIES.keys())}, Found: {list(df.columns)}"
            )

        # Step 1: Compute raw descriptors
        raw_desc_df = self._compute_raw_descriptors(df, element_cols)

        # Step 2: Apply CLR transform
        # The CLR transform requires strictly positive values.
        # Descriptors like variance are >= 0. If 0, CLR fails (log(0)).
        # We add a small epsilon to avoid log(0) if necessary, though physical descriptors
        # for alloys usually have non-zero variance unless pure element (which is rare in solder datasets).
        epsilon = 1e-10
        raw_desc_df = raw_desc_df.clip(lower=epsilon)

        clr_transformer = CLRTransformer()
        clr_features = clr_transformer.fit_transform(raw_desc_df.values)

        # Create result DataFrame with proper column names
        result_df = pd.DataFrame(clr_features, columns=[f"clr_{name}" for name in DESCRIPTOR_NAMES])
        
        # Add original index to maintain alignment if needed later
        result_df.index = df.index

        self.logger.info(f"Descriptor computation complete. Output shape: {result_df.shape}")
        return result_df

def main():
    """
    Standalone runner for testing the Descriptor Engine.
    Expects a validated dataset at data/processed/solder_hardness_validated.csv
    """
    import sys
    from pathlib import Path

    # Add project root to path
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))

    data_path = project_root / "data" / "processed" / "solder_hardness_validated.csv"
    output_path = project_root / "data" / "processed" / "descriptors_clipped.csv"

    if not data_path.exists():
        logger.error(f"Input file not found: {data_path}")
        logger.error("Please ensure T016 (Validation) has completed successfully.")
        sys.exit(1)

    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)

    logger.info("Initializing Descriptor Engine")
    engine = DescriptorEngine(seed=42)

    try:
        logger.info("Computing descriptors...")
        # Assuming columns are named 'Sn', 'Pb', etc. as per typical ingestion
        feature_df = engine.compute_descriptors(df)
        
        logger.info(f"Feature matrix shape: {feature_df.shape}")
        logger.info(f"Feature columns: {list(feature_df.columns)}")

        # Save output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        feature_df.to_csv(output_path, index=False)
        logger.info(f"Saved descriptors to {output_path}")

    except Exception as e:
        logger.error(f"Failed to compute descriptors: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()