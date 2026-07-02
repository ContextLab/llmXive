"""
Data processing module for HEA yield strength prediction.

This module provides base data schemas and validation logic for the 
high-entropy alloy yield strength prediction pipeline.
"""

import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
import re

# --- Schemas ---

@dataclass
class ElementProperties:
    """Schema for elemental properties used in descriptor calculation."""
    atomic_radius: float  # in pm (picometers)
    electronegativity: float  # Pauling scale
    valence_electrons: float  # average valence electrons per atom
    melting_point: float  # in Kelvin
    
@dataclass
class CompositionRow:
    """Schema for a single HEA composition row with calculated descriptors."""
    composition_id: str
    elements: Dict[str, float]  # element -> atomic fraction
    yield_strength_mpa: float
    delta: float  # atomic size difference
    delta_chi: float  # electronegativity difference
    vec: float  # valence electron concentration
    entropy_mixing: float  # mixing entropy (R units)
    melting_var: float  # melting temperature variance
    phase: str  # 'single', 'multi', or 'unknown'
    temp_celsius: float  # testing temperature
    
@dataclass
class ValidationReport:
    """Schema for validation results."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    count: int = 0
    
# --- Validation Logic ---

def validate_composition_df(df: pd.DataFrame) -> ValidationReport:
    """
    Validate a raw composition DataFrame against expected schema.
    
    Expected columns:
    - 'composition_id': unique identifier (string)
    - 'elements': dict or JSON string of element -> atomic fraction
    - 'yield_strength': numeric (will be normalized later)
    - 'phase': string ('single', 'multi', etc.)
    - 'temp_celsius': numeric (optional, defaults to 25 if missing)
    
    Returns:
        ValidationReport with validation status and any errors/warnings.
    """
    errors = []
    warnings = []
    count = 0
    
    required_cols = ['composition_id', 'elements', 'yield_strength', 'phase']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
        return ValidationReport(is_valid=False, errors=errors, warnings=warnings)
    
    # Validate row by row
    for idx, row in df.iterrows():
        row_errors = []
        
        # Check composition_id
        if not isinstance(row['composition_id'], str) or not row['composition_id'].strip():
            row_errors.append(f"Row {idx}: Invalid or missing composition_id")
        
        # Check elements
        elements = row['elements']
        if isinstance(elements, str):
            try:
                elements = eval(elements)  # Simple parsing; could use json.loads if formatted as JSON
            except Exception:
                row_errors.append(f"Row {idx}: Invalid elements format (must be dict or JSON string)")
                elements = None
        
        if isinstance(elements, dict):
            total_frac = sum(elements.values())
            if abs(total_frac - 1.0) > 0.01:
                row_errors.append(f"Row {idx}: Element fractions sum to {total_frac:.4f}, expected ~1.0")
            
            for elem, frac in elements.items():
                if not isinstance(frac, (int, float)) or frac < 0:
                    row_errors.append(f"Row {idx}: Invalid fraction for {elem}: {frac}")
        else:
            row_errors.append(f"Row {idx}: Elements must be a dictionary")
        
        # Check yield_strength
        if not isinstance(row['yield_strength'], (int, float)) or row['yield_strength'] <= 0:
            row_errors.append(f"Row {idx}: Invalid yield_strength: {row['yield_strength']}")
        
        # Check phase
        if not isinstance(row['phase'], str) or row['phase'].strip() == '':
            row_errors.append(f"Row {idx}: Invalid or missing phase")
        
        # Check temp_celsius (optional)
        if 'temp_celsius' in df.columns:
            if not isinstance(row.get('temp_celsius'), (int, float)):
                warnings.append(f"Row {idx}: Invalid temp_celsius, will default to 25")
        else:
            warnings.append(f"Row {idx}: Missing temp_celsius, will default to 25")
        
        if row_errors:
            errors.extend(row_errors)
        else:
            count += 1
    
    return ValidationReport(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        count=count
    )

def validate_elemental_properties(props: Dict[str, ElementProperties]) -> Tuple[bool, List[str]]:
    """
    Validate a dictionary of elemental properties.
    
    Args:
        props: Dict mapping element symbol (str) to ElementProperties.
        
    Returns:
        Tuple of (is_valid, list of error messages).
    """
    errors = []
    
    if not props:
        errors.append("Elemental properties dictionary is empty")
        return False, errors
    
    for elem, prop in props.items():
        if not isinstance(elem, str) or len(elem) == 0:
            errors.append(f"Invalid element key: {elem}")
            continue
        
        if not isinstance(prop, ElementProperties):
            errors.append(f"Value for {elem} is not ElementProperties instance")
            continue
        
        if prop.atomic_radius <= 0:
            errors.append(f"Element {elem}: atomic_radius must be positive")
        if prop.electronegativity <= 0:
            errors.append(f"Element {elem}: electronegativity must be positive")
        if prop.valence_electrons < 0:
            errors.append(f"Element {elem}: valence_electrons cannot be negative")
        if prop.melting_point <= 0:
            errors.append(f"Element {elem}: melting_point must be positive")
    
    return len(errors) == 0, errors

def validate_composition_row(row: CompositionRow) -> Tuple[bool, List[str]]:
    """
    Validate a single CompositionRow.
    
    Returns:
        Tuple of (is_valid, list of error messages).
    """
    errors = []
    
    if not row.composition_id or not isinstance(row.composition_id, str):
        errors.append("Invalid composition_id")
    
    if not row.elements or not isinstance(row.elements, dict):
        errors.append("Invalid elements dictionary")
    else:
        total = sum(row.elements.values())
        if abs(total - 1.0) > 0.01:
            errors.append(f"Element fractions sum to {total:.4f}, expected ~1.0")
    
    if row.yield_strength_mpa <= 0:
        errors.append("Yield strength must be positive")
    
    if row.phase not in ['single', 'multi', 'unknown']:
        errors.append(f"Invalid phase: {row.phase}")
    
    return len(errors) == 0, errors

# --- Helper Functions ---

def is_single_phase(row: Union[pd.Series, CompositionRow]) -> bool:
    """
    Check if a composition row represents a single-phase alloy.
    
    Args:
        row: Either a pandas Series or a CompositionRow.
        
    Returns:
        True if phase is 'single', False otherwise.
    """
    if isinstance(row, pd.Series):
        return row.get('phase', '').lower() == 'single'
    return row.phase == 'single'

def is_room_temperature(row: Union[pd.Series, CompositionRow], tol: float = 5.0) -> bool:
    """
    Check if a composition was tested at room temperature (20-25°C).
    
    Args:
        row: Either a pandas Series or a CompositionRow.
        tol: Tolerance in degrees Celsius.
        
    Returns:
        True if temperature is within [20-tol, 25+tol], False otherwise.
    """
    temp = None
    if isinstance(row, pd.Series):
        temp = row.get('temp_celsius', 25.0)
    else:
        temp = row.temp_celsius
        
    return 20.0 - tol <= temp <= 25.0 + tol

def has_valid_yield_strength(row: Union[pd.Series, CompositionRow]) -> bool:
    """
    Check if a composition has a valid, positive yield strength value.
    
    Args:
        row: Either a pandas Series or a CompositionRow.
        
    Returns:
        True if yield strength is positive, False otherwise.
    """
    if isinstance(row, pd.Series):
        val = row.get('yield_strength', 0)
    else:
        val = row.yield_strength_mpa
    return val > 0

__all__ = [
    'ElementProperties',
    'CompositionRow',
    'ValidationReport',
    'validate_composition_df',
    'validate_elemental_properties',
    'validate_composition_row',
    'is_single_phase',
    'is_room_temperature',
    'has_valid_yield_strength'
]