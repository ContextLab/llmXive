"""
Utilities for assigning chemical families to elements.
"""
from typing import Optional


def assign_chemical_family(element: str) -> str:
    """
    Assign a chemical family to an element based on its symbol.

    Args:
        element: The element symbol (e.g., 'Fe', 'O').

    Returns:
        The chemical family string (e.g., 'Alkali', 'Transition', 'Oxide').
    """
    element = element.strip()
    if not element:
        return "Unknown"

    # Define element families
    alkali_metals = {"Li", "Na", "K", "Rb", "Cs", "Fr"}
    alkaline_earth_metals = {"Be", "Mg", "Ca", "Sr", "Ba", "Ra"}
    transition_metals = {
        "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn",
        "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd",
        "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg"
    }
    post_transition_metals = {
        "Al", "Ga", "In", "Tl", "Sn", "Pb", "Bi", "Po"
    }
    metalloids = {"B", "Si", "Ge", "As", "Sb", "Te", "Po"}
    non_metals = {"H", "C", "N", "O", "F", "P", "S", "Se", "Cl", "Br", "I"}
    halogens = {"F", "Cl", "Br", "I", "At"}
    noble_gases = {"He", "Ne", "Ar", "Kr", "Xe", "Rn"}
    lanthanides = {"La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu"}
    actinides = {"Ac", "Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr"}

    if element in alkali_metals:
        return "Alkali"
    elif element in alkaline_earth_metals:
        return "Alkaline Earth"
    elif element in transition_metals:
        return "Transition"
    elif element in post_transition_metals:
        return "Post-Transition"
    elif element in metalloids:
        return "Metalloid"
    elif element in halogens:
        return "Halogen"
    elif element in noble_gases:
        return "Noble Gas"
    elif element in lanthanides:
        return "Lanthanide"
    elif element in actinides:
        return "Actinide"
    elif element in non_metals:
        return "Non-Metal"
    else:
        return "Unknown"
