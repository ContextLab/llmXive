import numpy as np
from pymatgen.core.structure import Structure
from pymatgen.core.sites import Site
from typing import List

def generate_symmetric_tilt_grain_boundary_supercell(seed_structure: Structure, misorientation_angle_degrees: float = 7.24) -> Structure:
    """
    Generates a symmetric tilt grain boundary supercell from a seed structure.

    Args:
        seed_structure (Structure): The seed BCC structure to create the GB from (e.g., MP-13).
        misorientation_angle_degrees (float): Misorientation angle in degrees for the tilt boundary.

    Returns:
        Structure: A Structure object representing the symmetric tilt grain boundary supercell.
    """

    # Convert misorientation angle to radians
    misorientation_angle_radians = np.deg2rad(misorientation_angle_degrees)

    # Define the shear vector (in fractional coordinates).  This is a simple example for a [100] tilt axis
    shear_vector = np.array([0, 0, np.tan(misorientation_angle_radians)])

    # Create supercell matrix
    supercell_matrix = np.eye(3)
    supercell_matrix[2, 2] = 1 + shear_vector[2] # Apply shear along z axis for the tilt boundary

    # Create the supercell structure
    gb_structure = seed_structure.copy()
    gb_structure.make_supercell(supercell_matrix)


    return gb_structure