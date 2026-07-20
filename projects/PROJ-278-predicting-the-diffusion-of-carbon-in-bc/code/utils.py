from pymatgen.core import Element
from typing import Optional, Dict, List, Any
import logging

def get_atomic_radius(element_symbol: str) -> Optional[float]:
    try:
        el = Element(element_symbol)
        return el.atomic_radius
    except Exception as e:
        logging.warning(f"Could not get atomic radius for {element_symbol}: {e}")
        return None

def get_vec(element_symbol: str) -> Optional[int]:
    try:
        el = Element(element_symbol)
        return el.oxi_state_guesses(max_oxi_states=1)[0] if el.oxi_state_guesses() else 0
    except Exception as e:
        logging.warning(f"Could not get VEC for {element_symbol}: {e}")
        return 0

def get_electronegativity(element_symbol: str) -> Optional[float]:
    try:
        el = Element(element_symbol)
        return el.X
    except Exception as e:
        logging.warning(f"Could not get electronegativity for {element_symbol}: {e}")
        return None

def get_properties(element_symbol: str) -> Dict[str, Any]:
    return {
        "atomic_radius": get_atomic_radius(element_symbol),
        "VEC": get_vec(element_symbol),
        "electronegativity": get_electronegativity(element_symbol)
    }

def get_properties_batch(elements: List[str]) -> List[Dict[str, Any]]:
    return [get_properties(el) for el in elements]
