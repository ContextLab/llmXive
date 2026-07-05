"""
Descriptor engine for computing physical/chemical descriptors from CLR-transformed compositions.

Descriptors include:
- Weighted mean atomic mass
- Electronegativity variance
- Atomic radius variance
- Weighted average melting point
- Valence electron concentration (VEC)

Methodology:
1. Apply CLR to raw composition vector.
2. Use resulting CLR coefficients as weights for original raw elemental property tables.
   (NOT computing properties on log-ratios directly).
"""
import numpy as np
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from .transformer import CLRTransformer

logger = logging.getLogger(__name__)

# Standard elemental properties (Source: CRC Handbook / WebElements approximations)
# These are hardcoded as a fallback, but ideally loaded from a real data source or file
ELEMENT_PROPERTIES = {
    'Sn': {'atomic_mass': 118.71, 'electronegativity': 1.96, 'atomic_radius': 140, 'melting_point': 505.08, 'valence_electrons': 4},
    'Ag': {'atomic_mass': 107.87, 'electronegativity': 1.93, 'atomic_radius': 144, 'melting_point': 1234.93, 'valence_electrons': 1},
    'Cu': {'atomic_mass': 63.55, 'electronegativity': 1.90, 'atomic_radius': 128, 'melting_point': 1357.77, 'valence_electrons': 1},
    'Au': {'atomic_mass': 196.97, 'electronegativity': 2.54, 'atomic_radius': 144, 'melting_point': 1337.33, 'valence_electrons': 1},
    'In': {'atomic_mass': 114.82, 'electronegativity': 1.78, 'atomic_radius': 166, 'melting_point': 429.75, 'valence_electrons': 3},
    'Bi': {'atomic_mass': 208.98, 'electronegativity': 2.02, 'atomic_radius': 156, 'melting_point': 544.70, 'valence_electrons': 3},
    'Pb': {'atomic_mass': 207.2, 'electronegativity': 2.33, 'atomic_radius': 175, 'melting_point': 600.61, 'valence_electrons': 4},
    'Zn': {'atomic_mass': 65.38, 'electronegativity': 1.65, 'atomic_radius': 134, 'melting_point': 692.68, 'valence_electrons': 2},
    'Ni': {'atomic_mass': 58.69, 'electronegativity': 1.91, 'atomic_radius': 124, 'melting_point': 1728.00, 'valence_electrons': 2},
    'Sb': {'atomic_mass': 121.76, 'electronegativity': 2.05, 'atomic_radius': 140, 'melting_point': 903.78, 'valence_electrons': 3},
}

class DescriptorEngine:
    """
    Computes physical and chemical descriptors from solder compositions.
    """
    
    def __init__(self, property_source: Optional[Path] = None):
        """
        Initialize the descriptor engine.
        
        Args:
            property_source: Optional path to a CSV file with elemental properties.
                            If None, uses the hardcoded ELEMENT_PROPERTIES.
        """
        self.properties_df = self._load_properties(property_source)
        self.clr_transformer = CLRTransformer()
        self._feature_names = None

    def _load_properties(self, source: Optional[Path]) -> pd.DataFrame:
        """Load elemental properties from file or use defaults."""
        if source and source.exists():
            logger.info(f"Loading elemental properties from {source}")
            df = pd.read_csv(source)
            # Ensure expected columns exist
            required_cols = ['element', 'atomic_mass', 'electronegativity', 'atomic_radius', 'melting_point', 'valence_electrons']
            if not all(col in df.columns for col in required_cols):
                raise ValueError(f"Property file missing required columns: {required_cols}")
            return df.set_index('element')
        else:
            logger.info("Using hardcoded elemental properties")
            return pd.DataFrame(ELEMENT_PROPERTIES).T

    def _get_property_vector(self, property_name: str) -> np.ndarray:
        """Extract a property vector aligned with current feature names."""
        if self._feature_names is None:
            raise RuntimeError("Feature names must be set before computing descriptors.")
        
        values = []
        for elem in self._feature_names:
            if elem not in self.properties_df.index:
                # Fallback for unknown elements: use 0 or raise error? 
                # For robustness, we log warning and use 0
                logger.warning(f"Element '{elem}' not found in property database. Using 0 for {property_name}.")
                values.append(0.0)
            else:
                values.append(self.properties_df.loc[elem, property_name])
        return np.array(values)

    def compute_descriptors(self, compositions: pd.DataFrame) -> pd.DataFrame:
        """
        Compute descriptors for a dataframe of compositions.
        
        Args:
            compositions: DataFrame with columns as element symbols (e.g., 'Sn', 'Ag')
                          and rows as samples. Values are fractions (0-1).
        
        Returns:
            DataFrame with computed descriptors.
        """
        if compositions.empty:
            raise ValueError("Input compositions dataframe is empty.")
        
        # Store feature names for later use
        self._feature_names = list(compositions.columns)
        
        # Convert to numpy array
        X = compositions.values.astype(float)
        
        # 1. Apply CLR transform
        logger.info("Applying CLR transform to compositions...")
        clr_X, weights = self.clr_transformer.fit_transform(X, feature_names=self._feature_names)
        
        # 2. Compute descriptors using CLR coefficients as weights
        # The task specifies: "Using the resulting CLR coefficients to weight the original raw elemental property tables"
        # This implies a weighted sum where weights are the CLR values.
        # Note: CLR values can be negative. This is mathematically consistent with CoDA.
        
        descriptors = {}
        
        # Descriptor: Weighted Mean Atomic Mass
        prop_mass = self._get_property_vector('atomic_mass')
        descriptors['weighted_mean_atomic_mass'] = np.dot(clr_X, prop_mass)
        
        # Descriptor: Electronegativity Variance
        # Variance of property P weighted by composition? Or variance of CLR-weighted property?
        # Task says: "electronegativity variance". Usually in alloys, this is the variance of the property
        # across the distribution. 
        # Interpretation: Variance of the property values weighted by the CLR coefficients?
        # A more standard interpretation in this context (weighted by composition) is:
        # Var = sum(w_i * (P_i - mean_P)^2). But here we use CLR weights.
        # Let's interpret as: sum(clr_i * P_i^2) - (sum(clr_i * P_i))^2 ? 
        # Actually, let's stick to the simplest interpretation of "weighted variance" using the weights derived.
        # However, CLR weights sum to 0, so standard variance formula doesn't apply directly.
        # Alternative interpretation from literature: The variance of the property distribution.
        # Let's compute the variance of the property values themselves, but weighted by the magnitude of CLR?
        # Re-reading task: "Using the resulting CLR coefficients to weight the original raw elemental property tables"
        # This phrasing strongly suggests a linear combination: sum(clr_i * P_i).
        # For variance, maybe it means the variance of the CLR-weighted projections?
        # Let's compute: sum(clr_i * P_i^2) - (sum(clr_i * P_i))^2 is not valid if sum(clr)=0.
        # Let's try a different approach: The variance of the property values in the alloy.
        # Standard alloy variance: sum(x_i * (P_i - P_mean)^2).
        # But the task says "Using CLR coefficients". 
        # Let's assume the task implies: Variance = sum( (clr_i * P_i)^2 ) / sum(clr_i^2) ?
        # Or perhaps it simply means: Calculate the property variance of the original composition, 
        # but the task wants the CLR step to be explicit in the pipeline.
        # Let's go with: Variance of the property values weighted by the absolute CLR values (to handle sign).
        # OR, more likely, the task implies a specific descriptor formula from literature.
        # Given the ambiguity, I will implement: Weighted Variance = sum( w_i * (P_i - mean_P)^2 ) where w_i are CLR weights?
        # No, weights must be positive for variance.
        # Let's assume the "weight" refers to the magnitude of the contribution.
        # Let's implement: Variance = sum( clr_i^2 * P_i^2 ) - (sum(clr_i * P_i))^2? No.
        # Let's go with a robust definition: The variance of the property distribution.
        # We will calculate the standard variance but ensure the CLR step is the input transformation.
        # Actually, let's follow the instruction literally: "weight the ... tables".
        # Weighted Mean = sum(clr_i * P_i).
        # Weighted Variance = sum(clr_i * (P_i - WeightedMean)^2). 
        # Since sum(clr_i) = 0, this might be zero or negative.
        # Let's pivot to a safe interpretation: The variance of the property values in the alloy,
        # but the *pipeline* requires CLR first.
        # We will calculate the variance of the CLR-transformed property vector?
        # Let's do: Variance = np.var(clr_X * P_vec) ? No, that's element-wise.
        # Let's calculate the variance of the property values across the elements, weighted by the composition (x),
        # but the task says "Using CLR coefficients".
        # Okay, I will interpret this as: The variance of the property values weighted by the CLR coefficients,
        # treating CLR as a deviation from the mean.
        # Variance = sum( clr_i * (P_i - mean_P)^2 ) / sum(clr_i^2)?
        # Let's just compute the variance of the CLR-weighted property vector:
        # descriptors['electronegativity_variance'] = np.var(clr_X * prop_en)
        # This seems the most direct interpretation of "using CLR coefficients".
        
        prop_en = self._get_property_vector('electronegativity')
        descriptors['electronegativity_variance'] = np.var(clr_X * prop_en, axis=1) # Wait, axis?
        # clr_X is (N, D), prop_en is (D,). clr_X * prop_en is (N, D).
        # np.var of that gives a scalar per row? Yes, if axis is not specified, it's all.
        # We want per sample.
        descriptors['electronegativity_variance'] = np.var(clr_X * prop_en, axis=1)
        
        # Atomic Radius Variance
        prop_radius = self._get_property_vector('atomic_radius')
        descriptors['atomic_radius_variance'] = np.var(clr_X * prop_radius, axis=1)
        
        # Weighted Average Melting Point
        prop_mp = self._get_property_vector('melting_point')
        descriptors['weighted_avg_melting_point'] = np.dot(clr_X, prop_mp)
        
        # Valence Electron Concentration (VEC)
        prop_vec = self._get_property_vector('valence_electrons')
        descriptors['vec'] = np.dot(clr_X, prop_vec)
        
        # Create result DataFrame
        result_df = pd.DataFrame(descriptors, index=compositions.index)
        
        # Add original composition columns for reference? No, just descriptors.
        logger.info(f"Computed descriptors: {list(descriptors.keys())}")
        return result_df
