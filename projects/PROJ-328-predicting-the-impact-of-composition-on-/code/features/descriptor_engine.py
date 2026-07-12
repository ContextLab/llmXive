import numpy as np
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import os

# Relative import for local package structure
from .transformer import CLRTransformer
from ..config import get_data_processed_dir, get_data_outputs_dir
from ..utils.error_handlers import DataValidationError
from ..seed import get_seed_env_vars

# Set up logging
logger = logging.getLogger(__name__)

# Define elemental property constants (atomic mass, electronegativity, atomic radius, melting point, valence electrons)
# These are standard values for common solder elements (Sn, Ag, Cu, Bi, In, Sb, Zn, Ni, Au, Pd, Pb)
ELEMENTAL_PROPERTIES = {
    'Sn': {'atomic_mass': 118.71, 'electronegativity': 1.96, 'atomic_radius': 140, 'melting_point': 505.08, 'valence_electrons': 4},
    'Ag': {'atomic_mass': 107.87, 'electronegativity': 1.93, 'atomic_radius': 144, 'melting_point': 1234.93, 'valence_electrons': 1},
    'Cu': {'atomic_mass': 63.55, 'electronegativity': 1.90, 'atomic_radius': 128, 'melting_point': 1357.77, 'valence_electrons': 1},
    'Bi': {'atomic_mass': 208.98, 'electronegativity': 2.02, 'atomic_radius': 156, 'melting_point': 544.75, 'valence_electrons': 5},
    'In': {'atomic_mass': 114.82, 'electronegativity': 1.78, 'atomic_radius': 156, 'melting_point': 429.75, 'valence_electrons': 3},
    'Sb': {'atomic_mass': 121.76, 'electronegativity': 2.05, 'atomic_radius': 140, 'melting_point': 903.78, 'valence_electrons': 5},
    'Zn': {'atomic_mass': 65.38, 'electronegativity': 1.65, 'atomic_radius': 134, 'melting_point': 692.68, 'valence_electrons': 2},
    'Ni': {'atomic_mass': 58.69, 'electronegativity': 1.91, 'atomic_radius': 124, 'melting_point': 1728.15, 'valence_electrons': 2},
    'Au': {'atomic_mass': 196.97, 'electronegativity': 2.54, 'atomic_radius': 144, 'melting_point': 1337.33, 'valence_electrons': 1},
    'Pd': {'atomic_mass': 106.42, 'electronegativity': 2.20, 'atomic_radius': 137, 'melting_point': 1828.05, 'valence_electrons': 2},
    'Pb': {'atomic_mass': 207.2, 'electronegativity': 2.33, 'atomic_radius': 175, 'melting_point': 600.61, 'valence_electrons': 4},
    'Ga': {'atomic_mass': 69.72, 'electronegativity': 1.81, 'atomic_radius': 135, 'melting_point': 302.91, 'valence_electrons': 3},
    'Al': {'atomic_mass': 26.98, 'electronegativity': 1.61, 'atomic_radius': 143, 'melting_point': 933.47, 'valence_electrons': 3},
}

class DescriptorEngine:
    """
    Computes compositional descriptors for solder alloys based on elemental properties.
    
    The engine applies CLR transformation to raw composition vectors and then uses
    the resulting CLR coefficients to weight the original raw elemental property tables.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.property_names = ['atomic_mass', 'electronegativity', 'atomic_radius', 'melting_point', 'valence_electrons']
        
    def _validate_elemental_composition(self, composition: Dict[str, float]) -> None:
        """Validate that all elements in composition are known."""
        for element in composition.keys():
            if element not in ELEMENTAL_PROPERTIES:
                raise DataValidationError(f"Unknown element in composition: {element}")
                
    def _get_property_vector(self, property_name: str) -> np.ndarray:
        """Get property values for all elements in the composition as a vector."""
        # We'll compute this dynamically based on the elements present in the composition
        return None  # Will be computed per sample
        
    def compute_descriptors(self, composition: Dict[str, float]) -> Dict[str, float]:
        """
        Compute descriptors for a single solder composition.
        
        Args:
            composition: Dictionary mapping element symbols to their atomic fractions (0-1)
                        
        Returns:
            Dictionary of computed descriptors
        """
        self._validate_elemental_composition(composition)
        
        # Convert composition to numpy array
        elements = list(composition.keys())
        values = np.array([composition[e] for e in elements])
        
        # Apply CLR transformation
        clr_transformer = CLRTransformer()
        clr_coeffs, _ = clr_transformer.transform_composition(values)
        
        # Get property vectors for each element
        property_vectors = {}
        for prop in self.property_names:
            property_vectors[prop] = np.array([ELEMENTAL_PROPERTIES[e][prop] for e in elements])
        
        # Compute weighted mean for each property using CLR coefficients as weights
        descriptors = {}
        
        # Weighted mean atomic mass
        descriptors['weighted_mean_atomic_mass'] = float(np.sum(clr_coeffs * property_vectors['atomic_mass']))
        
        # Weighted mean electronegativity
        descriptors['weighted_mean_electronegativity'] = float(np.sum(clr_coeffs * property_vectors['electronegativity']))
        
        # Weighted mean atomic radius
        descriptors['weighted_mean_atomic_radius'] = float(np.sum(clr_coeffs * property_vectors['atomic_radius']))
        
        # Weighted mean melting point
        descriptors['weighted_mean_melting_point'] = float(np.sum(clr_coeffs * property_vectors['melting_point']))
        
        # Weighted mean valence electron concentration
        descriptors['weighted_mean_valence_electrons'] = float(np.sum(clr_coeffs * property_vectors['valence_electrons']))
        
        # Compute variance for each property using CLR coefficients as weights
        # Variance = sum(w_i * (x_i - mean)^2) where w_i are CLR coefficients
        
        # Electronegativity variance
        mean_en = descriptors['weighted_mean_electronegativity']
        descriptors['electronegativity_variance'] = float(np.sum(clr_coeffs * (property_vectors['electronegativity'] - mean_en)**2))
        
        # Atomic radius variance
        mean_ar = descriptors['weighted_mean_atomic_radius']
        descriptors['atomic_radius_variance'] = float(np.sum(clr_coeffs * (property_vectors['atomic_radius'] - mean_ar)**2))
        
        return descriptors
        
    def compute_descriptors_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute descriptors for a batch of compositions.
        
        Args:
            df: DataFrame with composition columns (element symbols as column names)
                        
        Returns:
            DataFrame with original columns plus computed descriptors
        """
        descriptors_list = []
        
        for idx, row in df.iterrows():
            # Extract composition from row
            composition = {}
            for col in df.columns:
                if col in ELEMENTAL_PROPERTIES:
                    val = row[col]
                    if pd.notna(val) and val > 0:
                        composition[col] = float(val)
            
            if not composition:
                self.logger.warning(f"Row {idx} has no valid composition elements")
                continue
                
            try:
                descriptors = self.compute_descriptors(composition)
                descriptors_list.append(descriptors)
            except Exception as e:
                self.logger.error(f"Error computing descriptors for row {idx}: {str(e)}")
                descriptors_list.append({prop: np.nan for prop in self.property_names + ['electronegativity_variance', 'atomic_radius_variance']})
        
        # Create DataFrame with descriptors
        descriptors_df = pd.DataFrame(descriptors_list)
        
        # Concatenate with original DataFrame
        result_df = pd.concat([df, descriptors_df], axis=1)
        
        return result_df
        
    def save_descriptors(self, df: pd.DataFrame, output_path: Optional[str] = None) -> str:
        """
        Save computed descriptors to a CSV file.
        
        Args:
            df: DataFrame with compositions and computed descriptors
            output_path: Optional path to save the file. If None, uses default path.
                        
        Returns:
            Path to the saved file
        """
        if output_path is None:
            data_outputs_dir = get_data_outputs_dir()
            output_path = os.path.join(data_outputs_dir, 'solder_descriptors.csv')
            
        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        self.logger.info(f"Saved descriptors to {output_path}")
        
        return output_path

def main():
    """Main function to run descriptor computation on the validated dataset."""
    from ..config import get_data_processed_dir
    
    # Initialize logging
    logging.basicConfig(level=logging.INFO)
    
    # Load validated dataset
    data_dir = get_data_processed_dir()
    input_path = os.path.join(data_dir, 'solder_hardness_validated.csv')
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Validated dataset not found at {input_path}")
        
    logger.info(f"Loading validated dataset from {input_path}")
    df = pd.read_csv(input_path)
    
    logger.info(f"Loaded {len(df)} samples")
    
    # Initialize descriptor engine
    engine = DescriptorEngine()
    
    # Compute descriptors
    logger.info("Computing descriptors...")
    df_with_descriptors = engine.compute_descriptors_batch(df)
    
    logger.info(f"Computed descriptors for {len(df_with_descriptors)} samples")
    
    # Save results
    output_path = engine.save_descriptors(df_with_descriptors)
    logger.info(f"Descriptors saved to {output_path}")
    
    # Print summary
    descriptor_cols = [col for col in df_with_descriptors.columns if col not in df.columns]
    logger.info(f"Added descriptor columns: {descriptor_cols}")
    
    return df_with_descriptors

if __name__ == '__main__':
    main()