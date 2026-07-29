"""
Descriptor Engine for Solder Alloys.

Computes weighted mean atomic mass, electronegativity variance, atomic radius variance,
weighted average melting point, and valence electron concentration.

Workflow:
1. Apply CLR to raw composition vector to get coefficients.
2. Use CLR coefficients to weight original raw elemental property tables.
"""
import numpy as np
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from features.transformer import CLRTransformer
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Standard elemental properties (approximate values for common solder elements)
# In a real pipeline, this might be loaded from a CSV or database
ELEMENT_PROPERTIES = {
    "Sn": {"atomic_mass": 118.71, "electronegativity": 1.96, "atomic_radius": 140, "melting_point": 231.93, "valence_electrons": 4},
    "Pb": {"atomic_mass": 207.2, "electronegativity": 2.33, "atomic_radius": 175, "melting_point": 327.46, "valence_electrons": 4},
    "Ag": {"atomic_mass": 107.87, "electronegativity": 1.93, "atomic_radius": 144, "melting_point": 961.78, "valence_electrons": 1},
    "Cu": {"atomic_mass": 63.55, "electronegativity": 1.90, "atomic_radius": 128, "melting_point": 1084.62, "valence_electrons": 1},
    "Bi": {"atomic_mass": 208.98, "electronegativity": 2.02, "atomic_radius": 156, "melting_point": 271.36, "valence_electrons": 5},
    "In": {"atomic_mass": 114.82, "electronegativity": 1.78, "atomic_radius": 166, "melting_point": 156.60, "valence_electrons": 3},
    "Zn": {"atomic_mass": 65.38, "electronegativity": 1.65, "atomic_radius": 134, "melting_point": 419.53, "valence_electrons": 2},
    "Sb": {"atomic_mass": 121.76, "electronegativity": 2.05, "atomic_radius": 140, "melting_point": 630.63, "valence_electrons": 5},
    "Au": {"atomic_mass": 196.97, "electronegativity": 2.54, "atomic_radius": 144, "melting_point": 1064.18, "valence_electrons": 1},
    "Ni": {"atomic_mass": 58.69, "electronegativity": 1.91, "atomic_radius": 124, "melting_point": 1455.00, "valence_electrons": 2},
    "Fe": {"atomic_mass": 55.85, "electronegativity": 1.83, "atomic_radius": 126, "melting_point": 1538.00, "valence_electrons": 2},
    "Co": {"atomic_mass": 58.93, "electronegativity": 1.88, "atomic_radius": 125, "melting_point": 1495.00, "valence_electrons": 2},
    "Mn": {"atomic_mass": 54.94, "electronegativity": 1.55, "atomic_radius": 127, "melting_point": 1246.00, "valence_electrons": 2},
    "Al": {"atomic_mass": 26.98, "electronegativity": 1.61, "atomic_radius": 143, "melting_point": 660.32, "valence_electrons": 3},
    "Mg": {"atomic_mass": 24.31, "electronegativity": 1.31, "atomic_radius": 160, "melting_point": 650.00, "valence_electrons": 2},
    "Ca": {"atomic_mass": 40.08, "electronegativity": 1.00, "atomic_radius": 197, "melting_point": 842.00, "valence_electrons": 2},
}


class DescriptorEngine:
    """
    Computes physical property descriptors from solder compositions.
    """

    def __init__(self):
        self.element_properties = pd.DataFrame(ELEMENT_PROPERTIES).T

    def compute_descriptors(self, df: pd.DataFrame, composition_cols: List[str]) -> pd.DataFrame:
        """
        Compute descriptors for a dataframe of solder compositions.

        Args:
            df: DataFrame containing composition data (weight fractions).
            composition_cols: List of column names representing elements.

        Returns:
            DataFrame with original columns plus new descriptor columns.
        """
        logger.info(f"Computing descriptors for {len(df)} samples using elements: {composition_cols}")

        # Filter to only elements we have properties for
        valid_elements = [e for e in composition_cols if e in self.element_properties.index]
        if len(valid_elements) != len(composition_cols):
            missing = set(composition_cols) - set(valid_elements)
            logger.warning(f"Missing property data for elements: {missing}. Skipping these in descriptor calculation.")

        if len(valid_elements) == 0:
            raise ValueError("No valid elements found for descriptor calculation.")

        # 1. Apply CLR transform to get coefficients
        # The CLR transformer expects a matrix of compositions
        comp_matrix = df[valid_elements].values

        # Handle potential zeros (add small epsilon if necessary, though cleaner should handle this)
        # For robustness, we'll add a tiny value if any are exactly zero to avoid log(0)
        epsilon = 1e-10
        comp_matrix = np.where(comp_matrix == 0, epsilon, comp_matrix)

        clr_transformer = CLRTransformer()
        clr_matrix, _ = clr_transformer.fit_transform(comp_matrix)

        # 2. Compute descriptors using CLR coefficients as weights
        # Note: The spec says "Using the resulting CLR coefficients to weight the original raw elemental property tables"
        # This implies: Descriptors = sum(CLR_coeff * Property_Value) for each element

        descriptors = {}

        # Weighted Mean Atomic Mass
        mass_weights = clr_matrix[:, [valid_elements.index(e) for e in valid_elements]]
        mass_values = np.array([self.element_properties.loc[e, "atomic_mass"] for e in valid_elements])
        descriptors["weighted_mean_atomic_mass"] = np.sum(mass_weights * mass_values, axis=1)

        # Weighted Mean Electronegativity
        en_weights = clr_matrix[:, [valid_elements.index(e) for e in valid_elements]]
        en_values = np.array([self.element_properties.loc[e, "electronegativity"] for e in valid_elements])
        descriptors["weighted_mean_electronegativity"] = np.sum(en_weights * en_values, axis=1)

        # Electronegativity Variance (weighted by CLR coefficients squared? or just variance of weighted values?)
        # Standard approach in materials informatics: Variance of properties weighted by atomic fraction or CLR weight.
        # We'll compute the weighted variance of electronegativity.
        # Var = sum(w * (x - mean)^2)
        # However, since we are using CLR weights which sum to 0, we might interpret this as a moment.
        # Let's stick to the prompt's likely intent: variance of the property values weighted by the composition magnitude.
        # Alternative interpretation: Variance of the property distribution in the alloy.
        # Let's use: sum( (clr_coef * property)^2 ) as a proxy for variance contribution, or standard weighted variance.
        # Given the prompt says "electronegativity variance", let's calculate the variance of the property values
        # weighted by the absolute CLR weights or just the raw composition if we were using raw.
        # But the prompt specifically says "Using the resulting CLR coefficients to weight...".
        # Let's calculate the variance of the property values, weighted by the CLR coefficients.
        # Since CLR coefficients can be negative, variance is usually calculated on the raw composition or using a different weighting.
        # Let's assume the prompt implies: Variance = sum( (w_i * x_i)^2 ) - (sum(w_i * x_i))^2? No.
        # Let's use the standard weighted variance formula where weights are the absolute values of CLR coefficients or the raw composition.
        # However, to strictly follow "weighting with CLR coefficients", we will compute the second moment.
        # Let's try: Variance = sum( (CLR_i * Property_i)^2 ) - (sum(CLR_i * Property_i))^2
        # This is the variance of the property distribution where the "probability" is defined by CLR weights.
        # Note: CLR weights sum to 0, so the mean is 0. Thus Variance = sum( (CLR_i * x_i)^2 ).
        descriptors["electronegativity_variance"] = np.sum((en_weights * en_values) ** 2, axis=1)

        # Atomic Radius Variance (similar logic)
        radius_weights = clr_matrix[:, [valid_elements.index(e) for e in valid_elements]]
        radius_values = np.array([self.element_properties.loc[e, "atomic_radius"] for e in valid_elements])
        descriptors["atomic_radius_variance"] = np.sum((radius_weights * radius_values) ** 2, axis=1)

        # Weighted Average Melting Point
        mp_weights = clr_matrix[:, [valid_elements.index(e) for e in valid_elements]]
        mp_values = np.array([self.element_properties.loc[e, "melting_point"] for e in valid_elements])
        descriptors["weighted_avg_melting_point"] = np.sum(mp_weights * mp_values, axis=1)

        # Valence Electron Concentration (VEC)
        # VEC is typically sum(atomic_fraction * valence_electrons)
        # We will use CLR weights here as per the "weighting" instruction, though physically VEC is usually based on atomic fraction.
        # If the prompt strictly demands CLR weighting, we do so.
        vec_weights = clr_matrix[:, [valid_elements.index(e) for e in valid_elements]]
        vec_values = np.array([self.element_properties.loc[e, "valence_electrons"] for e in valid_elements])
        descriptors["weighted_valence_electron_concentration"] = np.sum(VEC_weights * vec_values, axis=1)

        # Create new dataframe with descriptors
        desc_df = pd.DataFrame(descriptors)
        desc_df.index = df.index

        # Merge back to original dataframe
        result = pd.concat([df, desc_df], axis=1)

        logger.info(f"Computed {len(descriptors)} descriptors.")
        return result

    def get_element_properties_df(self) -> pd.DataFrame:
        """Returns the internal elemental properties dataframe."""
        return self.element_properties


def main():
    """
    Main entry point for standalone execution of descriptor engineering.
    Loads validated data, computes descriptors, and saves the result.
    """
    from seed import init_reproducibility
    from config import get_data_processed_dir, get_data_outputs_dir
    import json

    init_reproducibility()

    processed_dir = get_data_processed_dir()
    output_dir = get_data_outputs_dir()

    input_file = processed_dir / "solder_hardness_validated.csv"
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}. Run ingestion pipeline first.")
        return

    logger.info(f"Loading data from {input_file}")
    df = pd.read_csv(input_file)

    # Identify composition columns (usually all columns except 'hardness', 'alloy_id', etc.)
    # We'll assume columns with element symbols in them
    possible_elements = list(ELEMENT_PROPERTIES.keys())
    composition_cols = [c for c in df.columns if c in possible_elements]

    if not composition_cols:
        logger.error("No composition columns found in the dataset.")
        return

    logger.info(f"Detected composition columns: {composition_cols}")

    engine = DescriptorEngine()
    result_df = engine.compute_descriptors(df, composition_cols)

    output_file = output_dir / "solder_hardness_with_descriptors.csv"
    result_df.to_csv(output_file, index=False)
    logger.info(f"Saved descriptors to {output_file}")

    # Save metadata
    metadata = {
        "input_file": str(input_file),
        "output_file": str(output_file),
        "elements_used": composition_cols,
        "descriptors_computed": list(engine.compute_descriptors(df.head(1), composition_cols).columns[len(df.columns):])
    }
    with open(output_dir / "descriptor_engine_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

if __name__ == "__main__":
    main()
