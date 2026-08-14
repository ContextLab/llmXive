from typing import Optional


def assign_chemical_family(element: str) -> str:
    """
    Assign a chemical family to an element.

    Args:
        element: Element symbol (e.g., 'Na', 'Fe', 'O')

    Returns:
        Chemical family string (e.g., 'Alkali', 'Transition', 'Oxide')
    """
    element = element.strip().capitalize()

    # Alkali metals
    if element in ["Li", "Na", "K", "Rb", "Cs", "Fr"]:
        return "Alkali"

    # Alkaline earth
    if element in ["Be", "Mg", "Ca", "Sr", "Ba", "Ra"]:
        return "Alkaline_Earth"

    # Transition metals
    transition = [
        "Sc",
        "Ti",
        "V",
        "Cr",
        "Mn",
        "Fe",
        "Co",
        "Ni",
        "Cu",
        "Zn",
        "Y",
        "Zr",
        "Nb",
        "Mo",
        "Tc",
        "Ru",
        "Rh",
        "Pd",
        "Ag",
        "Cd",
        "Hf",
        "Ta",
        "W",
        "Re",
        "Os",
        "Ir",
        "Pt",
        "Au",
        "Hg",
    ]
    if element in transition:
        return "Transition"

    # Lanthanides/Actinides
    if element in [
        "La",
        "Ce",
        "Pr",
        "Nd",
        "Pm",
        "Sm",
        "Eu",
        "Gd",
        "Tb",
        "Dy",
        "Ho",
        "Er",
        "Tm",
        "Yb",
        "Lu",
    ]:
        return "Lanthanide"

    if element in [
        "Ac",
        "Th",
        "Pa",
        "U",
        "Np",
        "Pu",
        "Am",
        "Cm",
        "Bk",
        "Cf",
        "Es",
        "Fm",
        "Md",
        "No",
        "Lr",
    ]:
        return "Actinide"

    # Non-metals and metalloids
    if element in ["H", "He", "C", "N", "O", "F", "Ne", "P", "S", "Cl", "Ar"]:
        return "Non_Metal"

    if element in ["B", "Si", "Ge", "As", "Se", "Br", "Kr", "Sb", "Te", "I", "Xe"]:
        return "Metalloid"

    # Post-transition
    if element in [
        "Al",
        "Ga",
        "In",
        "Sn",
        "Tl",
        "Pb",
        "Bi",
        "Po",
        "At",
        "Rn",
    ]:
        return "Post_Transition"

    return "Unknown"
