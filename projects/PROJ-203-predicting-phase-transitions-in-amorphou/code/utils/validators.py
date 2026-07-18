"""
Data integrity validators for the amorphous solids phase transition pipeline.

Provides checks for:
- NaN/Inf detection in numerical arrays
- Physical bound validation for structural descriptors (RDF, coordination, etc.)
- Composition validity checks
"""

import numpy as np
import pandas as pd
from typing import Union, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ValidationErrorType(Enum):
    """Types of validation errors."""
    NAN_FOUND = "nan_found"
    INF_FOUND = "inf_found"
    OUT_OF_BOUNDS = "out_of_bounds"
    NEGATIVE_VALUE = "negative_value"
    MISSING_COLUMN = "missing_column"
    INVALID_COMPOSITION = "invalid_composition"
    STRUCTURAL_DESCRIPTOR_INVALID = "structural_descriptor_invalid"


@dataclass
class ValidationError:
    """Represents a single validation error."""
    error_type: ValidationErrorType
    field_name: str
    message: str
    value: Optional[Union[float, int, str]] = None
    expected_range: Optional[Tuple[float, float]] = None


@dataclass
class ValidationResult:
    """Result of a validation run."""
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[str]
    stats: Dict[str, int]

    def __bool__(self):
        return self.is_valid


class DescriptorBounds:
    """Physical bounds for common structural descriptors."""
    
    # RDF (Radial Distribution Function) properties
    RDF_PEAK_POSITION_MIN = 0.0  # Angstroms, must be positive
    RDF_PEAK_POSITION_MAX = 20.0  # Angstroms, reasonable upper limit
    RDF_PEAK_WIDTH_MIN = 0.0  # Angstroms, must be positive
    RDF_PEAK_WIDTH_MAX = 5.0  # Angstroms
    
    # Bond angle properties
    BOND_ANGLE_VARIANCE_MIN = 0.0  # degrees^2, must be non-negative
    BOND_ANGLE_VARIANCE_MAX = 360.0  # degrees^2, reasonable upper limit
    
    # Coordination numbers
    COORDINATION_MIN = 0
    COORDINATION_MAX = 16  # Reasonable upper limit for amorphous solids
    
    # Composition fractions
    FRACTION_MIN = 0.0
    FRACTION_MAX = 1.0
    
    # Thermal properties (Kelvin)
    Tg_MIN = 50.0  # K, below this is unlikely for stable glasses
    Tg_MAX = 2000.0  # K, above this is unlikely for typical amorphous solids
    Tx_MIN = 50.0
    Tx_MAX = 2500.0


def validate_nan_inf(
    data: Union[pd.DataFrame, np.ndarray],
    field_name: str = "data"
) -> List[ValidationError]:
    """
    Check for NaN and Inf values in numerical data.
    
    Args:
        data: DataFrame or numpy array to validate
        field_name: Name of the field for error reporting
        
    Returns:
        List of ValidationError objects
    """
    errors = []
    
    if isinstance(data, pd.DataFrame):
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            nan_mask = data[col].isna()
            inf_mask = np.isinf(data[col].astype(float))
            
            if nan_mask.any():
                nan_count = nan_mask.sum()
                errors.append(ValidationError(
                    error_type=ValidationErrorType.NAN_FOUND,
                    field_name=f"{field_name}.{col}",
                    message=f"Found {nan_count} NaN value(s) in column '{col}'",
                    value=float(nan_count)
                ))
            
            if inf_mask.any():
                inf_count = inf_mask.sum()
                errors.append(ValidationError(
                    error_type=ValidationErrorType.INF_FOUND,
                    field_name=f"{field_name}.{col}",
                    message=f"Found {inf_count} Inf value(s) in column '{col}'",
                    value=float(inf_count)
                ))
                
    elif isinstance(data, np.ndarray):
        nan_count = np.sum(np.isnan(data))
        inf_count = np.sum(np.isinf(data))
        
        if nan_count > 0:
            errors.append(ValidationError(
                error_type=ValidationErrorType.NAN_FOUND,
                field_name=field_name,
                message=f"Found {nan_count} NaN value(s) in array",
                value=float(nan_count)
            ))
        
        if inf_count > 0:
            errors.append(ValidationError(
                error_type=ValidationErrorType.INF_FOUND,
                field_name=field_name,
                message=f"Found {inf_count} Inf value(s) in array",
                value=float(inf_count)
            ))
    
    return errors


def validate_physical_bounds(
    df: pd.DataFrame,
    descriptor_map: Optional[Dict[str, Tuple[float, float]]] = None
) -> List[ValidationError]:
    """
    Validate that descriptor values are within physically reasonable bounds.
    
    Args:
        df: DataFrame containing descriptor columns
        descriptor_map: Optional mapping of column names to (min, max) bounds.
                       If None, uses default bounds based on column name patterns.
                       
    Returns:
        List of ValidationError objects
    """
    errors = []
    
    # Define default bounds based on common naming patterns
    default_bounds = {
        'rdf_peak_position': (DescriptorBounds.RDF_PEAK_POSITION_MIN, 
                              DescriptorBounds.RDF_PEAK_POSITION_MAX),
        'rdf_peak_width': (DescriptorBounds.RDF_PEAK_WIDTH_MIN, 
                           DescriptorBounds.RDF_PEAK_WIDTH_MAX),
        'bond_angle_variance': (DescriptorBounds.BOND_ANGLE_VARIANCE_MIN, 
                                DescriptorBounds.BOND_ANGLE_VARIANCE_MAX),
        'coordination_number': (DescriptorBounds.COORDINATION_MIN, 
                                DescriptorBounds.COORDINATION_MAX),
        'coordination': (DescriptorBounds.COORDINATION_MIN, 
                         DescriptorBounds.COORDINATION_MAX),
        'Tg': (DescriptorBounds.Tg_MIN, DescriptorBounds.Tg_MAX),
        'Tx': (DescriptorBounds.Tx_MIN, DescriptorBounds.Tx_MAX),
        'glass_transition_temp': (DescriptorBounds.Tg_MIN, DescriptorBounds.Tg_MAX),
        'crystallization_temp': (DescriptorBounds.Tx_MIN, DescriptorBounds.Tx_MAX),
    }
    
    # Merge with custom bounds if provided
    bounds_map = {**default_bounds, **(descriptor_map or {})}
    
    for col in df.columns:
        if col not in bounds_map:
            continue
        
        min_val, max_val = bounds_map[col]
        col_data = pd.to_numeric(df[col], errors='coerce')
        
        # Check for negative values where only positive are allowed
        if min_val >= 0:
            negative_mask = col_data < 0
            if negative_mask.any():
                neg_count = negative_mask.sum()
                errors.append(ValidationError(
                    error_type=ValidationErrorType.NEGATIVE_VALUE,
                    field_name=col,
                    message=f"Found {neg_count} negative value(s) in '{col}' (min: {min_val})",
                    value=None,
                    expected_range=(min_val, max_val)
                ))
        
        # Check for out-of-bounds values
        out_of_bounds_mask = (col_data < min_val) | (col_data > max_val)
        # Exclude NaN from out-of-bounds check (handled by NaN validator)
        out_of_bounds_mask = out_of_bounds_mask & ~col_data.isna()
        
        if out_of_bounds_mask.any():
            oob_count = out_of_bounds_mask.sum()
            errors.append(ValidationError(
                error_type=ValidationErrorType.OUT_OF_BOUNDS,
                field_name=col,
                message=f"Found {oob_count} value(s) out of bounds [{min_val}, {max_val}] in '{col}'",
                value=None,
                expected_range=(min_val, max_val)
            ))
    
    return errors


def validate_composition(
    df: pd.DataFrame,
    composition_columns: List[str],
    tolerance: float = 1e-6
) -> List[ValidationError]:
    """
    Validate that composition fractions sum to 1.0 (within tolerance).
    
    Args:
        df: DataFrame containing composition columns
        composition_columns: List of column names representing elemental fractions
        tolerance: Maximum allowed deviation from 1.0
        
    Returns:
        List of ValidationError objects
    """
    errors = []
    
    if not composition_columns:
        return errors
    
    missing_cols = [col for col in composition_columns if col not in df.columns]
    if missing_cols:
        errors.append(ValidationError(
            error_type=ValidationErrorType.MISSING_COLUMN,
            field_name="composition",
            message=f"Missing composition columns: {missing_cols}",
            value=None
        ))
        return errors
    
    composition_sum = df[composition_columns].sum(axis=1)
    deviation = (composition_sum - 1.0).abs()
    invalid_mask = deviation > tolerance
    
    if invalid_mask.any():
        invalid_count = invalid_mask.sum()
        max_deviation = deviation[invalid_mask].max()
        errors.append(ValidationError(
            error_type=ValidationErrorType.INVALID_COMPOSITION,
            field_name="composition_sum",
            message=f"Found {invalid_count} composition(s) not summing to 1.0 (max deviation: {max_deviation:.6f})",
            value=float(max_deviation),
            expected_range=(1.0 - tolerance, 1.0 + tolerance)
        ))
    
    # Check for negative fractions
    for col in composition_columns:
        neg_mask = df[col] < 0
        if neg_mask.any():
            neg_count = neg_mask.sum()
            errors.append(ValidationError(
                error_type=ValidationErrorType.NEGATIVE_VALUE,
                field_name=col,
                message=f"Found {neg_count} negative fraction(s) in '{col}'",
                value=None,
                expected_range=(0.0, 1.0)
            ))
    
    # Check for fractions > 1.0
    for col in composition_columns:
        over_mask = df[col] > 1.0
        if over_mask.any():
            over_count = over_mask.sum()
            errors.append(ValidationError(
                error_type=ValidationErrorType.OUT_OF_BOUNDS,
                field_name=col,
                message=f"Found {over_count} fraction(s) > 1.0 in '{col}'",
                value=None,
                expected_range=(0.0, 1.0)
            ))
    
    return errors


def validate_structural_descriptors(
    df: pd.DataFrame,
    required_descriptors: Optional[List[str]] = None
) -> List[ValidationError]:
    """
    Validate structural descriptor columns for required presence and validity.
    
    Args:
        df: DataFrame containing descriptor columns
        required_descriptors: List of required descriptor column names
        
    Returns:
        List of ValidationError objects
    """
    errors = []
    
    if required_descriptors:
        missing = [col for col in required_descriptors if col not in df.columns]
        if missing:
            errors.append(ValidationError(
                error_type=ValidationErrorType.MISSING_COLUMN,
                field_name="descriptors",
                message=f"Missing required structural descriptors: {missing}",
                value=None
            ))
    
    return errors


def validate_dataframe(
    df: pd.DataFrame,
    required_columns: Optional[List[str]] = None,
    check_nan: bool = True,
    check_bounds: bool = True,
    check_composition: bool = False,
    composition_columns: Optional[List[str]] = None,
    descriptor_columns: Optional[List[str]] = None
) -> ValidationResult:
    """
    Comprehensive validation of a DataFrame.
    
    Args:
        df: DataFrame to validate
        required_columns: List of columns that must exist
        check_nan: Whether to check for NaN/Inf values
        check_bounds: Whether to check physical bounds
        check_composition: Whether to check composition sums
        composition_columns: Columns to check for composition validity
        descriptor_columns: Columns treated as structural descriptors
        
    Returns:
        ValidationResult with errors, warnings, and statistics
    """
    errors = []
    warnings = []
    stats = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "nan_count": 0,
        "inf_count": 0,
        "out_of_bounds_count": 0
    }
    
    # Check required columns
    if required_columns:
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            errors.append(ValidationError(
                error_type=ValidationErrorType.MISSING_COLUMN,
                field_name="schema",
                message=f"Missing required columns: {missing}",
                value=None
            ))
    
    # Check for NaN/Inf
    if check_nan and not df.empty:
        nan_errors = validate_nan_inf(df, "dataframe")
        errors.extend(nan_errors)
        for err in nan_errors:
            if err.error_type == ValidationErrorType.NAN_FOUND:
                stats["nan_count"] += int(err.value or 0)
            elif err.error_type == ValidationErrorType.INF_FOUND:
                stats["inf_count"] += int(err.value or 0)
    
    # Check physical bounds
    if check_bounds and not df.empty:
        bound_errors = validate_physical_bounds(df)
        errors.extend(bound_errors)
        oob_count = sum(1 for e in bound_errors if e.error_type == ValidationErrorType.OUT_OF_BOUNDS)
        stats["out_of_bounds_count"] += oob_count
    
    # Check composition
    if check_composition and composition_columns:
        comp_errors = validate_composition(df, composition_columns)
        errors.extend(comp_errors)
    
    # Check structural descriptors
    if descriptor_columns:
        desc_errors = validate_structural_descriptors(df, descriptor_columns)
        errors.extend(desc_errors)
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        stats=stats
    )


def raise_if_invalid(result: ValidationResult, error_prefix: str = "Validation failed") -> None:
    """
    Raise an exception if validation result is invalid.
    
    Args:
        result: ValidationResult from validate_dataframe
        error_prefix: Prefix for the error message
        
    Raises:
        ValueError: If validation failed
    """
    if not result.is_valid:
        error_messages = [f"{error_prefix}:"]
        for err in result.errors:
            error_messages.append(f"  - [{err.error_type.value}] {err.message}")
        raise ValueError("\n".join(error_messages))