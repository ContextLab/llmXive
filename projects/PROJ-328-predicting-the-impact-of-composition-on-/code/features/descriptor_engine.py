"""
DescriptorEngine: Computes physical and chemical descriptors from solder compositions.
"""
import numpy as np
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from features.transformer import CLRTransformer

logger = logging.getLogger(__name__)

# Elemental properties (raw constants)
# Source: Standard periodic table data (approximate values for common solder elements)
ELEMENT_PROPERTIES = {
    'Sn': {'atomic_mass': 118.71, 'electronegativity': 1.96, 'atomic_radius': 140, 'melting_point': 231.93, 'valence_electrons': 4},
    'Pb': {'atomic_mass': 207.2, 'electronegativity': 2.33, 'atomic_radius': 175, 'melting_point': 327.46, 'valence_electrons': 4},
    'Ag': {'atomic_mass': 107.87, 'electronegativity': 1.93, 'atomic_radius': 144, 'melting_point': 961.78, 'valence_electrons': 1},
    'Cu': {'atomic_mass': 63.55, 'electronegativity': 1.90, 'atomic_radius': 128, 'melting_point': 1084.62, 'valence_electrons': 1},
    'Bi': {'atomic_mass': 208.98, 'electronegativity': 2.02, 'atomic_radius': 156, 'melting_point': 271.4, 'valence_electrons': 5},
    'In': {'atomic_mass': 114.82, 'electronegativity': 1.78, 'atomic_radius': 155, 'melting_point': 156.6, 'valence_electrons': 3},
    'Sb': {'atomic_mass': 121.76, 'electronegativity': 2.05, 'atomic_radius': 140, 'melting_point': 630.63, 'valence_electrons': 5},
    'Au': {'atomic_mass': 196.97, 'electronegativity': 2.54, 'atomic_radius': 144, 'melting_point': 1064.18, 'valence_electrons': 1},
    'Ni': {'atomic_mass': 58.69, 'electronegativity': 1.91, 'atomic_radius': 124, 'melting_point': 1455.0, 'valence_electrons': 2},
    'Zn': {'atomic_mass': 65.38, 'electronegativity': 1.65, 'atomic_radius': 134, 'melting_point': 419.53, 'valence_electrons': 2},
}

class DescriptorEngine:
    """
    Engine for computing physical descriptors from compositional data.
    """

    def __init__(self, element_properties: Optional[Dict[str, Dict[str, float]]] = None):
        """
        Initialize the DescriptorEngine.

        Args:
            element_properties: Dictionary of elemental properties. Defaults to built-in set.
        """
        self.properties = element_properties or ELEMENT_PROPERTIES
        self.feature_names = [
            'weighted_mean_atomic_mass',
            'electronegativity_variance',
            'atomic_radius_variance',
            'weighted_avg_melting_point',
            'valence_electron_concentration'
        ]
        logger.info("DescriptorEngine initialized")

    def compute_physical_descriptors(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute physical descriptors using raw elemental composition percentages as weights.

        Method:
            1. Calculate weighted mean/variance of properties using raw composition.
            2. Do NOT apply CLR to the physical constants.

        Args:
            df: DataFrame with elemental composition columns (e.g., 'Sn', 'Pb', 'Ag').

        Returns:
            DataFrame with added descriptor columns.
        """
        descriptors = {}

        # Identify element columns (assume columns matching keys in properties)
        element_cols = [col for col in df.columns if col in self.properties]
        if not element_cols:
            logger.warning("No element columns found in DataFrame")
            return df

        # Ensure we have valid weights (sum to ~1)
        # We assume input is already normalized or close to it
        weights = df[element_cols].fillna(0)

        # 1. Weighted Mean Atomic Mass
        atomic_masses = [self.properties[e]['atomic_mass'] for e in element_cols]
        descriptors['weighted_mean_atomic_mass'] = (weights * atomic_masses).sum(axis=1)

        # 2. Weighted Mean Electronegativity (for variance calculation)
        electronegativities = [self.properties[e]['electronegativity'] for e in element_cols]
        mean_en = (weights * electronegativities).sum(axis=1)
        # Variance: sum(w_i * (x_i - mean)^2)
        var_en = (weights * (np.array(electronegativities) - mean_en.values[:, np.newaxis])**2).sum(axis=1)
        descriptors['electronegativity_variance'] = var_en

        # 3. Weighted Mean Atomic Radius (for variance calculation)
        atomic_radii = [self.properties[e]['atomic_radius'] for e in element_cols]
        mean_ar = (weights * atomic_radii).sum(axis=1)
        var_ar = (weights * (np.array(atomic_radii) - mean_ar.values[:, np.newaxis])**2).sum(axis=1)
        descriptors['atomic_radius_variance'] = var_ar

        # 4. Weighted Average Melting Point
        melting_points = [self.properties[e]['melting_point'] for e in element_cols]
        descriptors['weighted_avg_melting_point'] = (weights * melting_points).sum(axis=1)

        # 5. Valence Electron Concentration (VEC)
        valence_electrons = [self.properties[e]['valence_electrons'] for e in element_cols]
        descriptors['valence_electron_concentration'] = (weights * valence_electrons).sum(axis=1)

        # Create descriptor DataFrame
        desc_df = pd.DataFrame(descriptors, index=df.index)

        # Concatenate with original DataFrame
        result = pd.concat([df, desc_df], axis=1)
        logger.info(f"Computed {len(descriptors)} physical descriptors")

        return result

    def apply_clr_to_composition(self, df: pd.DataFrame, element_cols: List[str]) -> pd.DataFrame:
        """
        Apply CLR transform to the composition vector.

        Args:
            df: DataFrame with elemental composition columns.
            element_cols: List of column names representing elements.

        Returns:
            DataFrame with CLR-transformed composition columns (prefix 'clr_').
        """
        if not element_cols:
            logger.warning("No element columns provided for CLR transform")
            return df

        # Extract composition matrix
        X = df[element_cols].values.astype(float)

        # Handle missing values
        X = np.nan_to_num(X, nan=0.0)

        # Apply CLR
        transformer = CLRTransformer()
        try:
            X_clr = transformer.fit_transform(X)
        except Exception as e:
            logger.error(f"CLR transform failed: {e}")
            raise

        # Create new column names
        clr_cols = [f'clr_{col}' for col in element_cols]

        # Create DataFrame for CLR values
        clr_df = pd.DataFrame(X_clr, columns=clr_cols, index=df.index)

        # Concatenate
        result = pd.concat([df, clr_df], axis=1)
        logger.info(f"Applied CLR transform to {len(element_cols)} elements")

        return result

    def generate_feature_matrix(self, df: pd.DataFrame, use_physical_descriptors: bool = True,
                                use_clr_composition: bool = True) -> Tuple[pd.DataFrame, List[str]]:
        """
        Generate the final feature matrix for modeling.

        Args:
            df: Input DataFrame with composition and properties.
            use_physical_descriptors: Whether to include computed physical descriptors.
            use_clr_composition: Whether to include CLR-transformed composition.

        Returns:
            Tuple of (feature_matrix, list_of_feature_names)
        """
        # Identify element columns
        element_cols = [col for col in df.columns if col in self.properties]

        feature_data = df.copy()

        # Step 1: Compute physical descriptors (if requested)
        if use_physical_descriptors:
            feature_data = self.compute_physical_descriptors(feature_data)

        # Step 2: Apply CLR to composition (if requested)
        if use_clr_composition:
            feature_data = self.apply_clr_to_composition(feature_data, element_cols)

        # Select features for model
        selected_features = []
        if use_physical_descriptors:
            selected_features.extend(self.feature_names)
        if use_clr_composition:
            selected_features.extend([f'clr_{col}' for col in element_cols])

        # Filter to existing columns
        available_features = [f for f in selected_features if f in feature_data.columns]
        X = feature_data[available_features]

        logger.info(f"Generated feature matrix with {len(available_features)} features")

        return X, available_features

def main():
    """
    Main entry point for testing the DescriptorEngine.
    """
    logger.info("Starting DescriptorEngine test")

    # Create sample data
    data = {
        'Sn': [0.95, 0.63, 0.50],
        'Pb': [0.05, 0.37, 0.25],
        'Ag': [0.00, 0.00, 0.25],
        'target_hardness': [15.0, 12.0, 10.0]
    }
    df = pd.DataFrame(data)

    engine = DescriptorEngine()

    # Test physical descriptors
    df_desc = engine.compute_physical_descriptors(df)
    print("Physical Descriptors:")
    print(df_desc[engine.feature_names])

    # Test CLR transform
    df_clr = engine.apply_clr_to_composition(df, ['Sn', 'Pb', 'Ag'])
    print("\nCLR Transformed:")
    print(df_clr[[f'clr_{c}' for c in ['Sn', 'Pb', 'Ag']]])

    # Test full feature matrix
    X, features = engine.generate_feature_matrix(df)
    print(f"\nFeature Matrix Shape: {X.shape}")
    print(f"Features: {features}")

    logger.info("DescriptorEngine test completed")

if __name__ == "__main__":
    main()
