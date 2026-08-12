from typing import Optional

def assign_chemical_family(element: str) -> str:
    """
    Assigns a chemical family to an element based on its symbol.
    """
    if not element:
        return "Unknown"
    
    element = element.strip()
    
    # Simple mapping for demonstration
    alkali = ['Li', 'Na', 'K', 'Rb', 'Cs', 'Fr']
    alkaline_earth = ['Be', 'Mg', 'Ca', 'Sr', 'Ba', 'Ra']
    transition = ['Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn',
                  'Y', 'Zr', 'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd',
                  'Hf', 'Ta', 'W', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg']
    lanthanide = ['La', 'Ce', 'Pr', 'Nd', 'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy',
                  'Ho', 'Er', 'Tm', 'Yb', 'Lu']
    actinide = ['Ac', 'Th', 'Pa', 'U', 'Np', 'Pu', 'Am', 'Cm', 'Bk', 'Cf',
                'Es', 'Fm', 'Md', 'No', 'Lr']
    halogen = ['F', 'Cl', 'Br', 'I', 'At']
    noble_gas = ['He', 'Ne', 'Ar', 'Kr', 'Xe', 'Rn']
    
    if element in alkali:
        return "Alkali"
    elif element in alkaline_earth:
        return "Alkaline Earth"
    elif element in transition:
        return "Transition"
    elif element in lanthanide:
        return "Lanthanide"
    elif element in actinide:
        return "Actinide"
    elif element in halogen:
        return "Halogen"
    elif element in noble_gas:
        return "Noble Gas"
    elif 'O' in element or element == 'O':
        return "Oxide"
    else:
        return "Other"
