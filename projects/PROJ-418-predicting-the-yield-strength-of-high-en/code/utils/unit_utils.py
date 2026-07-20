from typing import Union
import numpy as np

def convert_yield_strength(value: Union[float, int], from_unit: str, to_unit: str = "MPa") -> float:
    """
    Converts yield strength values between units.
    Supported: MPa, GPa, psi, ksi
    """
    value = float(value)
    from_unit = from_unit.lower()
    to_unit = to_unit.lower()
    
    if from_unit == to_unit:
        return value
    
    # Convert to MPa first
    if from_unit == 'mpa':
        mpa_val = value
    elif from_unit == 'gpa':
        mpa_val = value * 1000
    elif from_unit == 'psi':
        mpa_val = value * 0.00689476
    elif from_unit == 'ksi':
        mpa_val = value * 6.89476
    else:
        raise ValueError(f"Unsupported source unit: {from_unit}")
    
    # Convert from MPa to target
    if to_unit == 'mpa':
        return mpa_val
    elif to_unit == 'gpa':
        return mpa_val / 1000
    elif to_unit == 'psi':
        return mpa_val / 0.00689476
    elif to_unit == 'ksi':
        return mpa_val / 6.89476
    else:
        raise ValueError(f"Unsupported target unit: {to_unit}")

def normalize_to_mpa(value: Union[float, int], unit: str) -> float:
    """
    Convenience wrapper to convert any unit to MPa.
    """
    return convert_yield_strength(value, unit, "MPa")

def main():
    print("Unit utils loaded.")

if __name__ == "__main__":
    main()
